# anker-solix-docker-api

Provides a docker container to run python 3.12 with dependencies for https://github.com/thomluther/anker-solix-api

docker pull ghcr.io/kantmn/anker-solix-docker-api:latest

Map container Dir /app to your local path where the anker-solix-api is available

The container will run script.py inside on startup

make sure you have a script like this or similar https://github.com/user-attachments/files/17829418/api_2_prometheus_webservice.txt

you may have to change the paths inside the script to /app to work
