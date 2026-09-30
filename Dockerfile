FROM python:3.12-slim

WORKDIR /app

# curl is used by the Compose healthcheck to probe /healthz from inside the container.
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/uploads

ENV PYTHONUNBUFFERED=1

# v2.0: sessions live in Postgres (see the `sessions` table in app.py), not an
# in-process dict, so multiple workers is safe - unlike v1 which was pinned
# to a single worker for exactly that reason.
EXPOSE 8000
CMD ["gunicorn", "app:app", "-w", "3", "-b", "0.0.0.0:8000", "--access-logfile", "-"]
