# Use the python 3.11 slim bullseye image as the base image
FROM python:3.11-slim-bullseye

# Create a directory named 'app' in the container
RUN mkdir /app

# Copy the Pipfile from the local directory to the 'app' directory in the container
COPY Pipfile /app

# Set the working directory to /app
WORKDIR /app

# Update the package lists and install curl, then install pipenv and update its dependencies
RUN apt update && apt install -y curl && pip install pipenv && pipenv update && rm -rf /var/lib/apt/lists/*

# Set the working directory to /app
WORKDIR /app

# Copy all files from the local directory to the 'app' directory in the container
COPY . /app/

# Expose port 8000
EXPOSE 8000

# Define the entry point for the container, using 'pipenv run' to run 'main.py' with Python
ENTRYPOINT [ "pipenv", "run", "python", "main.py" ]

# Add a health check to monitor the application's status, using curl to check if the server is responding
HEALTHCHECK --start-period=6s --interval=8s --timeout=6s CMD curl -f http://localhost:8000/ || exit 1
