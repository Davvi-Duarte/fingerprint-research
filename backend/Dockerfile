FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p instance

EXPOSE 5000

# Init migrations if folder doesn't exist, then upgrade, then start
CMD ["sh", "-c", "\
  if [ ! -d migrations ]; then \
    flask db init && flask db migrate -m 'initial'; \
  fi && \
  flask db upgrade && \
  gunicorn --bind 0.0.0.0:5000 --workers 2 run:app"]
