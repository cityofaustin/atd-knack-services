# Local Development

Requires Git, Docker, and Docker Compose.

### Start the API

1. Clone `atd-knack-services` and `cd` into it.
2. Follow [the docs](https://github.com/cityofaustin/atd-knack-services#auth--environmental-variables) to create an environment file in the root directory. You'll need these four variables to load data from Knack into your local postgrest instance:

```
KNACK_APP_ID=<your knack app id>
KNACK_API_KEY=<your knack api key>
# these PGREST vars must match the values defined in docker-compose.yml
PGREST_JWT=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoibXlfYXBpX3VzZXIifQ.4dRa7CiDQUxDmnHkRBBAfZ2qSfAgQXz97AahDAU7IAg
PGREST_ENDPOINT=http://127.0.0.1:3000
```

3. Use `docker-compose` to start the postgres DB and postgrest API:

`$ docker-compose -f dev/docker-compose.yml up`

You can confirm the API is running opening `http://127.0.0.1:3000` in your browser—it should return the API's JSON definition. If you'd like to connect to the database using a GUI client (e.g., TablePlus), you cannect with:

-  database name: postgres
-  username: postgres
-  password: password

(These details are defined in `docker-compose.yml`)

### Run Scripts

Yay, you're ready to run the scripts! In a separate terminal window, you can run any script by mounting your local copy of the repo and passing in your `env_file`.

1. Start by loading your app's metadata

```
 docker run -it \
    --rm \
    --network host \
    --env-file env_file \
    -v <absolute-path-to-this-repo>:/app \
    atddocker/atd-knack-services:production \
    services/metadata_to_postgrest.py
```

2. To load records, you'll need to define a new entry in `/services/config/knackpy.py`, or use an existing container.

-  See: [configuration docs](https://github.com/cityofaustin/atd-knack-services#configuration)
-  [`records_to_postgrest.py` docs](https://github.com/cityofaustin/atd-knack-services#load-knack-records-to-postgres)

```
$ docker run -it \
    --rm \
    --network host \
    --env-file env_file \
    -v <absolute-path-to-this-repo>:/app \
    atddocker/atd-knack-services:production \
    services/records_to_socrata.py -a <my-app-name> -c <my-container-id>
```
