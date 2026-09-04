# H2 2026 Command Center - PODS 2 (SQLite Version)

Deal Execution Tracker & Strategy Dashboard for the PODS 2 H2 2026 Strategic Playbook.
Flask + SQLite backend, single-file frontend (Tailwind + vanilla JS), Google Cloud
Platform–style UI with a light/dark theme, an interactive analytics workspace, per-Account-Manager
row-level access control, and PDF report export.

## 1. Strategic Context

- **Target:** IDR 163.0B portfolio valuation for H2 2026 (editable by admin in Settings)
- **Current tracked pipeline:** IDR 54.89B across 31 opportunities
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

No `solution` / `project` / `product` accounts are seeded — create them from Settings → User
Management → Add User when you're ready to bring those teams on.

## 4. Role-Based & Row-Level Access Control

- **admin** — full CRUD on all opportunities, users, and settings.
- **account_manager** — can view **all** opportunities but can only **create/edit/delete/update**
  the ones assigned to their own name. The UI shows a 🔒 lock on opportunities owned by other AMs,
  and the server independently rejects cross-AM edits with `403`. New opportunities an AM creates
  are automatically assigned to them (they cannot assign to someone else).
- **management** — read-only; no Settings tab, no edit controls.
- **solution / project / product** — cross-functional roles that bridge Sales with delivery. They
  can browse the **Tracker** read-only (same full pipeline data everyone else sees — every
  opportunity, customer, AM, TCV, stage) for context, plus their own **My Team Tasks** inbox (every
  task assigned to their team, across every opportunity). From either place they can open an
  opportunity's **Team Tasks** panel to file a new follow-up under their own team, and update the
  **status** and **note** on their own team's tasks — nothing else. They can't edit any opportunity
  field (TCV, stage, the execution framework, etc.), reassign a task to a different team, or touch
  another team's tasks, and have no access to Calendar, Analytics, or Performance; both the nav and
  the API independently enforce this.

Enforced both in the UI and server-side (`can_edit_deal()` in `app.py`).

## 5. Feature Highlights

- **Theme** — light/dark toggle in the top app bar (persists in `localStorage`, follows the OS
  preference on first load).
- **AWS-inspired design** — a fixed dark-navy top app bar (stays dark in both light and dark theme,
  like aws.amazon.com), left nav rail, card-based layout, an AWS Cloudscape-style blue accent
  (no orange), and Inter/Amazon Ember-style typography. The sign-in page matches: it's built from the
  same theme tokens as the rest of the app (so it follows your light/dark preference too) with a
  fixed dark-navy brand panel on the right, the same as the app's header.
- **Feature search (Ctrl/Cmd+K)** — click the search bar in the top app bar (or press **Ctrl+K** /
  **Cmd+K**) to open a command palette that searches every section of the dashboard (Tracker,
  Calendar, Pipeline Analytics, Performance, Login Logs, Settings, etc.) plus a few quick actions
  (Add Opportunity, Export PDF, Toggle theme). Type to filter, use the arrow keys + Enter, or click
  a result to jump straight there. Only shows what your role can access.
- **Full-year coverage header** — Full-Year 2026 Target, Achieved (YTD), 2026 Pipeline + Recurring,
  and Remaining Gap as icon-badged metric cards, plus a stacked **coverage bar** (Achieved /
  Recurring / 2026 Pipeline / Gap) with pill-style legend chips, so you can see how much of the
  full-year target is already covered and what's left to close.
