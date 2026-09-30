# Changelog

All notable changes to the H2 2026 Command Center - PODS 2 are recorded here.
Versions follow [Semantic Versioning](https://semver.org/) (MAJOR.MINOR.PATCH):
MAJOR for breaking changes, MINOR for new backward-compatible features, PATCH
for fixes. The current version is shown in the app (bottom of the left nav,
and the sign-in screen) and via `GET /api/version`.

## [2.11.0] - 2026-09-30 (branch: v2.0)
### Added
- **Weekly Plan's "Goal of the visit" is now multiple points**, not one
  block of text - each goal is its own line with a remove button, and
  "+ Add point" adds another. Stored as newline-separated text (same
  convention already used for Next Actions elsewhere), rendered as a real
  bullet list wherever a plan is displayed.
- **Admin/management can double-click any planned visit to see its full
  details** - customer, topic, every goal point, and the attachment - in a
  read-only popup, from both the "All Account Managers" overview and a
  single AM's drilled-in view. No edit controls are shown; it's purely a
  detail view, since only the AM themselves can change their own plan.
### Changed
- The compact one-line preview of a visit (in the day cards and the All-AMs
  grouped summary) now joins goal points with " · " instead of showing raw
  newlines.

Verified in an ephemeral Docker stack: added a 4-point goal to a visit as an
AM, confirmed all 4 points saved and reloaded correctly; confirmed an admin
double-clicking that visit (both from the single-AM view and the grouped
All Account Managers view) opens a read-only detail modal showing every
goal point as a bullet, with no Save/Delete/upload controls present.

## [2.10.0] - 2026-09-30 (branch: v2.0)
### Added
- **"My Profile"**: click the avatar/name in the top bar (any role) to change
  your own username and/or password. Requires re-entering your current
  password to save any change; a username change is checked for a conflict
  the same way the admin's own user form already is. New `PUT /api/me`.
- **Notifications now have real read state and age out.** Clicking a
  notification marks it read (dims it, and it stops counting toward the bell
  badge) and persists that across reloads; any notification - read or not -
  is deleted outright once it's 14 days old, so overdue items don't pile up
  forever. New `notification_state` table and `POST /api/notifications/read`;
  `GET /api/notifications` now births, ages, and prunes this state on every
  call rather than only ever computing fresh.
### Changed
- **Weekly Plan's Customer field is now a searchable dropdown** (Choices.js,
  matching the Tracker's own filters) instead of a plain text box with a
  native datalist - offered customers are still that AM's own Tracker/
  Account Coverage accounts, plus a "+ Add new customer…" option that reveals
  a text field for a brand-new prospect.
- Renamed the "Weekly Meeting Prep" eyebrow on My Weekly Plan to "Visit
  Planning" - that wording belongs to the separate, existing Weekly Meeting
  tab and was confusing sitting on this page too.
- **Top bar search is noticeably longer**, extending to just before the
  icon cluster (Configuration/Settings/Notifications/Theme) instead of
  stopping well short of it with a large dead gap.

Verified in an ephemeral Docker stack: confirmed a wrong current password is
rejected and a correct one updates both username and password (re-verified
login with the new credentials); confirmed a notification dims and the badge
count drops immediately on click, persists after a reload, and is deleted
once its tracked age exceeds 14 days (simulated by backdating the row
directly); confirmed the Customer dropdown renders every option unclipped
and picking "+ Add new customer…" reveals the free-text field; confirmed the
widened search bar and no console errors across a full click-through.

## [2.9.0] - 2026-09-30 (branch: v2.0)
### Added
- **"My Weekly Plan"**: a new per-AM, per-week visit planner, replacing the
  Calendar tab. Each Account Manager plans Mon-Fri customer visits (customer,
  topic to bring, goal of the visit - matching the team's existing paper
  Commitment Plan template), reviewed live in the weekly meeting instead of
  screenshotted from a spreadsheet.
  - Customer is picked from that AM's own Tracker opportunities and Account
    Coverage list (a `<datalist>`, so it's quick to pick an existing account
    but still free text for a brand-new prospect).
  - Each planned visit can have one attached image or PDF (plan or proof of
    the visit), stored the same way opportunity documents already are.
  - Plans are saved per calendar week (`week_start` = that week's Monday) and
    per AM (`am_full_name`) - nothing is shared or overwritten between AMs or
    weeks, and the AM-rename tool in Settings now carries weekly plan entries
    along with everything else when a name is merged.
  - **Admin/management get a review view**: an "All Account Managers" mode
    shows every AM's week side-by-side (read-only), or a specific AM can be
    picked to see their plan exactly as they see it. An AM only ever sees and
    edits their own plan.
  - New endpoints: `GET/POST /api/weekly_plan`, `PUT/DELETE
    /api/weekly_plan/<id>`, `GET /api/weekly_plan/customers`,
    `POST/GET/DELETE /api/weekly_plan/<id>/attachment`. New `weekly_plans`
    table.
### Changed
- **The Tracker tab is now labeled "My Tracker"** and the Calendar tab has
  been removed (superseded by My Weekly Plan above) - the next-action items
  it showed are still visible in each opportunity's own timeline and in the
  Weekly Meeting prep tab, which never depended on the Calendar.
### Fixed
- **A real bug from the Calendar removal**: `loadDeals()` still referenced
  the now-gone `#tab-calendar` element after every Tracker filter change,
  which would have thrown on every single filter/search/sort action. Caught
  and removed before shipping.

Verified in an ephemeral Docker stack: created, edited, and deleted plan
entries as a real AM login (Anisa Rahmy), including attaching and removing a
PDF; confirmed the customer field only offers that AM's own accounts;
confirmed an admin login sees every AM's week in the grouped overview and
can drill into one AM read-only with no edit controls; confirmed every other
tab (Tracker, Analytics, Performance, Account Coverage, Management, Weekly
Meeting, My Team Tasks, Settings, Configuration, Login Logs) still switches
cleanly with zero console errors after the Calendar removal; confirmed light
and dark theme.

## [2.8.0] - 2026-09-30 (branch: v2.0)
### Fixed
- **Filter dropdowns (AM/Pillar/Stage) were rendering clipped to 1-2 visible
  rows, floating in the wrong place.** Root cause: `.card`'s CSS sets
  `contain: layout paint` for render performance, which also clips any
  content that overflows the card's own box - including the Choices.js
  dropdown panel, especially when it flips to open upward (common near the
  bottom of a typical viewport). All options were always present in the DOM
  and the underlying `<select>` - only the visible popup was cut off. Fixed
  by disabling containment specifically on the Tracker toolbar card so its
  dropdowns can overflow the card and render in full.
- **Account Manager filter only listed people with a registered login**,
  missing any AM who already has opportunities in the Tracker but hasn't
  been given a v2.0 account yet (e.g. after a v1.9 sync or bulk import).
  `GET /api/account_managers` now also includes every distinct name already
  assigned to a deal, unioned with registered `account_manager` users, so
  the filter covers everyone actually in the pipeline data.
### Changed
- **Top app bar redesigned**: the small "Search features" pill is now a
  long, full-width search bar (Google Cloud Console style) instead of a
  narrow fixed-width button.
- Removed the "IDR · Production" chip and the "H2 2026 Strategic Playbook"
  subtitle from the header; the app is now just labeled "Dashboard Tracker"
  throughout (browser tab title, sign-in screen, top bar) so this build can
  be replicated for other teams without PODS-2-specific wording baked in.
- **The logo in the top bar is now a home button** - click it from any page
  to jump straight back to the Tracker.

Verified in an ephemeral Docker stack: seeded a deal for an AM with no
registered v2.0 login ("Mutiara Rizky") alongside the 4 seeded registered
AMs, confirmed she was previously invisible in the filter and now appears
and filters correctly; confirmed the AM/Pillar dropdowns render every option
in full (no clipping) in both light and dark theme, at both a narrow
(800px) and a wide (1440px) viewport; confirmed the home button navigates
back to Tracker from another tab; confirmed a real AM login (Anisa Rahmy)
still gets auto-scoped to her own opportunities by default with no console
errors.

## [2.7.0] - 2026-09-30 (branch: v2.0)
### Changed
- **Tracker toolbar redesigned**: search is now full-width on its own row
  instead of squeezed alongside the filters, with Account Manager/Pillar/
  Stage/Sort on their own row below.
- **AM/Pillar/Stage/Sort filters now use Choices.js** instead of native
  `<select>` elements - a real styled dropdown panel (searchable, themed to
  match light/dark mode) instead of the browser's own unstyleable popup.
  Fully re-skinned to the app's existing design tokens; the "has a value"
  accent, AM-role default selection, and Clear button all carry over
  unchanged.
- **Revenue Overview hero card de-duplicated**: the legend row under the
  gauge repeated the exact same Achieved/Recurring/Pipeline/Gap numbers
  already shown in the tiles above it. Replaced with a new context row
  pulling genuinely different information from Pipeline Analytics and
  Account Coverage - opportunity count, average progress, accounts tracked,
  and engaged % - scoped to the same AM filter as the rest of the card.

Verified end-to-end: selecting an AM in the new Choices dropdown correctly
filters the Tracker table and re-scopes the hero card and its new context
row (confirmed via a real AM login, whose card correctly showed "Your FY
2026 Target," 100% covered, and her own opportunity/account counts); Clear,
light/dark theme, and every other tab (Analytics, Management, Calendar, Add
Opportunity modal) still work with no console errors.

## [2.6.0] - 2026-09-29 (branch: v2.0)
### Added
- **Merge Account Manager Name** (Settings, admin only): the 2.5.4 rename
  cascade only fires when you edit a user whose *own* full name is wrong -
  it didn't help when the user record already has the correct name but a
  deal, task, or coverage row still carries stale text from before that
  name was ever set (exactly this: "Dimas"/"Ashari" not appearing as users
  at all, only as leftover text elsewhere). This tool surfaces every name
  found in deals/tasks/coverage/config that doesn't match any registered
  user, with source and row-count context, and merges a chosen stray name
  into a real registered user's name in one action - independent of any
  user record, so it also covers this case.

Verified against the exact reported scenario: registered users already
correctly named "Dimas Aradzna Himawan Nugroho" / "Ashari Asrar", with
stray "Dimas"/"Ashari" text still sitting in a deal, an account_coverage
row and config's target figures. The mismatch list found both by name,
source and count; merging each cleared the mismatch list to empty and
correctly relabeled every affected row.

## [2.5.4] - 2026-09-29 (branch: v2.0)
### Added
- **Renaming a user now cascades everywhere their name is stored.** Two AMs
  (seeded long ago with short names, "Dimas"/"Ashari") had their real full
  names ("Dimas Aradzna Himawan Nugroho"/"Ashari Asrar") show up separately
  through the Master Account import, fragmenting one real person into two
  apparent identities across Account Coverage, deals, and targets. A
  person's full name is denormalized as plain text into a deal's
  `assigned_am`, a task's `assigned_to`, an `account_coverage` row's `am`,
  and the AM-keyed JSON figures in `config` (targets/achievements/
  recurring) rather than being a live reference - renaming the user via
  Settings -> User Management -> Edit now updates all of those too, so
  correcting a name re-merges everything under the one correct name instead
  of leaving the old name's data orphaned.

Verified: renamed a user with an assigned deal, a Tracker-derived coverage
row, a Master-imported coverage row for a different account, and a config
target keyed by the old name - all four updated to the new name in one
action, the renamed user's login and deal filtering still worked
afterward, and re-saving with an unchanged name is a safe no-op.

## [2.5.3] - 2026-09-29 (branch: v2.0)
### Fixed
- **Master Account import still left old cross-pod accounts behind** if the
  Performance workbook wasn't also re-uploaded - its cleanup only ever
  removed stale rows it created itself (`source='master'`), never stale
  rows left over from an earlier (pre-fix) Performance import
  (`source='performance'`). Since the Master file is described as "the
  authoritative account list," it now also prunes stale performance-sourced
  rows that aren't in it - a performance-only import stays narrowly scoped
  to its own source (it's just a monthly revenue snapshot, not a complete
  account registry, so it can't safely make that call), but the master list
  can. Tracker/manual rows - real local work - are still never touched by
  either.

Verified: seeded two cross-pod `source='performance'` rows plus one
legitimate `source='tracker'` row, ran only the Master import, and
confirmed both strays are removed while the Tracker-derived row survives
untouched.

## [2.5.2] - 2026-09-29 (branch: v2.0)
### Changed
- **Tracker page header restructured**: "Export PDF" and "Add Opportunity"
  moved out of the filter bar into a proper page header (an eyebrow label +
  "Tracker" title, with the two actions aligned top-right) - the filter bar
  below now only holds filtering/sorting controls (search, AM, Pillar,
  Stage, Sort, Clear) on their own row, instead of 8 mixed controls
  competing for space on one crowded line.

## [2.5.1] - 2026-09-29 (branch: v2.0)
### Fixed
- **Account Coverage kept showing stale/cross-pod data in the browser even
  after the 2.4.4/2.5.0 fixes were deployed and re-imported** - the server
  side cleanup was working correctly (re-verified against both real files),
  but the page only ever loads Account Coverage data once at login. Neither
  switching to the Coverage tab nor a Performance import's success handler
  re-fetched it afterward, so the browser kept rendering whatever was in
  memory from page load. Fixed: opening the Coverage tab now always
  re-fetches fresh data, and importing a Performance workbook refreshes
  Account Coverage the same way the Master Account import already did.
  Verified without a page reload: seeded a stray cross-pod row, ran the
  import, and confirmed it disappears from the in-memory list and the
  rendered chart immediately.

## [2.5.0] - 2026-09-29 (branch: v2.0)
### Fixed
- **Master Account import was silently corrupting revenue figures.** Its
  "Revenue Data" sheet repeats the same month-end dates three times across
  the row - the real monthly revenue block, then a "Same"/"OTC" status-flag
  block, then a numeric "movement/delta" block - separated only by blank
  columns. The parser scanned the whole row for anything date-like instead
  of stopping at the first gap, so it silently summed all three blocks
  together into each account's revenue figure (confirmed against a real
  file: one account's total was pulled down by a -80,000,000 delta value
  that had nothing to do with its actual revenue). Fixed by only taking the
  first contiguous run of dated columns; cross-checked against a manual sum
  of the real file for a sampled account and confirmed exact.
### Changed
- **Hero card visual upgrade**: the FY Target gauge card now has an eyebrow
  header ("Revenue Overview", plus an "As of <performance snapshot label>"
  note when available), a vertical divider between the gauge and the KPI
  tiles, and the tiles themselves are elevated white/dark cards with soft
  shadows and gradient icon badges instead of flat tinted panels - bigger,
  bolder numbers throughout. The same `.metric-tile` styling is shared by
  Management View's KPI band, so it picked up the same treatment
  automatically.

## [2.4.4] - 2026-09-29 (branch: v2.0)
### Fixed
- **Account Coverage was importing other pods' accounts and AMs.** The
  Performance workbook's "byAccount (BP)" sheet carries every Business
  Engine 1 pod's accounts (Head 1/2/3), not just PODS 2's (Head 2) - the
  Master Account import already filtered to Head 2 only, but the Performance
  import never did, so every monthly upload silently pulled in ~350 accounts
  and a dozen AM names belonging to other teams (confirmed against a real
  production workbook: 565 total rows, only 214 actually Head 2). Fixed by
  applying the same Head-2 filter used elsewhere.
### Added
- Both the Performance and Master Account imports now **remove stale rows
  no longer in the uploaded file** (scoped to rows they created themselves -
  `source='performance'` or `source='master'` respectively - never touching
  manually-added or Tracker-derived accounts), so re-uploading a corrected
  file cleans up anything wrongly imported before, instead of only ever
  adding/updating. This is what makes the fix above actually clean up
  already-polluted production data once re-run, without needing a manual
  delete option (imported rows intentionally can't be deleted by hand, to
  prevent accidental data loss - re-import is the sanctioned way to correct
  them).

Verified against the real "PODS 2 - Up to August 2026.xlsx": import now
reports 214 account rows (down from 565), only the 6 real PODS 2 AM names
appear anywhere in Account Coverage, and a manually-seeded stray row
mimicking the existing production pollution was correctly removed on
import.

## [2.4.3] - 2026-09-29 (branch: v2.0)
### Changed
- **Tracker filter bar polish, pre-launch pass**:
  - Native dropdown popups (Account Manager, Pillar, Stage, and every other
    `<select>` in the app) now render in the matching light/dark palette
    instead of a plain white list that looked jarring in dark mode - browsers
    do this automatically once told the page supports both via CSS
    `color-scheme`.
  - A filter that isn't at its default ("All ...", empty search) now gets a
    visible primary-colored highlight, so it's obvious at a glance which
    filters are actually narrowing the Tracker list.
- **Calendar's "Action plan list"**: removed as a permanent fixture - it was
  a plain-text duplicate of what the grid above it already shows. It still
  appears, retitled "Actions without a date", but only when the "No date
  set" KPI is selected, since those items are the one thing the grid
  genuinely can't display.

## [2.4.2] - 2026-09-29 (branch: v2.0)
### Fixed
- **Performance workbook import read every AM summary column one off from
  where it actually is** in the real "PODS (2)" template - `Target FY 2026`
  was read as `Actual YTD`, `Actual YTD` as `MRC`, `MRC` as `PO on Hand`, and
  so on down the row, with `Current Pipeline` off by two (a blank spacer
  column wasn't accounted for). This silently corrupted the Performance
  page's team scorecard, the AM Targets import (an AM's target could show
  as low as 1/10th the real figure), and the PDF report. Fixed by
  re-deriving every column index directly against a real production
  workbook; verified target/achieved/recurring/gap/pipeline all now match
  the source file exactly for every AM, both via `/api/performance` and
  `/api/config/am_targets/import`.

## [2.4.1] - 2026-09-29 (branch: v2.0)
### Added
- **HTTPS is live**: nginx now serves `https://pods2.jphartogi.com` (TLS
  1.2/1.3, HTTP/2) using the Let's Encrypt certificate obtained in 2.4.0,
  and redirects all plain HTTP traffic to HTTPS (the ACME challenge path
  stays on HTTP for renewals, per Let's Encrypt's requirement). Port 443 is
  now published in `docker-compose.yml`, and nginx mounts the certificate
  volume read-only.

Verified locally end-to-end with a dummy self-signed certificate at the same
path Let's Encrypt uses: HTTP redirects to HTTPS, HTTPS serves the real app
(login, API, page content) over TLS 1.3/HTTP2, the ACME challenge path still
resolves on port 80, and the container healthcheck (which curls plain HTTP)
still passes correctly despite the redirect.

## [2.4.0] - 2026-09-29 (branch: v2.0)
### Added
- **HTTPS groundwork**: nginx now recognizes `pods2.jphartogi.com` and serves
  Let's Encrypt's ACME HTTP-01 challenge path from a shared volume; a new
  `certbot` container (image `certbot/certbot`) handles certificate requests
  and renews automatically twice a day once a certificate exists. This phase
  is purely additive - no SSL is switched on yet, so it's safe to deploy on
  its own; see DEPLOY.md for the certificate request + SSL cutover steps.

## [2.3.2] - 2026-09-24 (branch: v2.0)
### Fixed
- **Sync from v1.9** failed with `column "id" does not exist` whenever v1.9's
  `deal_sync_map` table had any rows (created by using Engine 1 Sync) -
  that table's primary key is `local_deal_id`, not `id` like every other
  synced table, but the upsert always assumed `id`. Fixed by looking up each
  table's real primary key column instead of hardcoding it.

## [2.3.1] - 2026-09-24 (branch: v2.0)
### Changed
- **Sync from v1.9 now runs entirely over the web** - no more downloading
  `db.sqlite3` from v1.9's Files tab and re-uploading it here. Settings ->
  Sync from v1.9 now takes a URL, username and password (same pattern as
  Engine 1 Sync): it logs into v1.9 with those credentials, downloads its
  current database over a new admin-only endpoint there
  (`GET /api/admin/export_db`, added in v1.9 1.9.2), and runs the same
  upsert-by-id sync as before. One click, no file handling.

## [2.3.0] - 2026-09-24 (branch: v2.0)
### Added
- **Sync from v1.9** (Settings, admin only): repeatedly pull the legacy
  v1.9 app's (jphartogi.pythonanywhere.com) latest `db.sqlite3` into v2.0
  while v1.9 is still the live day-to-day system. Unlike the one-time
  `migrate_from_sqlite.py` used for the initial cutover (which truncates
  first, for a brand-new database), this upserts by id: a record present in
  v1.9 is inserted or refreshed here, but a record that only exists in
  v2.0 (created directly here) is left untouched. On a matching id, v1.9's
  version wins, since it remains the source of truth until the final
  migration (planned Oct/Nov 2026). Covers users, deals, deal tasks, login
  logs, performance snapshots, account coverage, config and the Engine 1
  sync map. Safe to run repeatedly - verified idempotent (re-running with
  the same file produces the same result) and that unmatched v2.0-only rows
  are never touched.

## [2.2.1] - 2026-09-17 (branch: v2.0)
### Changed
- Management View's Blockers / Action points / Account Manager performance
  no longer read as three separate floating cards - they're now sections of
  one continuous "Deep Dive" report panel, divided by hairlines instead of
  each having its own border/shadow, so the page reads as one piece of
  analysis rather than a stack of disconnected boxes.

## [2.2.0] - 2026-09-17 (branch: v2.0)
### Changed
- **Management View redesigned as an executive report**: a proper page header
  ("Executive Summary" / "Management View") replaces the old thin filter
  chip bar; the status line is now a bold RAG-colored banner with an icon
  badge instead of a plain sentence; the 6 financial KPIs use the same
  icon-badge tile style as the FY target hero card instead of flat text
  cards; and Account Manager Performance now leads with a ranked,
  color-coded attainment-% bar chart (click a bar to filter to that AM) ahead
  of the detailed per-AM rows - the "one chart that tells the story" pattern
  from consulting-style reporting. Blockers / Action points / AM performance
  section headers also got colored icon badges instead of plain icons.

## [2.1.3] - 2026-09-17 (branch: v2.0)
### Fixed
- Smoother scrolling: the page has 70+ card-style elements on screen at once
  (KPI tiles, table wrappers, filter bars), each with a layered blurred
  box-shadow that the browser had to repaint on every scroll frame. Cards now
  use CSS `contain: layout paint` (isolates each card's paint from the rest
  of the page) and a lighter shadow blur radius; the main content area adds
  momentum scrolling and `overscroll-behavior: contain` so an overscroll at
  the top/bottom doesn't rubber-band the whole page; the tab-switch fade
  animation was simplified from an opacity+transform combo to opacity-only.

## [2.1.2] - 2026-09-17 (branch: v2.0)
### Changed
- The FY Target hero card (gauge + KPI tiles) now follows whichever Account
  Manager filter is active on Tracker, Calendar or Management - pick an AM
  there and the Target, Achieved, Pipeline+Recurring, Gap and gauge all
  re-scope to that person, the same way Management's own summary row already
  did. Clearing the filter (or switching to a tab with no AM picked) goes
  back to the whole-team totals.

## [2.1.1] - 2026-09-17 (branch: v2.0)
### Changed
- **Tracker toolbar** (search / Account Manager / Pillar / Stage / Sort) redone as
  a single card-framed bar with icon-prefixed fields, a custom chevron on every
  select, and a focus ring on click - replacing the plain unstyled row of
  native inputs.
- **FY Target strip** replaced with a single "hero" card: a Chart.js radial
  gauge showing % of full-year target covered (Achieved / Recurring / 2026
  Pipeline / Remaining gap as its ring segments, with a matching legend)
  alongside three KPI tiles - a Stripe/AWS-console-style composed summary
  instead of four flat cards stacked above a plain progress bar.

## [2.1.0] - 2026-09-17 (branch: v2.0)
### Added
- **Notifications**: a bell icon in the top bar (badge = open item count) lists,
  per signed-in user, their own overdue/soon-due Team Tasks, any task that
  `@mentions` their full name in its text or note, and - for account managers -
  their own opportunities' target PO/revenue dates coming up. Clicking an item
  jumps straight to the opportunity or the task on the Weekly Meeting board and
  flashes it. Computed live via `GET /api/notifications`, polled every 60s.
### Changed
- The FY Target / Achieved / 2026 Pipeline+Recurring / Gap strip now only shows
  on Tracker, Calendar and Management (where it's actually relevant) instead of
  on every tab.
- Every plain KPI/stat card across Analytics, Management, Weekly Meeting, My
  Team Tasks, Calendar, Performance and AM Workload now uses a shared
  `.stat-card` treatment (colored accent bar, small-caps label, larger tabular
  value) instead of a flat `<p>`/`<p>` pair, for a more consistent, AWS
  console-style analytics look.

## [2.0.0] - 2026-09-16 (branch: v2.0, in progress)
### Changed
- **Postgres instead of SQLite.** Schema and all ~140 raw-SQL call sites
  ported to `psycopg` v3 with a small connection pool; auth sessions moved
  from an in-process dict into a `sessions` table, which is what makes
  running multiple gunicorn workers safe (v1 was pinned to one worker for
  exactly this reason).
- **Docker Compose deployment**: Postgres, the app, Nginx, and an `autoheal`
  sidecar - each service has a healthcheck, `restart: unless-stopped`
  handles process crashes, and `autoheal` restarts anything Docker reports
  `unhealthy` without exiting (e.g. the app losing its DB connection).
  Verified end-to-end: killing the app process triggers a restart; stopping
  Postgres under a live app flips its healthcheck and autoheal restarts the
  app container until Postgres comes back.
- **One-time migration script** (`migrate_from_sqlite.py`) to carry an
  existing v1 `db.sqlite3` into the new Postgres database, preserving row
  ids (and therefore foreign keys) and resetting sequences afterward.
  Verified against a full copy of real production data (42 deals, 15 users,
  34 login logs) with an exact row-count match and a working login
  afterward.
- **Document uploads**: attach PDF/PPTX/DOCX/XLSX/images to an opportunity
  from its detail drawer, stored on the `uploads` Docker volume (survives
  container rebuilds - verified by restarting the app mid-test and
  re-downloading). Upload/delete restricted to admin or that opportunity's
  own AM, same as editing the opportunity itself.
- **Chart.js** replaces the hand-rolled inline-SVG bar/donut charts across
  Pipeline Analytics and Account Coverage - same data and the same
  click-to-drill-down/click-to-filter behavior, now with real tooltips,
  gridlines, and animation.
- **Tabulator.js** replaces the hand-built Tracker table and its custom
  pagination controls - sortable columns, a proper page-size selector, and
  responsive column collapsing on narrow screens (collapsed fields expand
  inline per row) instead of the columns just getting squeezed unreadable.

## Known follow-up
- Account Coverage's and AM Workload's own tables are still the original
  hand-rolled markup - only the Tracker table was moved to Tabulator so far.

## [1.9.1] - 2026-09-14
### Changed
- AM Workload folded into the Account Coverage page as a second tab inside
  it (Account Coverage / AM Workload) instead of a separate nav item, so
  it's a quick switch back and forth rather than two destinations.
- Removed the target-vs-pipeline comparison entirely - AM Workload now shows
  pure account-count workload instead: a PODS 2-wide total, an
  accounts-handled-by-AM bar chart, and per-AM stat cards (total accounts,
  engaged, champion, needs attention), answering "how many accounts does
  PODS 2 have, and how many does AM Y actually handle" directly.

## [1.9.0] - 2026-09-14
### Added
- **AM Workload** (new tab, Analytics group): a per-Account-Manager view of
  everything on their plate. A ranked bar chart compares every AM's live
  Tracker pipeline (sum of open, non-Closed opportunity TCV) against their
  FY 2026 target as a coverage %; click any AM (bar, card, or the selector)
  to drill into their target/pipeline/closed-won figures, a status donut of
  their accounts, their biggest unhandled accounts, and their full editable
  account list (same tagging as Account Coverage, reused here so an AM can
  review their own book from one place). Account matching is name-fuzzy
  (handles "Ashari" vs "Ashari Asrar" from different source files) so the
  workload total reflects the real person, not each data source's own
  spelling.

## [1.8.0] - 2026-09-11
### Changed
- Account Coverage: replaced the flat "Accounts / Handled / Champion /
  Unreviewed / Cold / ..." card grid with four headline % gauges (given by
  performance team, engaged, champion, needs attention) and a richer
  "Relationship status" taxonomy that isn't just a bad-news scale - an
  account can now be tagged **Existing customer**, **Preferred / good
  relationship**, or **Growth potential**, alongside the needs-attention
  tags (renamed **At risk / cooling**, Low priority, No contact, Not
  preferable). New accounts from an import that already show billed revenue
  are now auto-tagged Existing customer instead of Unreviewed.
- Reworked the page layout: headline gauges, then a 2-up status/source donut
  row, then a 2-up AM-load/rotation-signal row (rotation signal is now a
  proportional bar list instead of plain text), then the filterable table.
### Fixed
- Added a migration for local databases that already had the old, narrower
  account_coverage status list (SQLite can't ALTER a CHECK constraint in
  place, so this rebuilds the table exactly as done for the past user-roles
  widening, remapping the old "cold" value to "at_risk").

## [1.7.0] - 2026-09-11
### Changed
- Account Coverage redesigned to be easier to read at a glance: the
  Full-Year Target / Achieved-YTD / Coverage-toward-target strip (a different,
  unrelated notion of "coverage") no longer shows on this page. Added a
  status donut, a New-vs-performance-given donut, and a stacked bar chart of
  account load per AM &mdash; every chart segment is clickable and filters
  the table below it. The account table now has a search box, a source
  filter, a champions-only filter, and sortable columns (click a header to
  sort, click again to reverse).
### Fixed
- Confirmed uploaded workbooks (monthly ACH and master account list) are
  never written to disk or stored in the database &mdash; only the account
  figures extracted from them are kept.

## [1.6.1] - 2026-09-11
### Changed
- Account Coverage moved out from under Pipeline Analytics into its own
  top-level nav item ("Account Coverage", next to Pipeline Analytics and
  Performance under the Analytics group) instead of being a sub-tab.

## [1.6.0] - 2026-09-11
### Added
- **Account Coverage** (Analytics &rarr; Account Coverage): combines every
  account the performance team's monthly import assigns to an AM with
  whatever opportunities the tracker already has for that company, so you can
  see how "loaded" each AM's book really is. Accounts without a matching
  opportunity can be tagged Cold / Low Priority / No Contact / Not Preferable,
  or marked as a "Champion" account; a Rotation Signal panel flags large
  accounts with no open opportunity, no champion tag, and no Not-Preferable
  reason as the best candidates for a coverage push or reassignment. An AM
  can also manually add an account they're working that isn't in the import.
- **Import master account list** (Account Coverage, admin only): uploads the
  Engine-1-wide "Master Account Planning" workbook and pulls in each PODS 2
  account's 2026 target and AM as the authoritative list. A **Coverage
  source breakdown** shows how many accounts came from the performance team
  (this import, or the monthly ACH one) versus how many are "new" &mdash;
  surfaced only because an AM filed a Tracker opportunity or added them by
  hand &mdash; plus overall and performance-given % handled.

## [1.5.0] - 2026-09-10
### Added
- **Engine 1 Sync** (Settings, admin only): push every opportunity here into
  Engine 1's PODS 2 over its own API. Remembers which Engine 1 record each
  opportunity maps to, so re-running it updates in place instead of
  duplicating. Falls back to **Export for Engine 1 import** — an `.xlsx` in
  Engine 1's exact backup-import column layout — for when this server can't
  make outbound requests (e.g. a free PythonAnywhere plan).
- Version tracking: this changelog, an `APP_VERSION` constant, `GET
  /api/version`, and the version shown in the UI.

## [1.4.0] - 2026-09-09
### Changed
- H2 2026 Command Center PDF report is now landscape and far more detailed for
  management: the Opportunity Detail table adds Strategic Pillar, TCV, Rev
  2026, Target Quarter, Target PO date, and Target Revenue date (with a
  blocked-deal marker), and a new "Upcoming Target Close Dates" section lists
  every dated PO/revenue milestone across the portfolio, nearest first.

## [1.3.0] - 2026-09-06
### Added
- Team Task "Assigned to" is now a searchable picker over registered users
  (excluding admin/management), not free text.
### Changed
- Weekly Meeting board groups tasks into collapsible per-opportunity threads
  (collapsed by default) instead of one flat list.
- Solved items split into a separate, collapsed-by-default "Solved" section;
  admin can delete a task from the Weekly Meeting board.

## [1.2.0] - 2026-09-04
### Added
- Each team task requires an individual "assigned to" name, not just a team.
- One-click "Mark Solved" / "Needs Discussion" buttons for admin and
  management on the Weekly Meeting board.

## [1.1.0] - 2026-09-03
### Added
- Weekly Meeting tasks threaded by opportunity with inline checklist editing.
- Per-AM PO/revenue target-close-date gaps on the management view.
### Fixed
- Weekly summary now looks 7 days *ahead* for planned items (it previously
  looked backward, which made "planned" mean the opposite of what it said).

## [1.0.0] - 2026-08-30
Baseline for version tracking - everything shipped before per-release
changelog entries started. Highlights, in order:
- Initial PODS-2 deal tracker: opportunities, 8-proof Execution Framework,
  Strategy, role-based access (Admin/AM/Management).
- Performance analytics, Tracker export, refreshed UI, Analytics tabs.
- Admin login logs and a Performance summary PDF export.
- Calendar overhaul, Action Plan tab, Management View revamp.
- AWS-inspired UI refresh with a feature search command palette.
- **Team Tasks**: the Sales ↔ Solution/Project/Product bridge, with new
  cross-functional roles and a shared Weekly Meeting board.
- Opportunity-modal autosave with an unsaved-changes guard.
- Per-AM target view (an AM sees their own number, not the whole team's),
  vertical Action Plan timeline driven by independent Timeline Items, Team
  Task from/to team chips, and a weekly summary.
