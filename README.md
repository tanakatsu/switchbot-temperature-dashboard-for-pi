## SwitchBot Temperature Dashboard for Raspberry Pi

### Overview

This project provides a simple, lightweight monitoring stack for **Raspberry Pi**, designed to collect, store, and visualize temperature data from SwitchBot devices.

It consists of:
- A Python-based logging application that collects temperature data
- **InfluxDB** as a time-series database for storing the data
- **Grafana** for visualizing the data in real time

Using Docker Compose, InfluxDB and Grafana can be started quickly with minimal configuration.
Once the services are running, you can configure the data source and dashboard through the web UI and immediately start monitoring temperature trends.

### Prerequisites

Before getting started, make sure the following requirements are met:

- **Docker** is installed and running
  Docker is used to run InfluxDB and Grafana via Docker Compose.
  See the official documentation for installation instructions:
  https://docs.docker.com/get-docker/

- **uv** is installed
  `uv` is used to manage Python dependencies and run the logging application.
  Installation instructions can be found here:
  https://github.com/astral-sh/uv

These tools are required on your Raspberry Pi (or development machine) before proceeding to the next steps.

### Getting Started

1. Clone the repository:
   ```bash
   git clone
   ```
1. Navigate to the project directory:
   ```bash
   cd switchbot-temperature-dashboard-for-pi
   ```
1. Install the required dependencies:
   ```bash
   uv sync
   ```
1. Copy .env.example to .env and fill in your configurations:
   ```bash
   cp .env.example .env
   ```
1. Start the InfluxDB and Grafana:
   ```bash
   docker compose up -d
   ```
1. Configure Grafana:
    1. Log in to Grafana
        ```
        http://localhost:3000
        ```
        From development machine, you can access Grafana at `http://raspberrypi.local:3000`.
    1. Log in with the following credentials:
        - Username: `admin`
        - Password: value of the `GF_SECURITY_ADMIN_PASSWORD` environment variable
    1. Register InfluxDB as a Data Source
        1. Click Connections → Data sources from the left-hand menu
        1. Click Add data source and select InfluxDB
        1. Query Language
            - Select InfluxQL
        1. HTTP
            - URL: `http://influxdb:8086`
        1. Auth
            - Enable Basic auth
            - User: value of the `INFLUXDB_ADMIN_USER` environment variable
            - Password: value of the `INFLUXDB_ADMIN_PASSWORD` environment variable
        1. InfluxDB Details
            - Database: value of the `INFLUXDB_DB` environment variable
            - User: value of the environment `INFLUXDB_ADMIN_USER` variable
            - Password: value of the `INFLUXDB_ADMIN_PASSWORD` environment variable
            - HTTP Method: GET
            - Min time interval: 10m
        1. Click Save & test
            - You should see a message: "datasource is working."
1. Start the logging application:
   ```bash
   uv run main.py
   ```
1. Set up Dashboard (Grafana):
    1. Create a New Dashboard
        1. In Grafana, click Dashboards from the left-hand menu
        1. Click New → New dashboard
        1. Click Add visualization
        1. Select data source
            - Select influxdb
    1. Configure the Panel Query
        1. In Query Editor:
            - Choose "sensor" in "select measurement"
            - Choose "temp_c" in "field(value)"
            - Click "+" in "GROUP BY" and choose "tag(sensor_id::tag)"
        1. Configure Visualization
            1. In the Visualization panel:
                - Select Time series (recommended for temperature data)
            1. Set a panel title, for example:
                - Title: Temperature
        1. Save the Dashboard
            1. Click Save dashboard (disk icon in the top right)
            1. Enter a dashboard name, for example:
                - SwitchBot Temperature Dashboard
            1. Click Save
        1. Verify the Data
            1. If data is being written correctly to InfluxDB, the graph should display time-series data.
            1. Adjust the time range (top-right corner) if no data is visible.

        You have now successfully set up a Grafana dashboard connected to InfluxDB.
