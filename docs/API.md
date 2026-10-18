# Dashboard REST API (quick reference)

Base URL `https://pods2.jphartogi.com`. JSON in / out. Errors are `{"error": "..."}` with a 4xx status.

## Authentication
Send `Authorization: Bearer <token>`. Two kinds of token:

* **API key** (`pods_...`) - for agents and integrations. Create in *Settings -> API keys & agents*.
  Acts as the chosen user (that user's role permissions apply); *Read-only* keys get `403` on any
  non-GET request. Keys cannot create other keys.
* **Session token** - `POST /api/login {"username","password"}` -> `{"token",...}`; expires, used by the web app.

## Read endpoints
| | |
|---|---|
| `GET /api/deals?am=&pillar=&stage=` | opportunities (full records) |
| `GET /api/config` | targets, stages, pillars, per-AM figures |
| `GET /api/account_managers` | AM names |
| `GET /api/visit/overview` | accounts with visit status, plan check, yesterday/next-day tasks, ongoing opportunities, relationship status; AM totals; dropdown options |
| `GET /api/visit/tasks?am_id=&account_id=&status=&activity=&date_from=&date_to=` | daily log / plan |
| `GET /api/visit/blockers` | blockers |
| `GET /api/visit/analytics` | weekly visits, activity mix, daily logging |
| `GET /api/weekly_plan?week_start=YYYY-MM-DD&am=` | My Weekly Plan entries |
| `GET /api/account_coverage` | account coverage / relationship tags |
| `GET /api/performance` | latest monthly ACH snapshot |

What an AM-linked key sees is limited to that AM's accounts/tasks; admin and management keys see everyone.

## Write endpoints (read & write key or session)
| | |
|---|---|
| `POST /api/visit/tasks` `{task_date, am_id, account_id, activity, status, topic, outcome}` | log / plan a task (`PUT`/`DELETE /api/visit/tasks/<id>` to change) |
| `POST /api/visit/blockers` `{text, escalate_to, due_date, status, am_id?}` | raise a blocker |
| `POST /api/visit/accounts` `{name, type?, cadence?, am_id?}` | add an account by hand |
| `PUT /api/visit/priority` `{am_id?, priority_ids: [...]}` | set an AM's priority accounts |
| `POST /api/deals`, `PUT /api/deals/<id>` | create / update opportunities |

Activity / status values must exist in the dropdown lists returned in `GET /api/visit/overview` -> `enums`.

## Example
```bash
curl -H "Authorization: Bearer $PODS_API_KEY" https://pods2.jphartogi.com/api/visit/overview
```
