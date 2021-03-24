# epilepsy-database-visualisation


## Prerequisites

You need to install [docker](https://docs.docker.com/get-docker/) and [docker-compose](https://docs.docker.com/compose/install/).


## Setup

To launch Grafana, mysql, postgres and influxdb on local, you **MUST SET UP ALL THE RELEVANT ENVIRONMENT VARIABLES** (e.g in an **env.sh** file), then launch the following command to run the containers:

```sh
    $ source env.sh  # Set env vars
    $ rm -rf conf/provisioning/datasources/datasources.yml
    $ envsubst < "conf/template.yml" > "conf/provisioning/datasources/datasources.yml"  # Customize config files with specified env vars
    $ docker-compose up
```

**Warning**: You might need to edit the **datasource URL** of the mysql datasource for Grafana as the current one (cf: "docker.for.mac.localhost:3306") will only work on MAC OS. If you are not using a MAC OS, you might need to set your private ip address.

You can do it before running *docker-compose up* or after within Grafana as the datasources are editable.

Enjoy !
