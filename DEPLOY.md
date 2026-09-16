# Deploying v2.0 (Docker Compose + Postgres)

This branch (`v2.0`) replaces the SQLite file + single gunicorn worker setup
with a 4-container Docker Compose stack: Postgres, the Flask app (multiple
gunicorn workers, since sessions now live in Postgres instead of an
in-process dict), Nginx, and an `autoheal` sidecar that restarts any
container Docker's own healthcheck reports unhealthy.

## First-time setup

1. Copy the env template and fill in a real Postgres password:
   ```bash
   cp .env.example .env
   ```

2. Build and start everything:
   ```bash
   docker compose up -d --build
   ```
   `docker compose ps` should show all four containers as `healthy` within
   about 30 seconds. This also creates the schema and seeds placeholder
   admin/AM users + example deals (same as a brand-new v1 install).

3. **If you're migrating real data from the old SQLite-based deployment**,
   copy the old `db.sqlite3` in and run the one-time migration - see
   "Migrating from v1" below. If this is a genuinely fresh install, skip to
   step 4.

4. Visit `http://<server-ip>/` - you should see the login screen. Default
   seeded logins (change these immediately if you didn't migrate real data):
   `admin` / `admin123`, plus the seeded AM accounts in `app.py`'s
   `SEED_AMS`.

## Migrating from v1 (SQLite)

Do this once, right after step 2 above, before real users touch the app:

```bash
# Copy the old database into the running app container
docker compose cp /path/to/db.sqlite3 app:/tmp/old.sqlite3

# Run the migration (prompts for confirmation since it will replace the
# placeholder seed data created in step 2)
docker compose exec -e DATABASE_URL="postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@db:5432/$POSTGRES_DB" \
  app python3 migrate_from_sqlite.py /tmp/old.sqlite3 "$DATABASE_URL"
```

Always test this against a **copy** of the real `db.sqlite3` first, never
the live file, until you've confirmed the row counts and a login work.

## Day-to-day operations

```bash
docker compose ps                 # health status of all 4 containers
docker compose logs -f app        # tail the app's logs
docker compose restart app        # manual restart of just the app
docker compose down               # stop everything (data persists in volumes)
docker compose down -v            # stop AND wipe Postgres/uploads data - careful
```

Uploaded documents live in the `uploads` named volume and Postgres data in
the `pgdata` named volume - both survive `docker compose down` / rebuilds,
and are only destroyed by an explicit `docker compose down -v`.

## What the healthcheck/auto-restart actually does

- Each service has a `healthcheck:` (Postgres: `pg_isready`; the app:
  `GET /healthz`, which actually checks it can reach Postgres, not just that
  the process is up; Nginx: a plain HTTP probe).
- Docker's own `restart: unless-stopped` handles the simple case (a
  container process crashes and exits) automatically.
- `autoheal` handles the harder case: a container whose process is still
  running but has gone unresponsive (fails its healthcheck without
  exiting) - it force-restarts anything labeled `autoheal=true` that Docker
  reports as `unhealthy`.

This was verified end-to-end during development: killing the app's process
outright triggers Docker's own restart; stopping Postgres out from under a
running app causes `/healthz` to fail, Docker marks the app container
unhealthy, and `autoheal` restarts it (repeatedly, until Postgres comes back
- at which point everything stabilizes on its own).

## Not yet done in v2.0

- Document uploads (PDF/PPTX) to the `uploads` volume - the `documents`
  table exists in the schema, but the upload/download endpoints and the UI
  in the opportunity detail drawer aren't wired up yet.
- Frontend chart/table modernization (Chart.js, Tabulator.js) - still the
  original hand-rolled SVG charts and `<table>` markup from v1.
