# atd-knack-services

ATD Knack Services is a set of pyhton modules which automate the flow of data from ATD's Knack applications to downstream systems.

These utilities are designed to:

- incrementally offload Knack application records and metadata as a JSON documents in a PostgreSQL data store
- incrementally fetch records and publish them to external systems such as Socrata and ArcGIS Online
- lay the groundwork for further integration with a data lake and/or a data warehouse
- be deployed in Airflow or similar task management frameworks

![basic data flow](docs/basic_flow.jpg)

## TODO

- document docker CI
- warning: if you copy an app, the record IDs will change. do a replace!
- disable legacy publisher for those that have been migrated
- document field matching. think about field mapping...

## Core concepts

- Incremental loading and Knack filter limitations
- Truncating/replacing

## Configuration

### Postgres data store

A PostgreSQL database serves as staging area for Knack records to be published to downstream systems. Knack data lives in two tables within the `api` schema.

#### `knack`

This is the primary table which holds all knack records. Records are uniquely identified by the Knack application ID (`app_id`), the container ID (`container_id`) of the source Knack object or view, and the Knack record ID of the record.

Note that although Knack record IDs are globally unique, this table may hold multiple copies of the same record, but with a different field set, because the same record may be sourced from different views. **You should always reference all primary key columns when reading from or writing data to this table.**

| **Column name** | **Data type**              | **Constraint** | **Note**                      |
| --------------- | -------------------------- | -------------- | ----------------------------- |
| `app_id`        | `text`                     | `primary key`  |                               |
| `container_id`  | `text`                     | `primary key`  |                               |
| `record_id`     | `text`                     | `primary key`  |                               |
| `record`        | `json`                     | `not null`     |                               |
| `updated_at`    | `timestamp with time zone` | `not null`     | _set via trigger `on update`_ |

#### `knack_metadata`

This table holds Knack application metadata, which is kept in sync and relied upon by the scripts in this repo. We store app metadata in the database as means to reduce API load on the Knack application itself.

| **Column name** | **Data type** | **Constraint** |
| --------------- | ------------- | -------------- |
| `app_id`        | `text`        | `primary key`  |
| `metadata`      | `json`        | `not null`     |

### PostgREST API

