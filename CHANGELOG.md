# Changelog

All notable changes to the H2 2026 Command Center - PODS 2 are recorded here.
Versions follow [Semantic Versioning](https://semver.org/) (MAJOR.MINOR.PATCH):
MAJOR for breaking changes, MINOR for new backward-compatible features, PATCH
for fixes. The current version is shown in the app (bottom of the left nav,
and the sign-in screen) and via `GET /api/version`.

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
