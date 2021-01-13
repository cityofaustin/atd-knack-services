from copy import deepcopy
import json
import math

import requests


def get_metadata(client, app_id):
    """A helper func which fetches an app's metadata based on the provided app_id str"""
    results = client.select(
        "knack_metadata",
        params={"app_id": f"eq.{app_id}", "limit": 1},
        pagination=False,
    )
    if results:
        return results[0]["metadata"]
    return None


class Postgrest(object):
    """Class to interact with PostgREST"""

    def __init__(self, url, token=None):
        self.token = token
        self.url = url
        self.default_headers = {"Content-Type": "application/json"}
        if self.token:
            self.default_headers["Authorization"] = f"Bearer {self.token}"

    def _make_request(self, *, resource, method, headers, params=None, data=None):
        url = f"{self.url}/{resource}"
        req = requests.Request(method, url, headers=headers, params=params, json=data,)
        prepped = req.prepare()
        session = requests.Session()
        res = session.send(prepped)
        res.raise_for_status()
        try:
            return res.json()
        except json.JSONDecodeError:
            return res.text

    def _get_request_headers(self, headers):
        """Update the instance's default request headers with any provided by the user
        when making a request"""
        request_headers = deepcopy(self.default_headers)
        if headers:
            request_headers.update(headers)
        return request_headers

    def insert(self, resource, data=None, headers=None):
        headers = self._get_request_headers(headers)
        return self._make_request(
            resource=resource, method="post", headers=headers, data=data
        )

    def update(self, resource, params=None, data=None, headers=None):
        """ This method is dangerous! It is possible to delete and modify records
        en masse. Read the PostgREST docs."""
        headers = self._get_request_headers(headers)
        return self._make_request(
            resource=resource, method="patch", headers=headers, params=params, data=data
        )

    def upsert(self, resource, data=None, headers=None):
        """ This method is dangerous! It is possible to delete and modify records
        en masse. Read the PostgREST docs."""
        headers = self._get_request_headers(headers)
        if headers.get("Prefer"):
            headers["Prefer"] += ", resolution=merge-duplicates"
        else:
            headers["Prefer"] = "resolution=merge-duplicates"
        return self._make_request(
            resource=resource, method="post", headers=headers, data=data
        )

    def delete(self, resource, params=None, headers=None):
        """This method is dangerous! It is possible to delete and modify records
        en masse. Read the PostgREST docs."""
        if not params:
            raise Exception(
                "You must supply parameters with delete requests. This is for your own protection."  # noqa E501
            )
        headers = self._get_request_headers(headers)
        return self._make_request(
            resource=resource, method="delete", headers=headers, params=params
        )

    def select(
        self, resource, params=None, pagination=True, headers=None, order_by=None
    ):
        """Fetch selected records from PostgREST. See documentation for horizontal
        and vertical filtering at http://postgrest.org/.

        Args:
            resource (str): Required. The postgrest's endpoint's table or view name to
                query.
            headers (dict): Custom PostgREST headers which will be passed to the
                request. Defaults to None.
            order_by (str): Field name to use a sort field when querying records. This
                must be provided when pagniation=True to ensure that the DB returns
                consistent results across all pages/offsets.
            pagination (bool): If the client should make repeated requests until etiher:
                -  the limit param (if present) is met
                -  if no limit param is included, until no more records are returned from
                    the API.
                Defaults to True.
            params (dict): PostgREST-compliant request parameters. Defaults to None.

        Returns:
            List: A list of dicts of data returned from the host
        """
        params = {} if not params else params
        limit = params.get("limit", math.inf)
        params.setdefault("offset", 0)
        params["order"] = order_by

        if pagination and not order_by:
            raise ValueError(
                "It's not reliable to paginate requests without specifying an 'order_by' field"
            )

        records = []
        headers = self._get_request_headers(headers)

        while True:
            data = self._make_request(
                resource=resource, method="get", headers=headers, params=params
            )
            records += data

            if not data or len(records) >= limit or not pagination:
                # Postgrest has a max-rows configuration setting which limits the total
                # number of rows that can be returned from a request. when the the
                # client specifies a limit higher than max-rows, the the max-rows # of
                # rows are returned
                return records
            else:
                params["offset"] += len(data)
