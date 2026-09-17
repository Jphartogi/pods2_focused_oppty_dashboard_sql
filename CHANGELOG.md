# Changelog

All notable changes to the H2 2026 Command Center - PODS 2 are recorded here.
Versions follow [Semantic Versioning](https://semver.org/) (MAJOR.MINOR.PATCH):
MAJOR for breaking changes, MINOR for new backward-compatible features, PATCH
for fixes. The current version is shown in the app (bottom of the left nav,
and the sign-in screen) and via `GET /api/version`.

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
