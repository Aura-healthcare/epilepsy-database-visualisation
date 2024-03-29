# InfluxDB env vars
export INFLUXDB_USERNAME=admin
export INFLUXDB_PASSWORD=auraadmin
export INFLUXDB_DATABASE=hackathon

# Grafana env vars
export GRAFANA_USERNAME=admin
export GRAFANA_PASSWORD=admin

# MYSQL env vars
export MYSQL_ROOT_PASSWORD=admin
export MYSQL_DATABASE=aura
export MYSQL_USER=admin
export MYSQL_PASSWORD=admin
# For MAC OS. For others OS, you must set your private IP address.
export MYSQL_HOST_IP=$(hostname -I | cut -d ' ' -f 2)

# PostgreSQL env vars
export POSTGRES_HOST_URL=$(hostname -I | cut -d ' ' -f 3)
export POSTGRES_DATABASE=postgres
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres
