FROM python:3.11.4-slim-bullseye

ENV PYTHONUNBUFFERED 1

WORKDIR /app/cheerleader

COPY requirements.txt ./
RUN pip install -r requirements.txt --no-cache-dir
COPY . ./

RUN ["chmod", "+x", "./docker-entrypoint.sh"]

CMD ./docker-entrypoint.sh
EXPOSE 8000
