FROM python:3.11-slim-bullseye

RUN mkdir /app

COPY Pipfile /app

WORKDIR /app

RUN pip install pipenv && pipenv update

WORKDIR /app

COPY . /app/

EXPOSE 8000

ENTRYPOINT [ "pipenv", "run", "python", "main.py" ]