- **Tracker** — search, filter by AM / Pillar / Stage, **sort** (defaults to Progress
  High → Low, so opportunities closest to 100% surface first; also TCV, Rev 2026, name), and
  **pagination** (10/25/50 rows per page). Inline progress sliders, blocker flags, and
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
- **Calendar** — shows every scheduled item: every evidence entry logged against any of the 8
  Enterprise Proofs (whatever stage it's in — planned, in progress or done) plus every ad-hoc next
  action. Toggles between **Week** (default) and **Month** view. Multi-day entries (see Execution
  Framework below) render on every day they span. Item labels show only the AM's own wording — no
  "Proof of X" prefix. The KPI tiles (Scheduled / Overdue / In Progress / Done / No date) are
  **clickable filters** — click one to narrow the grid and list to that category, click again to
  clear it. Clicking an item opens a small detail popup for just that item (text, status, dates,
  which opportunity it belongs to) with a **View opportunity** button, rather than jumping straight
  into the full opportunity. Admin and management see everyone with an AM filter; an **Account
  Manager only ever sees their own** action plan.
- **Configuration tab** (admin) — manage the **Deal Stages** and **Strategic Pillars** lists.
  Stages are fully configurable: add/rename/delete, and every dropdown, filter and chart follows.
  Deleting a value that is still in use asks for confirmation and never rewrites existing deals.
  (The Squad feature is hidden for now — the underlying data isn't deleted, so it can come back later.)
- **Pipeline vs Account Manager Gap** — per AM: `Gap = Target − YTD actual − FY26 recurring (no
  churn) − 2026 pipeline`, with a stacked coverage bar so you instantly see who is short. Enter each
  AM's Target / YTD / Recurring under Settings → Account Manager Targets, or use the **Import
  Target/Actual/Recurring** button (admin only) right on this Gap & Targets sub-tab to bulk-update
  them from the same monthly "PODS (2)" performance workbook already used for Performance import —
  only account managers matched by name in the file are changed, everyone else's figures are left
  untouched, and any unmatched names are reported back so nothing is silently skipped.
- **Strategy Coverage** — replaces the old wall-of-text playbook: per-AM coverage bars, a call-out
  listing opportunities that still have no strategy, and one collapsed line per documented deal that
  expands to read the full strategy.
- **Backup & restore (XLSX)** — admin-only, in Settings → Data Backup. Export everything
  (opportunities, strategies, next actions with dates, the 8-proof framework, config, users) to one
  Excel workbook; the same file is the import template for restoring or migrating to another host.
- **Execution Framework — the 8 Enterprise Proofs.** Every opportunity has a wider *Execution
  Framework* tab in its edit modal implementing the PODS 2 standard: **1 Qualification, 2 Engagement,
  3 Concept, 4 Value, 5 Contract, 6 Delivery, 7 Operation, 8 CLM**. Each proof carries an overall
  status (Not started / In progress / Done / N/A), a target date, and **an unlimited list of evidence
  entries** — each with its own **status** (Not started / Planned / In progress / Done, clickable
  directly on the entry) and its own **start date and optional end date**. Leaving the end date blank
  means a single-day activity; setting it schedules a multi-day activity that shows on every day it
  spans on the Calendar. This is how an AM records everything they have done — or plan to do — to
  fulfil that proof, building a real audit trail rather than a single note. Existing entries without
  their own status/dates inherit sensible defaults automatically, so nothing already recorded needs
  to be re-entered. N/A proofs are excluded from completion maths.
- **Autosave + unsaved-changes warning.** While editing an existing opportunity, any change on the
  Opportunity Details, Execution Framework, or Action Plan tabs (Team Tasks excepted — those already
  save immediately per-task) is auto-saved to the server about 1.5 seconds after you stop typing, with
  a small status label next to the Save button ("Unsaved changes" → "Saving…" → "All changes saved").
  If you close or cancel the modal in that short window before autosave catches up (or a new,
  not-yet-created opportunity, which can't autosave until it exists), you get a confirmation prompt
  first so nothing typed is silently lost. The **Save** button still works as before and closes the
  modal immediately.
- **Action Plan tab** — a third tab in the opportunity edit modal, alongside Opportunity Details and
  Execution Framework. It auto-collects every evidence entry across the 8 Enterprise Proofs that's
  currently marked **Planned** — the team's to-do list for that opportunity — with its own status
  selector so you can bump a step to In progress/Done right there (it disappears from this list the
  moment it's no longer Planned). Below it, **Next actions** (ad-hoc items that don't belong to a
  specific proof) now lives in its own tab too, instead of being tucked away in a collapsible on the
  Execution Framework tab.
- **Stage — manual** — an opportunity's Stage is set directly by the AM/admin in its edit form.
  (Earlier builds could auto-derive it from execution-framework progress; that automation has been
  removed so the team controls Stage explicitly.)
- **Team Tasks — the Sales ↔ Solution/Project/Product bridge.** A fourth tab in the opportunity edit
  modal where anyone who can touch it — Sales (AM/admin), or Solution/Project/Product themselves —
  files a follow-up task, deciding its **status right away** (Not started / In progress / **Blocked**
  / **Needs discussion** / Done — not stuck defaulting to Not started), a required **"Assigned to"**
  name (who specifically this is for — not just which team), and an optional **target date** it needs
  to be resolved by. Every task shows a **From → To** pair of chips (e.g. "Sales · Administrator →
  Solution") plus a name chip for who it's assigned to, so it's always clear who filed it, which team
  it's assigned to, and who specifically owns it: Sales-filed tasks always show "Sales · <filer's
  name>" as the source; when Solution/Project/Product file their own follow-up, the source chip shows
  their own team and name instead. The "Assigned to" name can be edited later the same way the note
  can, and is required on every create/edit — the API rejects a task or update with it blank. Sales
  sees the full opportunity and can assign a task to any of the three teams, reassign or delete any
  task, and edit anything else on the deal as usual. A cross-functional user
  instead gets a stripped-down version of the same modal (title "Team Tasks", no other tabs, no Save
  button — just a read-only summary of the opportunity for context): they can only file tasks under
  their *own* team and can only edit/delete their own team's tasks; every other team's tasks on that
  opportunity show up locked (status, note and date disabled, no delete). Every change saves
  immediately (not tied to a Save button), so it stays in sync in real time. Each cross-functional
  team also gets its own **My Team Tasks** inbox — a focused worklist with no FY target/gap/coverage
  noise — listing every task assigned to them across *all* opportunities, sorted by **closest target
  date first** (done tasks sink to the bottom); tick a task done, change its status, edit the note, or
  adjust the date, right there. Admin and management get a separate **Weekly Meeting** board with the
  same closest-date-first sorting — every Blocked/Needs-discussion item across the whole portfolio in
  one place, filterable by team and status, built specifically to run the weekly cross-team sync and
  see what's most urgent to resolve. Unlike My Team Tasks, Weekly Meeting is visible to **every role**
  (Sales and admin/management included, not just Solution/Project/Product) so everyone can see the
  same picture ahead of the meeting; unlike My Team Tasks it's editable there too (see next), but only
  the checklist state, not the task itself. Like My Team Tasks, it hides the FY target/gap/coverage
  strip too — both are focused worklists.
- **Weekly Meeting threads** — the board groups every task by **opportunity** instead of listing them
  flat, so everything Solution/Project/Product/Sales flagged on the same deal reads as one discussion
  thread (with an "N open" count on the thread header) instead of scattered rows you have to piece
  together during the sync. Each task inside a thread has its own **status dropdown and note field
  right there** — closing it as **Done**, flipping it to **Needs discussion**, or leaving a note as you
  talk through it — no need to open the opportunity to update the checklist. Editability follows the
  same ownership rule as Team Tasks (a cross-functional team can only touch its own tasks, an AM only
  their own deals, admin everything); **management** can also change status/note on any task from this
  view specifically so they can run the review and mark items resolved, without gaining edit rights
  over the opportunity itself. **Admin and management** additionally get two one-click buttons on every
  task — **"Mark solved"** and **"Needs further discussion"** — that set its status directly to `done`
  or `needs_discussion` without touching the dropdown, so it's a single click to categorize a weekly
  item as resolved or still open. Each button disables itself once the task is already in that state.
- **Get Weekly Summary** — a button on the Weekly Meeting tab that pulls together, condensed by
  opportunity, what **happened in the last 7 days** and what's **planned for the next 7 days** across
  the whole portfolio: team tasks (done ones by their last-updated date, not-yet-done ones by their
  target date), Timeline Items, and dated Execution Framework evidence entries. Two columns — **Done
  (last 7 days)** and **Planned (next 7 days)** — grouped one card per opportunity with a bullet per
  item (date, text, and source — which team task, Timeline Item, or which of the 8 Enterprise Proofs it
  came from) so the meeting can scan a handful of opportunity cards instead of a long flat list.
- **Action Plan timeline** — in the same Action Plan tab, Sales can set two **milestones** per
  opportunity: the **expected PO date** and the **expected revenue booking date**. A **vertical**
  timeline right below plots those milestones together with every dated **Timeline Item** (see next),
  sorted chronologically from **today** through to the end of the project, so you can see at a glance
  what's coming up and in what order. It updates live as you edit either milestone date or a Timeline
  Item's date.
- **Timeline Items** — the deal's own independent, directly-edited dated plan: add a line of text, a
  start date, an optional end date, and a status (Not started / Planned / In progress / Done).
  Deliberately **not derived from** the Execution Framework's Planned execution steps (which still
  shows underneath, unchanged, for reference) — Timeline Items exist so you can jot down what you have
  in mind for this opportunity without tying it to a specific one of the 8 Enterprise Proofs. This
  replaces the old "Next actions" checklist, which the Timeline (fed directly by these items) and the
  Planned execution steps list together already covered.
- **Framework analytics** — Analytics shows a proof-by-proof funnel (done / in progress / not
  started across the filtered deals), completion by Account Manager, and a click-to-drill list of the
  deals stuck at any given proof. The PDF report includes the same breakdown.
- **Target PO Closed Date per AM** — on the Leaderboard & Summary analytics tab, a card lists each
  Account Manager's nearest upcoming **expected PO date** across their opportunities (or "No PO target
  date set" if none has one), plus how many of their deals are missing it. A second card lists every
  opportunity in the current filter that's missing its **expected PO date** and/or **expected revenue
  collected date**, so management can chase the gaps before the weekly review instead of discovering
  them deal-by-deal.
- **Account Manager focus** — when an AM signs in, the Tracker is pre-filtered to their own
  opportunities (clearly flagged, and they can widen it to the whole team at any time).
- **Management View** (admin + management only) — a simple executive briefing that management lands
  on by default. A **"Needs your attention"** headline states whether anything is wrong, then three
  widgets: **Blockers** and **Action points** (collapsed, one-line summary until expanded), and
  **Account Manager performance** (open by default) — a per-AM card showing Target vs Covered
  (Achieved + Recurring + 2026 Pipeline, the same formula as the Analytics Gap section), an
  attainment bar, and a warning badge (On target / Behind target / Significantly behind) so you can
  see at a glance who isn't covering their number. Beneath it, an **Insight** panel explains *why*:
  for every AM short of target it checks whether they have blocked deals and calls that out as a
  likely contributor, or — if there are no blockers on file — says the gap more likely needs pipeline
  generation than escalation. Click or double-click anything to open the full opportunity detail.
- **Performance tab** — upload the monthly **PODS 2 - ACH** workbook from the performance team
  (admin only) and the dashboard reads the `PODS (2)` and `byAccount (BP)` sheets to show:
  team scorecard (Target FY, Actual YTD, MRC, PO on Hand, Forecast, Gap, attainment);
  **pipeline cover** against the conservative 3× rule per AM; monthly target vs actual/forecast;
  **MRC run-rate with next-quarter and full-year projection** (no-churn assumption);
  **churn watch** and **growing accounts** compared to the previous month or quarter; and
  **top revenue accounts cross-checked against pipeline in this dashboard** so you can see which
  big earners have no opportunity attached (upsell blind spots). The last 12 uploads are retained.
- **Performance PDF export** — *Export PDF* on the Performance tab downloads the current snapshot
  (optionally scoped to one AM) as a report: team scorecard, gap-to-target, pipeline cover, per-AM
  breakdown, churn watch and growing accounts (vs previous month), and revenue by product pillar —
  the gap comes first since that's the number management needs immediately, saved as
  `performance_summary_<date>.pdf`.
- **Login Logs** (admin only) — every successful sign-in is recorded with a timestamp (Jakarta time,
  GMT+7), the user, their role and IP address, so an admin can see exactly when each Account Manager
  last used the dashboard.
  Only the most recent logs are kept — the limit defaults to **100** and is adjustable (10–2000) right
  on the Login Logs page — so storage never grows unbounded. Logs can be exported to Excel at any time
  (`login_logs_<date>.xlsx`). This page and its API are strictly admin-only; it does not appear in the
  sidebar for any other role.
- **Tracker sheet export** — on Analytics, *Export Tracker sheet* produces one row per activity in
  the exact column order of the shared **H2 2026 Sales Activity Tracker** (`No. / PODS / Opportunity
  Name / Customer / Account Manager / TCV / Rev 2026 / Target Quarter / Pillar / Activity / Status /
  Due Date / Completed Date / Notes`), ready to paste into the OneDrive **Tracker** sheet. Each proof's
  evidence entries become activity rows; add `?include_empty=1` to also emit not-yet-started proofs.
- **Rev 2026 column** — every opportunity carries a `revenue_2026` value: the revenue realizable in
  the remaining H2 2026 (vs. the full multi-year TCV). This is the number that counts toward the
  2026 result and is editable per deal. Seeded equal to TCV; refine per deal in the edit modal.
- **Analytics** — organized into five sub-tabs so each view stays focused: **1. Gap & Targets**
  (the default landing tab — Pipeline vs Account Manager Gap comes first, since that's what
  management needs to see immediately), **2. Pipeline Breakdown** (charts for pipeline by AM,
  pillar, target quarter, stage distribution and top-8 opportunities), **3. Execution
  Framework** (the 8-proof funnel and completion by AM), **4. Strategy** (Strategy Coverage), and
  **5. Leaderboard & Summary** (AM leaderboard + management summary). 7 KPI cards (incl. 2026 Rev)
  and the **filter bar** (AM / Pillar / Stage / Quarter) stay visible across every sub-tab,
  and **clicking any chart bar/segment drills down** into the same filters.
- **AM target vs pipeline** — admins set a per-AM 2026 revenue target in Settings; the Analytics tab
  shows each AM's attainment (2026 revenue ÷ target) with a color-coded progress bar, gap, and TCV
  pipeline, plus a combined-team roll-up. Quickly spots which AMs are on/behind target.
- **Metric strip shows your own numbers if you're an AM** — the Full-Year Target / Achieved (YTD) /
  2026 Pipeline + Recurring / Remaining Gap strip at the top of the Tracker shows an Account Manager
  their **own** target, achieved, recurring, and pipeline figures (and is labelled "Your FY 2026
  Target") whenever they have a target on file in Settings, so they can tell at a glance whether
  *they personally* are covered — rather than the whole team's number, which would hide whether their
  own book is on track. Admin, management, and every other role still see the whole-team Full-Year
  target as before.
- **PDF export** — professional multi-section report (ReportLab) including 2026 revenue, an AM
  target-attainment table, and per-opportunity detail, downloaded as `deal_tracker_report_<date>.pdf`.

## 6. API Reference

**Auth** — `POST /api/login` → `{token, role, username, full_name}`, `POST /api/logout`
**Account managers** — `GET /api/account_managers` (any authenticated user)
**Deals** — `GET /api/deals?am=&pillar=&stage=&quarter=`, `POST /api/deals`,
`PUT /api/deals/<id>`, `DELETE /api/deals/<id>`, `PUT /api/deals/<id>/progress`,
`PUT /api/deals/<id>/blocker` (mutations require admin or the owning AM)
**Users** (admin) — `GET/POST /api/users`, `PUT/DELETE /api/users/<id>`. Roles: `admin`,
`account_manager`, `management`, `solution`, `project`, `product`.
**Team Tasks** — `GET/POST /api/deals/<id>/tasks` (list: any authenticated role; create: admin/owning
AM choosing any team, or a cross-functional role creating only under its own team — the `team` field
is ignored and forced server-side for them; both must supply a non-blank `assigned_to` — who
specifically the task is for — and may set the starting `status` and an optional `due` date at
creation time; a request with `assigned_to` missing or blank is rejected with 400), `PUT/DELETE
/api/tasks/<id>` (cross-functional roles may edit/delete only their own team's tasks, and can change
`text`/`status`/`note`/`due`/`assigned_to` but never `team`; admin/owning AM can edit or delete any
field on any task on their deals; `management` may `PUT` `status`/`note` only, on any task — powers
the inline checklist editing and the one-click Mark Solved / Needs Discussion buttons on the Weekly
Meeting board — and cannot delete or change `text`/`team`/`due`/`assigned_to`; an `assigned_to` sent
as blank on a `PUT` that's allowed to change it is rejected with 400, same as on create),
`GET /api/tasks?team=&status=&scope=`
(cross-opportunity list, any authenticated role — by default a cross-functional role only ever sees
its own team's tasks; pass `scope=all` to see every team's tasks instead, which is what the shared
Weekly Meeting board uses so every role sees the same picture). Every task also carries a
`source_team` (`sales`, or one of `solution`/`project`/`product` when that team files its own
follow-up) alongside `team` (which team it's assigned to) and `assigned_to` (which individual it's
assigned to, by name) — `source_team`/`team` are set automatically at creation time from the
creator's role and never editable afterward; `assigned_to` is a free-text name entered by whoever
files or edits the task.
**Config** — `GET /api/config` (all), `PUT /api/config` (admin). Config includes `target_amount`,
`strategic_pillars`, and `am_targets` (a map of AM full-name → 2026 revenue target). It still
carries a `squads` field for backward compatibility with existing data — the Squad feature is
just hidden from the UI for now, not removed from the schema.
Deals carry `estimated_value` (TCV), `revenue_2026`, and the two Action Plan milestones
`expected_po_date` / `expected_revenue_date`. The `next_actions` field now holds **Timeline Items**
(`{text, date, end, status}` — `status` is one of `not_started`/`planned`/`in_progress`/`done`); a
legacy `{action, done, due}` entry from before this shape existed is migrated transparently on read
by the frontend (`normalizeTimelineItems()`), so nothing already saved is ever lost.
**Reports** — `GET /api/export/pdf`, `GET /api/performance/export_pdf?am=`
**Login Logs** (admin) — `GET /api/login_logs`, `GET /api/login_logs/export_xlsx`. Config's
`max_login_logs` (default 100, range 10–2000) controls how many of the most recent logs are kept.

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
   preserves every existing deal, user, password and setting. A proof's older single note is folded
   into its evidence list automatically. (`config.auto_stage`/`config.stage_rules` may still exist
   from older releases but are no longer read — Stage is manual only.) It also adds the new
   `deal_tasks` table, and — only if your `users` table predates the `solution`/`project`/`product`
   roles — rebuilds `users` to widen its role constraint, copying every existing user row across
   unchanged (usernames, password hashes, everything) rather than touching any data.
4. Recommended right after reloading: **Settings → Data Backup → Export all data** so you have a
   restore point, then fill in the per-AM Target / YTD / Recurring figures.

## 9. Notes

- Session tokens are held in-memory (`TOKENS` in `app.py`); a server restart requires users to log
  in again. Passwords are hashed with PBKDF2 (`werkzeug.security`).
- Charts are lightweight inline SVG — no chart-library dependency beyond the Tailwind/FontAwesome CDNs.
- Branding lives in `static/img/`: `pods2-logo.png` is the master file; `pods2-logo-256.png` is what
  the header and sign-in page actually load, and `favicon-16/32.png` + `apple-touch-icon.png` are the
  browser-tab/bookmark icons. Regenerate the smaller sizes from the master with Pillow if you ever
  swap the logo — see the resize snippet used when these were first generated (any 1:1 PNG works).
# pods2_focused_oppty_dashboard
# pods2_focused_oppty_dashboard_sql
# pods2_focused_oppty_dashboard_sql