The Postgres data store is fronted by a [Postgrest](http://postgrest.com/) API which is used for all reading and writing to the database.

All operations within the `api` schema that is exposed via PostgREST must be authenticated with a valid JWT for the dedicated Postgres user. The JWT secret and API user name are stored in the DTS password manager.

### App names

Throughout these modules we use predefined names to refer to Knack applications. We pull these names out of thin air, but they must be used conistently, because they are used to identify the correct Knack auth tokens and ETL configuration parameters in `services/config/knack.py`. Whenever you see a variable or CLI argument named `app_name`, we're referring to these pre-defined app names.

### Auth & environmental variables

The required environmental variables for using these scripts are:

- `AGOL_USERNAME`: An ArcGIS Online user name that has access to the destination AGOL service
- `AGOL_PASSWORD`: The ArcGIS Online account password
- `APP_ID`: The Knack App ID of the application you need to access
- `API_KEY`: The Knack API key of the application you need to access
- `AWS_ACCESS_KEY_ID`: An AWS access key with read/write permissions on the S3 bucket
- `AWS_SECRET_ACCESS_KEY`: The AWS access key toke
- `PGREST_JWT`: A JSON web token used to authenticate PostgREST requests
- `PGREST_ENDPOINT`: The URL of the PostgREST server. Currently available at `https://atd-knack-services.austinmobility.io`

If you'd like to run locally in Docker, create an [environment file](https://docs.docker.com/compose/env-file/) and pass it to `docker run`. For development purpsoses, this command also overwrites the contents of the container's `/app` directory with your local copy of the repo:

```
$ docker run -it --rm --env-file env_file -v <absolute-path-to-this-repo>:/app atddocker/atd-knack-services:production services/records_to_socrata.py -a data-tracker -c object_11 -e prod
```

### Knack (`services/config/knack.py`)

Each Knack container which will be processed must have configuration parameters defined in `services/config/knack.py`, as follows:

```python
CONFIG = {
    <str: app_name>: {
        <str: continer_id>: <dict: container kwargs>
        },
    },
}
```

- `app_name` (`str`): The Knack application name. See note about application names, above.
- `container_id` (`str`): a Knack object or view key (e.g., `object_11`) which holds the records to be processed.

#### Container properties

- `scene_id` (`str`): If the container is a Knack view, this is required, and refers to the Knack scene ID which contains the view.
- `modified_date_field_id` (`str`, required): A knack field ID (e.g., `field_123`) which defines when each record was last modified. This field will be used to filter records for each ETL run.
- `description` (`str`, optional): a description of what kind of record this container holds.
- `socrata_resource_id` (`str`, optional): The Socrata resource ID of the destination dataset. This is required if publshing to Socrata.
- `location_fields` (`list`, optional): A list of knack field keys which will be translated to Socrata "location" field types or an ArcGIS Online point geometry.
- `service_id` (`str`, optional): The ArcGIS Online feature service identifier. Required to publish to ArcGIS Online.
- `layer_id` (`int`, optional): The ArcGIS Online layer ID of the the destination layer in the feature service.
- `upsert_matching_field` (`str`, optional): Required for publishing to arcgis online. The field name to be used to match records when upserting to ArcGIS Online. The field must be configured with a `unique` constraint on the layer.

## Services (`/services`)

### Load app metadata to Postgres

Use `metadata_to_postgrest.py` to load an application's metadata to Postgres.

```shell
$ python metadata_to_postgrest.py \
    --app-name data-tracker \
    --env prod \
```

#### CLI arguments

- `--app-name, -a` (`str`, required): the name of the source Knack application
- `--env, -e` (`str`, required): The application environment. Must be `prod` or `dev`.

### Load knack records to Postgres

Use `records_to_postgrest.py` to incrementally load data from a Knack container (an object or view) to the `knack` table in Postgres.

```shell
$ python records_to_postgrest.py \
    -a data-tracker \
    -c view_1 \
    -e prod \
    -d "2020-09-08T09:21:08-05:00"
```

#### CLI arguments

- `--app-name, -a` (`str`, required): the name of the source Knack application
- `--env, -e` (`str`, required): The application environment. Must be `prod` or `dev`.
- `--container, -c` (`str`, required): the name of the object or view key of the source container
- `--date, -d` (`str`, optional): an ISO-8601-compliant date string. If no timezone is provided, GMT is assumed. Only records which were modified at or after this date will be processed. If excluded, all records will be processed.

### Publish records to the open data portal

Use `records_to_socrata.py` to publish a Knack container to the Open Data Portal (aka, Socrata).

```shell
$ python records_to_socrata.py \
    -a data-tracker \
    -c view_1 \
    -e prod \
    -d "2020-09-08T09:21:08-05:00"
```

#### CLI arguments

- `--app-name, -a` (`str`, required): the name of the source Knack application
- `--container, -c` (`str`, required): the name of the object or view key of the source container
- `--env, -e` (`str`, required): The application environment. Must be `prod` or `dev`.
- `--date, -d` (`str`, optional): an ISO-8601-compliant date string. If no timezone is provided, GMT is assumed. Only records which were modified at or after this date will be processed. If excluded, all records will be processed.

### Publish records to ArcGIS Online

Use `records_to_agol.py` to publish a Knack container to an ArcGIS Online layer. Note that publishing to AGOL always inolves a complete truncate and replacee. Date filtering is not supported.

```shell
$ python records_to_agol.py \
    -a data-tracker \
    -c view_1 \
    -e prod \
```

#### CLI arguments

- `--app-name, -a` (`str`, required): the name of the source Knack application
- `--container, -c` (`str`, required): the name of the object or view key of the source container
- `--env, -e` (`str`, required): The application environment. Must be `prod` or `dev`.

## Utils (`/services/utils`)

The package contains utilities for fetching and pushing data between Knack applications and AWS S3.

TODO

## Deployment

An end-to-end ETL process will involve creating at least three Airflow tasks:

- Load app metadata to Postgres
- Load Knack records to Postgres
- Publish Knack records to destination system
