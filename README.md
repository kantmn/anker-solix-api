# anker-solix-docker-api

Provides a docker container to run python 3.12 with dependencies for https://github.com/thomluther/anker-solix-api

docker pull ghcr.io/kantmn/anker-solix-docker-api:latest

Map container Dir /app to your local path where the anker-solix-api is available

The container will run script.py inside on startup

make sure you have a script like this or similar to the script.py in this repo

you may have to change the paths inside the script to /app to work

the script above runs a webserver under port 5000

using http://ip:5000/metrics you can retrieve data from the anker solix api and use this metrics inside prometheus / grafana
