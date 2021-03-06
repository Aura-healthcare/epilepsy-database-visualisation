# epilepsy-database-visualisation


## Prerequisites

You need to install [docker](https://docs.docker.com/get-docker/) and [docker-compose](https://docs.docker.com/compose/install/).


## Setup

To launch Grafana, mysql and influxdb on local, run: 

```sh
    $ export INFLUXDB_USERNAME=admin
    $ export INFLUXDB_PASSWORD=admin
    $ export GRAFANA_USERNAME=admin
    $ export GRAFANA_PASSWORD=admin
    $ docker-compose up
```

**Warning**: You might need to edit the **datasource URL** of the mysql datasource for Grafana as the current one (cf: "docker.for.mac.localhost:3306") will only work on MAC OS.

You can do it before running *docker-compose up* or after within Grafana as the datasources are editable.

Enjoy !
