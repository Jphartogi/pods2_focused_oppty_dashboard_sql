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

## Keeping v2.0 up to date while v1.9 is still live

The initial migration above is one-time and destructive (it truncates first,
since it targets a brand-new database). While v1.9 keeps running as the live
system in parallel, use **Settings → Sync from v1.9** (admin only) instead -
enter v1.9's URL and an admin login there once, then click "Sync from v1.9"
whenever you want the latest data; no file to download or upload. It upserts
by id - refreshing anything that exists in both (v1.9's version wins) while
leaving alone anything created only in v2.0 - so it's safe to run as often as
needed right up to the final cutover, when v1.9 gets retired for good. This
needs v1.9 running 1.9.2 or later (adds the `GET /api/admin/export_db`
endpoint this pulls from).

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

## Document uploads

Attach PDF/PPTX/DOCX/XLSX/images to an opportunity from its detail drawer
("Attach file"). Files are saved to the `uploads` Docker volume (persists
across rebuilds) under `uploads/<deal_id>/`, with a `documents` table row
per file. Only admin or that opportunity's assigned AM can upload/delete;
anyone who can view the opportunity can download.

## HTTPS (Let's Encrypt)

Requires the domain's DNS to already point at this VM (`dig +short
pods2.jphartogi.com` should print the VM's IP) - Let's Encrypt verifies
ownership by reaching the domain over plain HTTP, so this won't work until
DNS has propagated.

1. Deploy the ACME-challenge-ready config (safe on its own, no SSL yet):
   ```bash
   git pull && docker compose up -d --build
   ```
2. In the GCP Console, open the VM's firewall rules (or Compute Engine ->
   VM instances -> edit the instance's network tags) and make sure a rule
   allows `tcp:443` from `0.0.0.0/0` - the same way `http-server` was added
   for port 80. The VM needs the `https-server` network tag, and a firewall
   rule targeting it for `tcp:443`.
3. Request the certificate (one-off). The `certbot` service's `entrypoint`
   is a permanent renewal-loop script, so a plain `docker compose run
   certbot certonly ...` gets its arguments silently swallowed by that loop
   instead - override `--entrypoint` on the command line to bypass it for
   this one request:
   ```bash
   docker compose run --rm --entrypoint "certbot certonly --webroot -w /var/www/certbot -d pods2.jphartogi.com --email you@example.com --agree-tos --no-eff-email" certbot
   ```
   This writes the certificate into the `certbot-conf` volume. If it fails,
   double-check DNS and that port 80 is actually reachable from the public
   internet first - Certbot's error message says exactly what it tried and
   what came back.
4. Pull the SSL-enabled nginx config (adds the `443 ssl` server block and
   redirects plain HTTP to HTTPS) and redeploy:
   ```bash
   git pull && docker compose up -d --build
   ```
5. Verify: `https://pods2.jphartogi.com` should load with a valid padlock,
   and `http://pods2.jphartogi.com` should redirect to it.

The `certbot` container then renews automatically (it wakes up every 12h and
calls `certbot renew`, which is a no-op until the cert is within 30 days of
expiring) - no further action needed after the initial request. Since the
renewed certificate lands in the same `certbot-conf` volume nginx already
reads from, nginx just needs a reload to pick it up - `docker compose exec
nginx nginx -s reload` (or restart the container) after a renewal.

## Not yet done in v2.0

- Account Coverage's and AM Workload's own account tables are still the
  original hand-rolled markup - only the Tracker table was moved to
  Tabulator.js so far.
