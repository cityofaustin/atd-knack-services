# atd-knack-services

Integration services for ATD's Knack applications.

## Design

ATD Knack Services is comprised of a Python library (`/services`) and scripts (`/scripts`) which automate the flow of data from ATD's Knack applications to downstream systems.

These utilities are designed to:

- incrementally offload Knack application records and metadata as a JSON documents in a collection of S3 data stores
- incrementally fetch records and publish them to external systems such as Socrata and ArcGIS Online
- lay the groundwork for further integration with a data lake and/or a data warehouse
- be deployed in Airflow or similar task management frameworks

![basic data flow](docs/basic_flow.jpg)

## Configuration

### S3 Data Store

Data is stored in an S3 bucket (`s3://atd-knack-services`), with one subdirectory per Knack application per environment. Each app subdirectory contains a subdirectory for each container, which holds invdividual records stored as JSON a file with its `id` serving as the filename. As such, each store follows the naming pattern `s3://atd-knack-services/<environment>/<app-name>/<container-id>`.

Application metadata is also stored as a JSON file at the root of each S3 bucket.

```
. s3://atd-knack-services
|-- prod
|   |-- data-tracker
|       |-- metadata.json
|       |-- view_1
|           |-- 5f31673f7a63820015ef4c85.json
|           |-- 5b34fbc85295dx37f1402543.json
|           |-- 5b34fbc85295de37y1402337.json
|           |...
```

## Services (`/services`)

### Load App Metadata to S3

Use `metadata_to_s3.py` to load an application's metadata to S3.

```shell
$ python metadata_to_s3.py \
    --app-name data-tracker \
    --env prod \
```

#### CLI arguments

- `--app-name, -a` (`str`, required): the name of the source Knack application
- `--env, -e` (`str`, required): The application environment. Must be `prod` or `dev`.

### Load Knack Records to S3

Use `records_to_S3.py` to incrementally load data from a Knack container (an object or view) to an S3 bucket.

```shell
$ python records_to_S3.py \
    -a data-tracker \
    -c view_1 \
    -e prod \
    -d "2020-09-08T09:21:08-05:00"
```

### Publish Records to the Open Data Portal

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
- `--date, -d` (`str`, required): an ISO-8601-compliant date string with timezone. only records which were modified at or after this date will be processed.

## Utils (`/services/utils`)

The package contains utilities for fetching and pushing data between Knack applications and AWS S3.

### `utils.s3.upload`

Multi-threaded uploading of file-like objects to S3.

### `utils.s3.download_many`

Multi-threaded downloading of file objects from S3.

### `utils.s3.download_one`

Download a single file from S3.

## How To

- Create bucket(s)
- Configure auth
- Add container configuration file to /services/config
- Create DAGs

An end-to-end ETL process will involve creating at least three Airflow tasks:

- Load app metadata to S3
- Load Knack records to S3
- Publish Knack records to destination system
