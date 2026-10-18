"""MCP server for the PODS 2 Dashboard Tracker.

Lets an AI agent (Claude Desktop, Claude Code, ...) read the sales dashboard and - if the
API key allows - log visits, raise blockers and add accounts. It is a thin client over the
dashboard's REST API, so all permissions are enforced server-side by the API key's user
and access level; this process holds no data and no database access.

    PODS_URL      dashboard base URL   (default https://pods2.jphartogi.com)
    PODS_API_KEY  key created in Settings -> API keys & agents   (required)
"""
import os
from datetime import date, timedelta

import httpx
from mcp.server.fastmcp import FastMCP

BASE_URL = os.environ.get("PODS_URL", "https://pods2.jphartogi.com").rstrip("/")
API_KEY = os.environ.get("PODS_API_KEY", "")

mcp = FastMCP("pods-dashboard", instructions=(
    "Read and update the PODS 2 sales dashboard: opportunities (pipeline), accounts, the visit "
    "calendar / daily log, blockers and team-week plans. Amounts in opportunities are IDR. "
    "Dates are YYYY-MM-DD. Prefer the read tools; only use write tools when the user asks."))


def _call(method: str, path: str, params: dict | None = None, json: dict | None = None):
    if not API_KEY:
        raise RuntimeError("PODS_API_KEY is not set")
    r = httpx.request(method, BASE_URL + path, params=params, json=json, timeout=30,
                      headers={"Authorization": f"Bearer {API_KEY}"})
    if r.status_code >= 400:
        try:
            msg = r.json().get("error", r.text)
        except Exception:
            msg = r.text
        raise RuntimeError(f"{r.status_code}: {msg}")
    return r.json()


def _deal_brief(d: dict) -> dict:
    return {"id": d["id"], "name": d["deal_name"], "customer": d["customer"], "am": d["assigned_am"],
            "stage": d["stage"], "pillar": d["strategic_pillar"], "tcv_idr": d["estimated_value"],
            "rev_2026_idr": d.get("revenue_2026", 0), "progress_pct": d["progress"],
            "blocked": d["is_blocked"], "blocker": d.get("blocker_description", ""),
            "target_quarter": d.get("target_quarter", ""), "expected_po_date": d.get("expected_po_date", ""),
            "expected_revenue_date": d.get("expected_revenue_date", "")}


def _account_brief(a: dict, ams: dict) -> dict:
    return {"id": a["id"], "name": a["name"], "am": ams.get(a["am_id"], ""), "type": a["type"],
            "cadence": a["cadence"], "visit_status": a["status"], "last_visit": a["last_visit"],
            "days_since_visit": a["days_since"], "next_planned_visit": a["next_planned_visit"],
            "plan_check": a["plan_check"], "opportunities": a["opp_count"], "opportunity_value_idr": a["opp_value"],
            "relationship_status": (a.get("cov") or {}).get("status"), "champion": (a.get("cov") or {}).get("is_champion")}


def _overview() -> dict:
    return _call("GET", "/api/visit/overview")


def _find(items: list, name: str, key: str = "name"):
    n = name.lower().strip()
    exact = [i for i in items if i[key].lower() == n]
    hits = exact or [i for i in items if n in i[key].lower()]
    if not hits:
        raise RuntimeError(f"Nothing matches '{name}'")
    if len(hits) > 1:
        raise RuntimeError(f"'{name}' is ambiguous: " + ", ".join(i[key] for i in hits[:8]))
    return hits[0]


# ------------------------------------------------------------------ read tools
@mcp.tool()
def search(query: str) -> dict:
    """Find opportunities and accounts by name. Returns matching opportunities (name, customer,
    AM, stage, value) and matching accounts with their number of ongoing opportunities."""
    terms = query.lower().split()
    deals = _call("GET", "/api/deals")
    hit = lambda text: all(t in text.lower() for t in terms)
    ov = _overview()
    ams = {a["id"]: a["name"] for a in ov["ams"]}
    return {
        "opportunities": [_deal_brief(d) for d in deals
                          if hit(f"{d['deal_name']} {d['customer']} {d['assigned_am']} {d['stage']}")][:25],
        "accounts": [_account_brief(a, ams) for a in ov["accounts"] if hit(a["name"])][:15],
    }


