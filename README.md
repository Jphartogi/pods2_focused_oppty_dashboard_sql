# H2 2026 Command Center - PODS 2 (SQLite Version)

Deal Execution Tracker & Strategy Dashboard for the PODS 2 H2 2026 Strategic Playbook.
Flask + SQLite backend, single-file frontend (Tailwind + vanilla JS), Google Cloud
Platform–style UI with a light/dark theme, an interactive analytics workspace, per-Account-Manager
row-level access control, and PDF report export.

## 1. Strategic Context

- **Target:** IDR 163.0B portfolio valuation for H2 2026 (editable by admin in Settings)
- **Current tracked pipeline:** IDR 54.89B across 31 opportunities
- **Execution Squads:** Volume Squad, Tender Squad, Strategic Squad
- **Strategic Pillars:** IoT Connectivity, Device Bundling, CCTV & Vision Analytics, Enterprise Solutions, Digital Reward
- **Account Managers:** Anisa Rahmy, Arie Prabowo, Ashari, Dimas

## 2. Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

App runs at `http://localhost:5000`. A `db.sqlite3` file is created and seeded automatically on
first run (users, config, and the 31 opportunities). Set `PORT` to change the port.

## 3. Accounts

| Username  | Password    | Role            | Access                                              |
|-----------|-------------|-----------------|-----------------------------------------------------|
| `admin`   | `admin123`  | admin           | Full access: Tracker, Analytics, Settings; edits all |
| `anisa`   | `anisa123`  | account_manager | Edits only opportunities assigned to **Anisa Rahmy** |
| `arie`    | `arie123`   | account_manager | Edits only opportunities assigned to **Arie Prabowo**|
| `ashari`  | `ashari123` | account_manager | Edits only opportunities assigned to **Ashari**      |
| `dimas`   | `dimas123`  | account_manager | Edits only opportunities assigned to **Dimas**       |
| `exec`    | `exec123`   | management      | View-only across Tracker and Analytics               |

> Change these passwords in any non-demo deployment via Settings → User Management.

## 4. Role-Based & Row-Level Access Control

- **admin** — full CRUD on all opportunities, users, and settings.
- **account_manager** — can view **all** opportunities but can only **create/edit/delete/update**
  the ones assigned to their own name. The UI shows a 🔒 lock on opportunities owned by other AMs,
  and the server independently rejects cross-AM edits with `403`. New opportunities an AM creates
  are automatically assigned to them (they cannot assign to someone else).
- **management** — read-only; no Settings tab, no edit controls.

Enforced both in the UI and server-side (`can_edit_deal()` in `app.py`).

## 5. Feature Highlights

- **Theme** — light/dark toggle in the top app bar (persists in `localStorage`, follows the OS
  preference on first load).
- **GCP-style design** — light top app bar, left nav rail, Material-inspired cards/elevation,
  Google brand colors, Roboto/Google Sans typography.
- **Full-year coverage header** — Full-Year 2026 Target, Achieved (YTD), 2026 Pipeline + Recurring,
  and Remaining Gap, plus a stacked **coverage bar** (Achieved / Recurring / 2026 Pipeline / Gap) so
  you can see how much of the full-year target is already covered and what's left to close.
- **Tracker** — search, filter by AM / Squad / Pillar / Stage, **sort** (TCV, Rev 2026, progress,
  name), and **pagination** (10/25/50 rows per page). Inline progress sliders, blocker flags, and
  next-action checklists. **Double-click any row** to open a full opportunity detail drawer.
- **Strategy per opportunity** — every deal has a free-text **Strategy** ("how you'll win & close"),
  editable by the owning AM. It shows in the detail drawer and drives the next-action plan, and is
  summarized for management in a **Strategy Playbook** card on the Analytics tab (grouped by AM,
  respecting the analytics filters).
- **Achievement & recurring** — in Settings, admins enter Achieved-YTD and expected recurring revenue.
  The target stays the full-year 2026 goal; the dashboard then shows the true remaining gap
  (Target − Achieved − Recurring − 2026 Pipeline).
- **Thousand separators** — all large IDR inputs (target, achievement, recurring, per-AM targets, TCV,
  Rev 2026) format as you type: `163000000000` → `163.000.000.000`, so you never miscount a zero.
- **Calendar** — every next action can carry a target date; the Calendar tab shows them in a month
  grid (overdue red, upcoming blue, done green) plus an overdue/upcoming list. Admin and management
  see everyone with an AM filter; an **Account Manager only ever sees their own** action plan.
