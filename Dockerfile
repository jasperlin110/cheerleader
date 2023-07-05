FROM python:3.11.4-slim-bullseye

ENV PYTHONUNBUFFERED 1

WORKDIR /app/cheerleader

COPY requirements.txt ./
RUN pip install -r requirements.txt --no-cache-dir
COPY . ./

RUN python3 manage.py makemigrations && python3 manage.py migrate

CMD ["gunicorn", "cheerleader.wsgi"]
EXPOSE 8000
