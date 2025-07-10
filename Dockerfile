FROM python:3.12-slim

# Set environment variables
ARG ANKERUSER=youranker@emailaccount.com
ARG ANKERPASSWORD=anker_password
ARG ANKERCOUNTRY=de
ARG ANKER_SOLIX_DUID=APCGQ80E1234567_
ARG WEATHER_API_URL=https://api.openweathermap.org/data/2.5/weather?lat=11.12345&lon=11.12345&appid=12345678890abcdefgh

ENV ANKERUSER=$ANKERUSER \
    ANKERPASSWORD=$ANKERPASSWORD \
    ANKERCOUNTRY=$ANKERCOUNTRY \
    ANKER_SOLIX_DUID=$ANKER_SOLIX_DUID \
    USE_SIGNAL=$USE_SIGNAL \
    SIGNAL_SENDER=$SIGNAL_SENDER \
    SIGNAL_TARGET=$SIGNAL_TARGET \
    SIGNAL_API_URL=$SIGNAL_API_URL \
    WEATHER_API_URL=$WEATHER_API_URL

WORKDIR /app

# Install all dependencies, pipenv, and clone repo in one layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    pip install pipenv && \
    git clone https://github.com/thomluther/anker-solix-api.git /app/anker_api && \
    rm -rf /var/lib/apt/lists/*

# Copy files and install python dependencies
COPY Pipfile Pipfile.lock script.py /app/

RUN pipenv lock --clear && \
    pipenv update && \
    pipenv lock && \
    pipenv install requests fastapi uvicorn && \
    pipenv sync -d && \
    pipenv install --deploy --ignore-pipfile

CMD ["pipenv", "run", "python", "script.py"]
