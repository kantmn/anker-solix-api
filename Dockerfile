FROM python:3.12-slim

# Install dependencies
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Install pipenv
RUN pip install pipenv

# Set the working directory
WORKDIR /app

# Copy the Pipfile and Pipfile.lock to the container
COPY Pipfile Pipfile.lock /app/

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
