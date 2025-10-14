FROM python:3.14-slim

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
    WEATHER_API_URL=$WEATHER_API_URL

WORKDIR /app

# Install Poetry
RUN apt-get update && \
    apt-get install -y --no-install-recommends git curl python3-venv pipx && \
    pipx install poetry cryptography aiohttp aiofiles paho-mqtt && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry && \
    git clone https://github.com/thomluther/anker-solix-api.git /app/anker_api && \
    rm -rf /var/lib/apt/lists/*

# Copy app files
COPY pyproject.toml script.py /app/

# Install dependencies
RUN poetry install --no-interaction --no-ansi

# Add extra packages manually
RUN poetry add requests fastapi uvicorn

# Run app
CMD ["poetry", "run", "python", "script.py"]
