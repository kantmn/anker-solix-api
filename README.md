# anker-solix-docker-api
Provides a docker container to run a python 3.12 script with dependencies for https://github.com/thomluther/anker-solix-api
This docker provides an http service under port http://ip:5000/metrics


# docker container setup
pull the container as needed, there are two plattforms (amd64/arm64) available as tags (latest/or yyyy-mm-dd) available.
``
docker pull ghcr.io/kantmn/anker-solix-api:latest
``

Map path from container 
> /app

to your local path where the anker-solix-api is available

The container will launch the file 
> script.py

inside the /app path on startup.

An example for this script is inside this repo, adjust it to your needs
The example script, needs to be added anker account credentials, see comments on the first lines
Script is running in a loop, with sleep time, so only ending when container is stopped, should recover from crash

you may have to change the paths inside the script to /app to work

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

#grafana
afterwards those metrics can be used e.g. in grafana to display graphs etc
see an examples here
![image](https://github.com/user-attachments/assets/87830c99-2b4a-42ce-aa7c-017fdc85151f)