@mcp.tool()
def list_opportunities(am: str = "", stage: str = "", pillar: str = "", customer: str = "") -> list:
    """List opportunities in the pipeline, optionally filtered by account manager (full name),
    stage, strategic pillar or customer (partial name). Sorted by value, largest first."""
    params = {k: v for k, v in (("am", am), ("stage", stage), ("pillar", pillar)) if v}
    deals = _call("GET", "/api/deals", params=params)
    if customer:
        deals = [d for d in deals if customer.lower() in (d["customer"] or "").lower()]
    return [_deal_brief(d) for d in sorted(deals, key=lambda d: -d["estimated_value"])]


@mcp.tool()
def get_opportunity(opportunity_id: int) -> dict:
    """Full detail of one opportunity: strategy, next actions / timeline and the 8-proof
    execution framework status."""
    deals = _call("GET", "/api/deals")
    d = next((x for x in deals if x["id"] == opportunity_id), None)
    if not d:
        raise RuntimeError(f"No opportunity with id {opportunity_id}")
    out = _deal_brief(d)
    out.update({"strategy": d.get("strategy", ""), "next_actions": d.get("next_actions", []),
                "proofs": {k: {"status": v.get("status"), "due": v.get("due"), "entries": v.get("entries", [])}
                           for k, v in (d.get("proofs") or {}).items()}})
    return out


@mcp.tool()
def pipeline_summary() -> dict:
    """Headline numbers: total pipeline and 2026 revenue vs the full-year target, split by
    stage and by account manager."""
    deals = _call("GET", "/api/deals")
    cfg = _call("GET", "/api/config")
    by_stage, by_am = {}, {}
    for d in deals:
        for bucket, key in ((by_stage, d["stage"]), (by_am, d["assigned_am"] or "(unassigned)")):
            b = bucket.setdefault(key, {"count": 0, "tcv_idr": 0, "rev_2026_idr": 0})
            b["count"] += 1
            b["tcv_idr"] += d["estimated_value"]
            b["rev_2026_idr"] += d.get("revenue_2026", 0)
    return {"opportunities": len(deals), "total_tcv_idr": sum(d["estimated_value"] for d in deals),
            "total_rev_2026_idr": sum(d.get("revenue_2026", 0) for d in deals),
            "full_year_target_idr": cfg.get("target_amount"), "achieved_ytd_idr": cfg.get("current_achievement"),
            "by_stage": by_stage, "by_account_manager": by_am}


@mcp.tool()
def list_accounts(am: str = "", account_type: str = "", needs_attention: bool = False) -> list:
    """List managed accounts with visit status (On track / Slipping / Overdue), last visit,
    next planned visit, plan check and ongoing opportunities. Filter by AM name, type
    ('Priority' or 'Other'), or only those needing attention."""
    ov = _overview()
    ams = {a["id"]: a["name"] for a in ov["ams"]}
    rows = ov["accounts"]
    if am:
        rows = [a for a in rows if am.lower() in ams.get(a["am_id"], "").lower()]
    if account_type:
        rows = [a for a in rows if a["type"].lower() == account_type.lower()]
    if needs_attention:
        rows = [a for a in rows if a["needs_attention"]]
    return [_account_brief(a, ams) for a in rows]


@mcp.tool()
def visit_overview() -> dict:
    """Team-level visit cadence: totals (priority accounts, on track, slipping, overdue,
    no visit planned, open blockers) and one line per account manager, including whether
    they logged anything today."""
    ov = _overview()
    return {"today": ov["today"], "totals": ov["totals"],
            "account_managers": [{k: a[k] for k in ("name", "priority", "on_track", "slipping", "overdue",
                                                    "no_plan", "logged_today", "open_blockers")} for a in ov["ams"]]}


