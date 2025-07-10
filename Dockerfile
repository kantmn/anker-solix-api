ENV MY_VAR=some_value
ENV ANKERUSER=youranker@emailaccount.com
ENV ANKERPASSWORD=anker_password
ENV ANKERCOUNTRY=DE
ENV ANKER_SOLIX_DUID=APCGQ80E1234567_
ENV USE_SIGNAL=true
ENV SIGNAL_SENDER=+49123456789
ENV SIGNAL_TARGET=+49123456789
ENV SIGNAL_API_URL=http://signal-cli-rest-api:8080/v2/send
ENV WEATHER_API_URL=https://api.openweathermap.org/data/2.5/weather?lat=11.12345&lon=11.12345&appid=12345678890abcdefgh

FROM python:3.12-slim

# Install dependencies
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Install pipenv
RUN pip install pipenv

# Set the working directory
WORKDIR /app

# Copy the Pipfile and Pipfile.lock to the container
COPY Pipfile Pipfile.lock script.py /app/

# Clear the lock file and regenerate it
RUN pipenv lock --clear

# Update and sync dependencies
RUN pipenv update && pipenv lock
RUN pipenv install requests fastapi uvicorn
RUN pipenv sync -d

# Clone the repo into the container
RUN git clone https://github.com/thomluther/anker-solix-api.git /app/anker_api

# Install dependencies using pipenv
RUN pipenv install --deploy --ignore-pipfile

# Set the entrypoint (adjust to your application)
CMD ["pipenv", "run", "python", "script.py"]
