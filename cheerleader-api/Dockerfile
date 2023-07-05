# syntax = docker/dockerfile:1.2

FROM python:3.11.4-slim-bullseye

ENV PYTHONUNBUFFERED 1

WORKDIR /app/cheerleader

COPY requirements.txt ./
RUN pip install -r requirements.txt --no-cache-dir
COPY . ./

RUN --mount=type=secret,id=_env,dst=/etc/secrets/.env source /etc/secrets/.env

RUN python3 manage.py makemigrations && python3 manage.py migrate

CMD ["gunicorn", "cheerleader.wsgi", "--bind", "0.0.0.0:8000"]
EXPOSE 8000
