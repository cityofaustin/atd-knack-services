# atd-knack-services

ATD Knack Services is a set of python modules which automate the flow of data from ATD's Knack applications to downstream systems.

![basic data flow](docs/basic_flow.jpg)

## Contents

- [Core Concepts](#core-concepts)
- [System Architecture](#system-architecture)
- [Configuration](#configuration)
- [Services](<#services-(`/services`)>)
- [Utils](<#utils-(`/services/utils`)>)
- [Common Tasks](#common-tasks)

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

- The [Knack configuration file](#knack-config) requires that all entries include a `modified_date_field_id`. This field must be exposed in the source container and must be configured in the Knack application to reliably maintain the datetime at which a record was last modified. Note that Knack does not have built-in funcionality to achieve this—it is incumbent upon the application builder to configure app rules accordingly.

- The [Postges data store](#postgres-data-store) relies on a stored procedure to maintain an `updated_at` timestamp which is set to the current datetime whenever a record is created or modified.

- The processing scripts in this repository accept a `--date` flag which will be used as a filter when extracting records from the Knack application or the Postgres database. Only records which were modified on or after this date will be ingested into the ETL pipeline.

In order to achieve incremental loads when writing data, these services require that destination system support an "upsert" method. Although both Postgres(t) and Socrata support upserting, ArcGIS Online does not\*. In such cases, a full replace of the destination dataset is applied on each ETL run. See `[Publish records to ArcGIS Online](#publish-records-to-arcgis-online) for more details.

\*The ArcGIS Python API claims support for an uspert method, documented [here](https://developers.arcgis.com/python/api-reference/arcgis.features.toc.html#featurelayer), but we abandoned this approach after repeated attempts to debug cryptic error messages.

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

### Auth & environmental variables

The required environmental variables for using these scripts are:

- `AGOL_USERNAME`: An ArcGIS Online user name that has access to the destination AGOL service
- `AGOL_PASSWORD`: The ArcGIS Online account password
- `KNACK_APP_ID`: The Knack App ID of the application you need to access
- `KNACK_API_KEY`: The Knack API key of the application you need to access
- `SOCRATA_USERNAME`: A Socrata user name that has access to the destination Socrata dataset
- `SOCRATA_PASSWORD`: The Socrata account password
- `PGREST_JWT`: A JSON web token used to authenticate PostgREST requests
- `PGREST_ENDPOINT`: The URL of the PostgREST server. Currently available at `https://atd-knack-services.austinmobility.io`

If you'd like to run locally in Docker, create an [environment file](https://docs.docker.com/compose/env-file/) and pass it to `docker run`. For development purpsoses, this command also overwrites the contents of the container's `/app` directory with your local copy of the repo:

```
$ docker run -it --rm --env-file env_file -v <absolute-path-to-this-repo>:/app atddocker/atd-knack-services:production services/records_to_socrata.py -a data-tracker -c object_11 -e prod
```

### Knack config

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

The field's display name can be freely-defined, but the field name must be `id` and they field type must be `text`. This field must also be assigned as the dataset's [row identifer](https://support.socrata.com/hc/en-us/articles/360008065493) to ensure that upserts are handled properly.

If you have a conflicting field in your Knack data named "ID", you should as general best practice rename it. If you absolutely must keep your "ID" field in Knack, this column name will be translated to `_id` when publishing to Socrata, so configure your dataset accordingly.

With the exception of the ID field, all Knack field names will be translated to Socrata-compliant field names by replacing spaces with underscores and making all characters lowercase.

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

The package contains utilities for fetching and pushing data between Knack applications and PostgREST.

TODO

## Common Tasks

### Dealing with schema changes

To avoid repeated API calls, Knack app metadata is stored alongside records in the Postgres database. This means that schema changes in your Knack app need to be kept in sync with Postgres in order to ensure that records published to downstream systems reflect these changes. As such, you should update the Knack metadata stored in Postgres whenever you make a schema change to a container. After updating the metadata, you should also run a full replacement of the Knack record data from Knack to Postgres, and from Postgres to any downstream recipients.

### Other

- Configure a new container
- Schema changes/updating metadata
- Adding a new destination dataset
- Extending/development

## Deployment

An end-to-end ETL process will involve creating at least three Airflow tasks:

- Load app metadata to Postgres
- Load Knack records to Postgres
- Publish Knack records to destination system

## TODO

- document docker CI
- disable legacy publisher for those that have been migrated
- document field matching. think about field mapping...
- staging instance
- document Truncating/replacing
