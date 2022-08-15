# atd-knack-services

ATD Knack Services is a set of python modules which automate the flow of data from ATD's Knack applications to downstream systems.

![basic data flow](docs/basic_flow.jpg)

## Contents

- [Core Concepts](#core-concepts)
- [System Architecture](#system-architecture)
- [Configuration](#configuration)
- [Services](<#services-(`/services`)>)
  - [Publish to Open Data Portal](#publish-records-to-the-open-data-portal)
  - [Publish to ArcGIS Online](#publish-records-to-arcgis-online)
  - [Publish to another Knack app](#publish-records-to-another-knack-app)
- [Utils](<#utils-(`/services/utils`)>)
- [Common Tasks](#common-tasks)
  - [Configure a Knack container](#configuring-a-knack-container)
  - [Dealing with Schema Changes](#dealing-with-schema-changes)
  - [Automate w/ Airflow and Docker](#automate-tasks-with-airflow-and-docker)
- [Troubleshooting](#troubleshooting)

## Core concepts

These utilities are designed to:

- Incrementally offload Knack application records and metadata as a JSON documents in a PostgreSQL data store
- Incrementally fetch records and publish them to external systems such as Socrata and ArcGIS Online
- Lay the groundwork for further integration with a data lake and/or a data warehouse
- Be deployed in Airflow or similar task management frameworks

### Knack containers

A "container" is a generic term to identify the source for a set of Knack application records. In Knack parlance, a container can refer to either a "view" (a UI component which exposes records in the application) or an "object" (the equivalent to a database table).

"Container" is not a Knack term; it is endemic to our team and carried forth from [Knackpy](https://github.com/cityofaustin/knackpy), and it is universally meant to refer to either a view or object key which uniquely identifies the resource in a given application.

### Incremental loading

These services are designed to keep Knack application data in sync with external systems efficiently by only processing records which have been created or modified during a given timeframe. By _incrementally_ processing new or modified records it possible to maintain a low level of latency between a Knack application and its dependents without placing undue demand on the Knack application stack, even when managing large datasets.

Incremental loading is made possible by referencing a record's timestamp throughout the pipleine. Specifically:

- The [Knack configuration file](#knack-config) allows for a `modified_date_field`. This field must be exposed in the source container and must be configured in the Knack application to reliably maintain the datetime at which a record was last modified. Note that Knack does not have built-in funcionality to achieve this—it is incumbent upon the application builder to configure app rules accordingly.

- The [Postgres data store](#postgres-data-store) relies on a stored procedure to maintain an `updated_at` timestamp which is set to the current datetime whenever a record is created or modified.

- The processing scripts in this repository accept a `--date` flag which will be used as a filter when extracting records from the Knack application or the Postgres database. Only records which were modified on or after this date will be ingested into the ETL pipeline.

## Security Considerations

Knack's built-in record IDs are used as primary keys throughout this pipeline, and are exposed in [any public datasets](#publish-records-to-the-open-data-portal) to which data is published. Be aware that if your Knack app exposes public pages that rely on the obscurity of a Knack record ID to prevent unwanted visitors, you should not use this ETL pipeline to publish any data from such containers.

## System Architecture

### Postgres data store

A PostgreSQL database serves as a staging area for Knack records to be published to downstream systems. Knack data lives in two tables within the `api` schema, described below.

#### `knack`

This is the primary table which holds all knack records. Records are uniquely identified by the Knack application ID (`app_id`), the container ID (`container_id`) of the source Knack object or view, and the Knack record ID (`record_id`) of the record. The entire raw Knack record data is stored as JSON in the `record` column.

Note that although Knack record IDs are globally unique, this table may hold multiple copies of the same record, but with a different field set, because the same record may be sourced from different views. **You should always reference all primary key columns when reading from or writing data to this table.**

| **Column name** | **Data type**              | **Constraint** | **Note**                      |
| --------------- | -------------------------- | -------------- | ----------------------------- |
| `app_id`        | `text`                     | `primary key`  |                               |
| `container_id`  | `text`                     | `primary key`  |                               |
| `record_id`     | `text`                     | `primary key`  |                               |
| `record`        | `json`                     | `not null`     |                               |
| `updated_at`    | `timestamp with time zone` | `not null`     | _set via trigger `on update`_ |

#### `knack_metadata`

This table holds Knack application metadata, which is kept in sync and relied upon by the scripts in this repo. We store app metadata in the database a as means to reduce API load on the Knack application itself.

| **Column name** | **Data type** | **Constraint** |
| --------------- | ------------- | -------------- |
| `app_id`        | `text`        | `primary key`  |
| `metadata`      | `json`        | `not null`     |

### PostgREST API

The Postgres data store is fronted by a [Postgrest](http://postgrest.com/) API which is used for all reading and writing to the database. The PostgREST server runs on an EC2 instance.

All operations within the `api` schema that is exposed via PostgREST must be authenticated with a valid JWT for the dedicated Postgres user. The JWT secret and API user name are stored in the DTS password manager.

## Configuration

### App names

Throughout these modules we use predefined names to refer to Knack applications. We pull these names out of thin air, but they must be used conistently, because they are used to identify the correct Knack auth tokens and ETL configuration parameters in `services/config/knack.py`. Whenever you see a variable or CLI argument named `app_name`, we're referring to these pre-defined app names.

| **App name**         | **Description**                                                                    |
| -------------------- | ---------------------------------------------------------------------------------- |
| `data-tracker`       | The [AMD Data Tracker](https://www.austinmobility.io/products/2068)                |
| `signs-markings`     | The [Signs & Markings Operations App](https://www.austinmobility.io/products/2906) |
| `finance-purchasing` | The [Finance & Purchasing App](https://atd.knack.com/finance-purchasing)           |

### Auth & environmental variables

The supported environmental variables for using these scripts are listed below. The required variables vary for each processing script—refer to their documentation:

- `AGOL_USERNAME`: An ArcGIS Online user name that has access to the destination AGOL service.
- `AGOL_PASSWORD`: The ArcGIS Online account password
- `KNACK_APP_ID`: The Knack App ID of the application you need to access
- `KNACK_API_KEY`: The Knack API key of the application you need to access
- `SOCRATA_API_KEY_ID`: The Socrata API key of the account you need to access
- `SOCRATA_API_KEY_SECRET`: The Socrata API key secret
- `SOCRATA_APP_TOKEN`: The Socrata app token
- `PGREST_JWT`: A JSON web token used to authenticate PostgREST requests
- `PGREST_ENDPOINT`: The URL of the PostgREST server. Currently available at `https://atd-knack-services.austinmobility.io`

If you'd like to run locally in Docker, create an [environment file](https://docs.docker.com/compose/env-file/) and pass it to `docker run`. For development purpsoses, this command also overwrites the contents of the container's `/app` directory with your local copy of the repo:

```
$ docker run -it --rm --env-file env_file -v <absolute-path-to-this-repo>:/app atddocker/atd-knack-services:production services/records_to_socrata.py -a data-tracker -c object_11
```

### Knack config

Each Knack container which will be processed must have configuration parameters defined in `services/config/knack.py`, as follows:

```python
CONFIG = {
    <str: app_name>: {
        <str: container_id>: <dict: container kwargs>
        },
    },
}
```

- `app_name` (`str`): The Knack application name. See note about application names, above.
- `container_id` (`str`): a Knack object or view key (e.g., `object_11`) which holds the records to be processed.

#### Container properties

- `scene` (`str`): If the container is a Knack view, this is required, and refers to the Knack scene ID which contains the view.
- `modified_date_field` (`str`, optional): A knack field ID (e.g., `field_123`) which defines when each record was last modified. If provided, this field will be used to filter records for each ETL run. If not provided, all records will always be fetched/processed from the source Knack container.
- `description` (`str`, optional): a description of what kind of record this container holds.
- `socrata_resource_id` (`str`, optional): The Socrata resource ID of the destination dataset. This is required if publshing to Socrata.
- `location_field_id` (`str`, optional): The field key which will be translated to Socrata "location" field types or an ArcGIS Online point geometry.
- `service_id` (`str`, optional): The ArcGIS Online feature service identifier. Required to publish to ArcGIS Online.
- `layer_id` (`int`, optional): The ArcGIS Online layer ID of the the destination layer in the feature service.
- `item_type` (`str`, optional): The type ArcGIS Online layer. Must be either `layer` or `table`.
- `dest_apps` (`dict`, optional): Destination app information for [publishing to another knack app](#publish-records-to-another-knack-app)
- `no_replace_socrata` (`bool`, optional): If true, blocks a `replace` operation on the destination Socrata dataset.
- `append_timestamps_socrata` (`dict` (`{'key': <timestamp_column_name> (str)}`>, optional): If present, a current timestamp will be added to each record at the given column name `key`.

## Services (`/services`)

### Load app metadata to Postgres

Use `metadata_to_postgrest.py` to load an application's metadata to Postgres. Metadata
will be proessed for the app ID provided in the `KNACK_APP_ID` environmental variable.

To avoid repeated API calls, Knack app metadata is stored alongside records in the Postgres database. This means that schema changes in your Knack app need to be kept in sync with Postgres in order to ensure that records published to downstream systems reflect these changes. As such, you should update the Knack metadata stored in Postgres whenever you make a schema change to a container. After updating the metadata, you should also run a full replacement of the Knack record data from Knack to Postgres, and from Postgres to any downstream recipients. See also [Dealing with Schema Changes](#dealing-with-schema-changes).

```shell
$ python metadata_to_postgrest.py
```

#### CLI arguments

- `--app-name, -a` (`str`, required): the name of the source Knack application

### Load knack records to Postgres

Use `records_to_postgrest.py` to incrementally load data from a Knack container (an object or view) to the `knack` table in Postgres.

```shell
$ python records_to_postgrest.py \
    -a data-tracker \
    -c view_1 \
    -d "2020-09-08T09:21:08-05:00"
```

#### CLI arguments

- `--app-name, -a` (`str`, required): the name of the source Knack application
- `--container, -c` (`str`, required): the object or view key of the source container
- `--date, -d` (`str`, optional): an ISO-8601-compliant date string. If no timezone is provided, GMT is assumed. Only records which were modified at or after this date will be processed. If excluded, all records will be processed.

### Load Knack metadata to Postgres

```shell
$ python metadata_to_postrest.py
```

#### CLI arguments

None. Ensure your `KNACK_APP_ID` environmental variable is set to the app whose metadata you will be publish.

### Publish records to the open data portal

#### Socrata Dataset Configuration

Use `records_to_socrata.py` to publish a Knack container to the Open Data Portal (aka, Socrata).

When publishing Knack data to a Socrata dataset, the Socrata dataset must be configured with an ID field which will be automatically populated with Knack's built-in record IDs.

The field's display name can be freely-defined, but the field name must be `id` and the field type must be `text`. This field must also be assigned as the dataset's [row identifer](https://support.socrata.com/hc/en-us/articles/360008065493) to ensure that upserts are handled properly.

If you have a conflicting field in your Knack data named "ID", you should as general best practice rename it. If you absolutely must keep your "ID" field in Knack, this column name will be translated to `_id` when publishing to Socrata, so configure your dataset accordingly.

With the exception of the ID field, all Knack field names will be translated to Socrata-compliant field names by replacing spaces with underscores and making all characters lowercase.

Knack container field names missing from the Socrata dataset's fields will be removed from the payload before publishing.

```shell
$ python records_to_socrata.py \
    -a data-tracker \
    -c view_1 \
    -d "2020-09-08T09:21:08-05:00"
```

#### CLI arguments

- `--app-name, -a` (`str`, required): the name of the source Knack application
- `--container, -c` (`str`, required): the object or view key of the source container
- `--date, -d` (`str`, optional): an ISO-8601-compliant date string. If no timezone is provided, GMT is assumed. Only records which were modified at or after this date will be processed. If excluded, all records will be processed and the destination dataset will be
  _completely replaced_.

### Publish records to ArcGIS Online

Use `records_to_agol.py` to publish a Knack container to an ArcGIS Online layer.

#### About timestamps

AGOL stores all timestamps in UTC time. That means, for example, that when you see a “Created Date” field on a sign work order in AGOL, the time is displayed in UTC, not local time.

In the old ETL pipeline, we were offsetting our timestamps to essentially trick AGOL so that it displayed timestamps in local time. This makes make it easier for our users to work with the data, because they don’t have to worry about timestamp conversions—but it adds overhead to the ETL and is really not ideal from a data quality perspective.

This ETL pipeline does not do this timestamp conversion—timestamps will be shown in UTC time. Unfortunately, this is not very transparent in AGOL, because neither the timezone name nor offset are exposed in AGOL apps.

#### About geometries

This service currently supports Esri's `point` and `multipoint` [geometry types](https://developers.arcgis.com/documentation/common-data-types/geometry-objects.htm). The geometry type is detected automatically based on a Knack record's location field type. A simple point geometry is used when the location field's value is a single `dict` object with latitude and longitude properties. A multipoint geometry will be created if the location field's value is an array type (ie, the field belongs to a member of a child record in a one-many relationship).

```shell
$ python records_to_agol.py \
    -a data-tracker \
    -c view_1 \
    -d 2021-01-01
```

#### CLI arguments

- `--app-name, -a` (`str`, required): the name of the source Knack application
- `--container, -c` (`str`, required): the object or view key of the source container
- `--date, -d` (`str`, optional): an ISO-8601-compliant date string. If no timezone is provided, GMT is assumed. Only records which were modified at or after this date will be processed. If excluded, all records will be processed and the destination dataset will be
  _completely replaced_.

### Publish records to another Knack app

Use `records_to_knack.py` to publish records to another Knack application. Records may be sourced from any Knack container, but may only be published to a single Knack object. It works like this:

- Records for both the source and destination apps must be stored in Postgres via `records_to_postgrest.py`.
- On execution, `records_to_knack.py` fetches records from the source and destination apps.
- Source and destination records are evaluated for differences
- Any new or modified records in the source app are pushed to the destination app

#### Configuration

Both the source and destination apps must be configured to publish their records to Postgres using `records_to_postgrest.py`.

In addition to the standard properties in `config/knack.py`, the _source app_ requires an additional `dest_apps` entry that holds info about each destination app. For example:

```python
"finance-purchasing": {
    "view_788": {
        "description": "Inventory items",
        "scene": "scene_84",
        "modified_date_field": "field_374",
        "dest_apps": {
            "data-tracker": {
                # destination records will be fetched from this container and compared to the source
                "container": "view_2863",
                "description": "Inventory items",
                "scene": "scene_1170",
                "modified_date_field": "field_1229",
                # new/modified records will be upserted to this object in the destination app
                "object": "object_15",
            },
        },
    },
}
```

In addition to the `config/knack.py` setup, field mappings must be defined in `config/field_maps.py`. See this file for additional information.

```python
FIELD_MAPS = {
    "finance-purchasing": {  # the source app name
        "view_788": [   # the source app container
            {
                # the source field key
                "src": "field_918",
                # the dest field key for the given destination app
                "data-tracker": "field_3812",
                # If the field is the unique record ID. One and only one is required per source application.
                "primary_key": True,
            },
            {
                "src": "field_720",
                "data-tracker": "field_3467",
            },
            {
                "src": "field_363",
                "data-tracker": "field_243",
                # Optional handler function
                "handler": handle_connection,
            },
        ],
    },
}
```

#### Environmental Variables

- `KNACK_APP_ID_SRC`: The Knack App ID of the source Knack application
- `KNACK_API_KEY_SRC`: The Knack API key of the source Knack application
- `KNACK_APP_ID_DEST`: The Knack App ID of the destination Knack application
- `KNACK_API_KEY_DEST`: The Knack API key of the destination Knack application
- `PGREST_JWT`: A JSON web token used to authenticate PostgREST requests
- `PGREST_ENDPOINT`: The URL of the PostgREST server. Currently available at `https://atd-knack-services.austinmobility.io`

#### CLI arguments

- `--app-name, -a` (`str`, required): the name of the source Knack application
- `--container, -c` (`str`, required): the object or view key of the source container
- `--app-name-dest, -dest` (`str`, required): the name of the destination Knack application
- `--date, -d` (`str`, optional): an ISO-8601-compliant date string. If no timezone is provided, GMT is assumed. Only records which were modified at or after this date will be processed. If excluded, all records will be processed.

## Utils (`/services/utils`)

The package contains utilities for fetching and pushing data between Knack applications and PostgREST.

## Common Tasks

### Configuring a Knack container

Because [Knack views](https://support.knack.com/hc/en-us/articles/226221788-About-Views) allow you to add columns from multiple objects to a single table, they will generally be your container of choice (as opposed to an "object") for surfacing data that will be published to other systems.

We have adopted the convention of dedicating part of each Knack application to an "API Views" page which contains any views in the app that are used for integration purposes.

When creating an API view, simply build a table view with the the relevant columns. Be aware that field name handling is specific to each script in `/services`, but in general the field names in the destination dataset need to match the field name in the Knack source _object_, even when the source container is a view. Re-naming a field _in the view itself_ has no effect on the field names used in the ETL. This is a limitation of the Knack API, which does not readily expose the field names in views. See the documentation for each particular service for more details on field name handling.

Note also that that. as a best practice, you should not use connection fields in Knack API view, because the value in that field will be the "[Display Field](https://support.knack.com/hc/en-us/articles/226588888-Working-With-Objects#edit-objects)" value as it is configured for the object. If someone were to change the display field for that object, it could break the ETL. Instead, when you're adding columns to the view, use the object drop-down menu to pick the related object, then add the field from that object that you want in the view.

### Dealing with schema changes

Follow these steps to add a new column to a dataset.

1. Add the new column to any destination datasets. Keep in mind that the column name in the destination dataset must match the column name in the source Knack object, except that all spaces will be replaced with underscores and all characters converted to lowercase.

2. Add the new column to the Knack view (aka container). Doing this will break the ETL until you complete the steps that follow!

3. Update the Knack app's metadata in Postgrest. See also [Load app metadata to Postgres](#load-app-metadata-to-postgres).

```shell
$ python metadata_to_postgrest.py
```

4. Re-load _all_ records from Knack to Postgrest. This ensures that every record matches the new schema. Do this by omitting the `--date/-d` argument from the shell command:

```shell
$ python records_to_postgrest.py \
    -a some-app \
    -c view_1 \
```

5. Run all downstream ETLs (`records_to_agol.py`, `records_to_socrata.py`, etc.) to populate the destination datasets with the new data. Again, omit the `--date/-d` argument to ensure all records are processed.

### Automate tasks with Airflow and Docker

See [atd-airflow](https://github.com/cityofaustin/atd-airflow) for examples of how these services can be deployed to run on a schedule. Airflow deployments rely on Docker, and this repo includes a `Dockerfile` which defines the runtime environment for all services, and is automatically built and pushed to DockerHub using Github actions.

If you add a Python package dependency to any service, adding that package to `requirements.txt` is enough to ensure that the next Docker build will include that package in the environment. Our Airflow instance refreshes its DAG's Docker containers every 5 minutes, so it will always be running the latest environment.

## Troubleshooting

### ArcGIS Online (AGOL)

Depending on the presence of the `--date` argument, `records_to_agol.py` uses two different approaches to delete AGOL records.

When the `--date` argument is present, the script simulates an upsert by deleting from AGOL any records present in the current payload. This is done with a `WHERE` clause:

```sql
WHERE 'id' in <arrray-of-knack-ids>
```

Alternatively, when no `--date` argument is present, all records in the destination layer are deleted with:

```sql
WHERE 1=1
```

When troubleshooting an obscure AGOL error, it's often a good starting point to manually run `records_to_agol.py` without the `--date` argument, as this can seemingly clear up any underlying versioning/indexing issues within AGOL's internal state.

One such error message looks like this:

```
Error: Violation of PRIMARY KEY constraint [value]. Cannot insert duplicate key in object [value]. The duplicate key value is [value].
```