- **Configuration tab** (admin) — manage the **Deal Stages**, Strategic Pillars and Squads lists.
  Stages are fully configurable: add/rename/delete, and every dropdown, filter and chart follows.
  Deleting a value that is still in use asks for confirmation and never rewrites existing deals.
- **Pipeline vs Account Manager Gap** — per AM: `Gap = Target − YTD actual − FY26 recurring (no
  churn) − 2026 pipeline`, with a stacked coverage bar so you instantly see who is short. Enter each
  AM's Target / YTD / Recurring under Settings → Account Manager Targets.
- **Strategy Coverage** — replaces the old wall-of-text playbook: per-AM coverage bars, a call-out
  listing opportunities that still have no strategy, and one collapsed line per documented deal that
  expands to read the full strategy.
- **Backup & restore (XLSX)** — admin-only, in Settings → Data Backup. Export everything
  (opportunities, strategies, next actions with dates, the 8-proof framework, config, users) to one
  Excel workbook; the same file is the import template for restoring or migrating to another host.
- **Execution Framework — the 8 Enterprise Proofs.** Every opportunity has an *Execution Framework*
  tab in its edit modal implementing the PODS 2 standard: **1 Qualification, 2 Engagement, 3 Concept,
  4 Value, 5 Contract, 6 Delivery, 7 Operation, 8 CLM**. Each proof carries a status
  (Not started / In progress / Done / N/A), a target date, and a notes/evidence line, so the AM's
  strategy turns into a structured, auditable execution plan instead of a loose to-do list.
  Proof target dates flow into the **Calendar**; N/A proofs are excluded from completion maths.
  Any pre-existing next actions are preserved under "Other next actions".
- **Framework analytics** — Analytics shows a proof-by-proof funnel (done / in progress / not
  started across the filtered deals), completion by Account Manager, and a click-to-drill list of the
  deals stuck at any given proof. The PDF report includes the same breakdown.
- **Account Manager focus** — when an AM signs in, the Tracker is pre-filtered to their own
  opportunities (clearly flagged, and they can widen it to the whole team at any time).
- **Management View** (admin + management only) — a simple executive briefing that management lands
  on by default: financial summary (target, achieved, recurring, pipeline, gap, framework health),
  blockers needing escalation with owners, action points due in the next 30 days plus overdue, and
  each deal's closing strategy with framework progress. Click or double-click anything to open the
  full opportunity detail.
- **Rev 2026 column** — every opportunity carries a `revenue_2026` value: the revenue realizable in
  the remaining H2 2026 (vs. the full multi-year TCV). This is the number that counts toward the
  2026 result and is editable per deal. Seeded equal to TCV; refine per deal in the edit modal.
- **Analytics** — 7 KPIs (incl. 2026 Rev) plus charts for pipeline by AM, pillar, squad, target
  quarter, stage distribution (donut) and top-8 opportunities, an AM leaderboard, and a management
  summary. A **filter bar** (AM / Pillar / Squad / Stage / Quarter) scopes the whole tab, and
  **clicking any chart bar/segment drills down** into the same filters.
- **AM target vs pipeline** — admins set a per-AM 2026 revenue target in Settings; the Analytics tab
  shows each AM's attainment (2026 revenue ÷ target) with a color-coded progress bar, gap, and TCV
  pipeline, plus a combined-team roll-up. Quickly spots which AMs are on/behind target.
- **PDF export** — professional multi-section report (ReportLab) including 2026 revenue, an AM
  target-attainment table, and per-opportunity detail, downloaded as `deal_tracker_report_<date>.pdf`.

## 6. API Reference

**Auth** — `POST /api/login` → `{token, role, username, full_name}`, `POST /api/logout`
**Account managers** — `GET /api/account_managers` (any authenticated user)
**Deals** — `GET /api/deals?am=&squad=&pillar=&stage=&quarter=`, `POST /api/deals`,
`PUT /api/deals/<id>`, `DELETE /api/deals/<id>`, `PUT /api/deals/<id>/progress`,
`PUT /api/deals/<id>/blocker` (mutations require admin or the owning AM)
**Users** (admin) — `GET/POST /api/users`, `PUT/DELETE /api/users/<id>`
**Config** — `GET /api/config` (all), `PUT /api/config` (admin). Config includes `target_amount`,
`strategic_pillars`, `squads`, and `am_targets` (a map of AM full-name → 2026 revenue target).
Deals carry `estimated_value` (TCV) and `revenue_2026`.
**Reports** — `GET /api/export/pdf`

All endpoints except `/api/login` require an `Authorization: Bearer <token>` header.

## 7. Deployment (make it accessible to your whole team)

