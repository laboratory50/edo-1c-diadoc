FROM debian:trixie

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-django \
    python3-lxml \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=edo_converter.settings

EXPOSE 8000

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]