@mcp.tool()
def get_visit_tasks(am: str = "", date_from: str = "", date_to: str = "", status: str = "", account: str = "") -> list:
    """The daily log / plan: tasks (visits, calls, proposals...) with date, account, activity,
    status and outcome. Filter by AM name, date range, status or account name."""
    ov = _overview()
    params = {}
    if am:
        params["am_id"] = _find(ov["ams"], am)["id"]
    if account:
        params["account_id"] = _find(ov["accounts"], account)["id"]
    for k, v in (("date_from", date_from), ("date_to", date_to), ("status", status)):
        if v:
            params[k] = v
    tasks = _call("GET", "/api/visit/tasks", params=params)
    return [{"id": t["id"], "date": t["task_date"], "am": t["am_name"], "account": t["account_name"],
             "activity": t["activity"], "status": t["status"], "topic": t["topic"], "outcome": t["outcome"],
             "not_updated": t["not_updated"]} for t in tasks]


@mcp.tool()
def team_week(week_start: str = "") -> dict:
    """Who is doing what this week: every account manager's tasks grouped by day (Mon-Sun).
    week_start is any date in the wanted week (default: this week)."""
    d = date.fromisoformat(week_start) if week_start else date.fromisoformat(_overview()["today"])
    mon = d - timedelta(days=d.weekday())
    sun = mon + timedelta(days=6)
    tasks = _call("GET", "/api/visit/tasks", params={"date_from": mon.isoformat(), "date_to": sun.isoformat()})
    out: dict = {}
    for t in sorted(tasks, key=lambda t: (t["am_name"], t["task_date"])):
        out.setdefault(t["am_name"], {}).setdefault(t["task_date"], []).append(
            f"{t['account_name']} - {t['activity']} [{t['status']}]" + (f": {t['topic']}" if t["topic"] else ""))
    return {"week": f"{mon.isoformat()} to {sun.isoformat()}", "plans": out}


@mcp.tool()
def list_blockers(include_resolved: bool = False) -> list:
    """Blockers raised by account managers that need escalation, with owner, who to escalate
    to, due date and whether they are overdue."""
    rows = _call("GET", "/api/visit/blockers")
    return [b for b in rows if include_resolved or b["status"] != "Resolved"]


@mcp.tool()
def visit_analytics() -> dict:
    """Trends: visits done per week per AM (last 8 weeks), what the team did in the last 30
    days by activity, and how many AMs logged on each recent working day."""
    return _call("GET", "/api/visit/analytics")


# ----------------------------------------------------------------- write tools
@mcp.tool()
def log_visit_task(account: str, date: str, activity: str = "Visit (in person)", status: str = "Planned",
                   topic: str = "", outcome: str = "", am: str = "") -> dict:
    """Log or plan a task on an account's calendar. Needs a read & write API key. 'account' is the
    account name (partial is fine if unique); 'am' is only needed for admin keys. Only a Done
    visit / video meeting counts as a visit. Activity and status must be existing dropdown values."""
    ov = _overview()
    body = {"task_date": date, "activity": activity, "status": status, "topic": topic, "outcome": outcome}
    acct = _find([a for a in ov["accounts"] if not am or am.lower() in
                  next((x["name"] for x in ov["ams"] if x["id"] == a["am_id"]), "").lower()], account)
    body["account_id"], body["am_id"] = acct["id"], acct["am_id"]
    return _call("POST", "/api/visit/tasks", json=body)


@mcp.tool()
def raise_blocker(text: str, escalate_to: str = "PODS Lead", due_date: str = "", am: str = "") -> dict:
    """Raise a blocker that needs escalation (one sentence, include the account). Needs a read &
    write key. escalate_to: PODS Lead, Group Head, Management / BOD, Solution team, Pricing / finance, Other."""
    body = {"text": text, "escalate_to": escalate_to, "due_date": due_date}
    if am:
        body["am_id"] = _find(_overview()["ams"], am)["id"]
    return _call("POST", "/api/visit/blockers", json=body)


@mcp.tool()
def add_account(name: str, account_type: str = "Other", cadence: str = "", am: str = "") -> dict:
    """Add a customer/account by hand - e.g. a prospect with no opportunity yet. Needs a read & write
    key. 'am' is only needed for admin keys; type is 'Priority' or 'Other'."""
    body = {"name": name, "type": account_type}
    if cadence:
        body["cadence"] = cadence
    if am:
        body["am_id"] = _find(_overview()["ams"], am)["id"]
    return _call("POST", "/api/visit/accounts", json=body)


if __name__ == "__main__":
    mcp.run()