Deploy **this** (SQLite) version for a team — it keeps one shared database on the server so
everyone sees and edits the same data. (The `deal_tracker_no_sql_pro` edition stores data in each
person's own browser and cannot be shared.)

**Before you deploy — do these two things:**
1. **Change the demo passwords.** After first login as `admin`, go to Settings → User Management and
   reset every account. The app ships with publicly known credentials.
2. **Run a single worker.** Auth tokens are held in memory, so the included `Procfile`, `Dockerfile`,
   and `render.yaml` all use `--workers 1`. Don't raise this, or users will get random logouts.

### Option A — PythonAnywhere (recommended: free *and* keeps your data)
Best free choice for a small team: no credit card, and the SQLite file persists.
1. Create a free "Beginner" account at pythonanywhere.com.
2. Open a **Bash console** and get the code onto the server, e.g.
   `git clone <your-repo-url>` (push this folder to GitHub first) — or upload a zip via the **Files** tab.
3. Install dependencies: `pip install --user Flask reportlab gunicorn`
4. **Web** tab → *Add a new web app* → *Manual configuration* → *Python 3.10+*.
5. Edit the WSGI file it created (link on the Web tab) so it points at this app:
   ```python
   import sys
   path = "/home/<youruser>/deal_tracker_sqlite_pro"   # folder containing app.py
   if path not in sys.path:
       sys.path.insert(0, path)
   from app import app as application                    # app.py exposes `app`
   ```
6. Click **Reload**. Your team visits `https://<youruser>.pythonanywhere.com` and logs in.
   `db.sqlite3` is created next to `app.py` on first load and persists across reloads.
   *(Free accounts click a "run for 3 more months" button occasionally to stay active.)*

### Option B — Render (easiest Git deploy; free tier does NOT keep data)
1. Push this folder to GitHub, then on render.com create a **New → Web Service** from the repo.
2. Build: `pip install -r requirements.txt` — Start: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1`.
3. You get a free `https://…onrender.com` URL with HTTPS.
   ⚠️ **Free-tier caveat:** the disk is ephemeral, so `db.sqlite3` is wiped on every restart/redeploy,
   and the service sleeps after ~15 min idle (first request then takes ~50s). To keep data on Render
   you need a **paid** plan + persistent disk (see `render.yaml`), or switch storage to a free managed
   Postgres (e.g. Neon/Supabase) — that requires code changes. For free + durable, use Option A.

### Option C — Docker (any host / your own server)
```bash
docker build -t deal-tracker-pods2 .
docker run -p 8000:8000 -v "$PWD/data:/app/data" -e DB_PATH=/app/data/db.sqlite3 deal-tracker-pods2
```
The `-v` volume + `DB_PATH` keep the database on the host so it survives container restarts.

### Option D — Heroku / Railway / any Procfile host
`git push heroku main` — uses `Procfile`, `runtime.txt`, `requirements.txt`. Note these platforms
also have ephemeral filesystems; attach a managed database or volume for durable storage.

## 8. Updating a running deployment (without losing data)

New columns are added **non-destructively**: on startup `migrate_db()` runs `ALTER TABLE ADD COLUMN`
only for columns that don't yet exist, so your existing `db.sqlite3` keeps all its rows. To update a
live PythonAnywhere instance:

1. Replace `app.py` and `templates/index.html` with the new versions (git pull in a Bash console, or
   re-upload via the **Files** tab). **Do not delete `db.sqlite3`.**
2. **If this update adds a new library, install it first.** The XLSX backup feature needs `openpyxl`:
   ```bash
   pip3.10 install --user openpyxl        # use the pip matching your web app's Python version
   ```
   (Everything else keeps working without it; only Export/Import will report that it's missing.)
3. Go to the **Web** tab and click **Reload**. On reload the app auto-migrates the database — it adds
   any missing columns (`deals.strategy`, `deals.proofs`, `config.current_achievement`,
   `config.recurring_revenue`, `config.stages`, `config.am_achievements`, `config.am_recurring`) and
   preserves every existing deal, user, password and setting.
4. Recommended right after reloading: **Settings → Data Backup → Export all data** so you have a
   restore point, then fill in the per-AM Target / YTD / Recurring figures.

## 9. Notes

- Session tokens are held in-memory (`TOKENS` in `app.py`); a server restart requires users to log
  in again. Passwords are hashed with PBKDF2 (`werkzeug.security`).
- Charts are lightweight inline SVG — no chart-library dependency beyond the Tailwind/FontAwesome CDNs.
# pods2_focused_oppty_dashboard
# pods2_focused_oppty_dashboard_sql
# pods2_focused_oppty_dashboard_sql
