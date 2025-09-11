[![Security Scan](https://github.com/kantmn/anker-solix-api/actions/workflows/codacy.yml/badge.svg)](https://github.com/kantmn/anker-solix-api/actions/workflows/codacy.yml)
[![CodeQL](https://github.com/kantmn/anker-solix-api/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/kantmn/anker-solix-api/actions/workflows/github-code-scanning/codeql)
[![Dependabot](https://github.com/kantmn/anker-solix-api/actions/workflows/dependabot/dependabot-updates/badge.svg)](https://github.com/kantmn/anker-solix-api/actions/workflows/dependabot/dependabot-updates)
[![Release building](https://github.com/kantmn/anker-solix-api/actions/workflows/release.yml/badge.svg)](https://github.com/kantmn/anker-solix-api/actions/workflows/release.yml)

# anker-solix-api docker image
Provides a docker container to run a python 3.12 script with dependencies for https://github.com/thomluther/anker-solix-api
This docker provides an http service under port http://ip:5000/metrics


# docker container setup
pull the container as needed, there are two plattforms (amd64/arm64) available.

``
docker pull ghcr.io/kantmn/anker-solix-api:latest
``

if you want to use fixed version use
 
``
docker pull ghcr.io/kantmn/anker-solix-api:yyyy.mm
``

Map path from container 
> /logs

This will locate the log metrics only


Add and fille the following Docker Env variables as needed
```
ANKERUSER=YOUR_ANKER_LOGIN_EMAIL

ANKERPASSWORD=YOU_ANKER_PASSWORD

ANKERCOUNTRY=YOUR_REGION (e.g. DE=Germany)

ANKER_SOLIX_DUID=YOUR_ANKER_GUID (this removes the APCGQ80E12344567_ from the requests)

WEATHER_API_URL=YOUR_OPENWEATHERMAP_API_URL
(contains coords and api key, key is free of charge and can be obtainted https://home.openweathermap.org/users/sign_up example for api URL https://api.openweathermap.org/data/2.5/weather?lat=11.23456&lon=22.123456&appid=API_KEY_FROM_OPENWEATHER)
```
The Script is running in a loop, with sleep time, so only ending when container is stopped, should recover from crash

# prometheus connection
The metrics is compatible for a prometheus crawling job (https://github.com/prometheus/prometheus)

for example open
`
/etc/prometheus.yml
`
and add
````
- job_name: "anker-solix-api"
    scrape_interval: 5s
    static_configs:
      - targets: ["ip:5000"]
````

# grafana dashboard
afterwards those metrics can be used e.g. in grafana to display graphs etc
see an examples here
<img width="1920" height="1862" alt="Screenshot 2025-07-10 at 16-38-44 Export - Dashboards - Grafana" src="https://github.com/user-attachments/assets/17e585ea-2193-48b6-a61e-f17b984dba42" />
