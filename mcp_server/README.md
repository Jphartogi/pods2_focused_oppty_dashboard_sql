# PODS 2 Dashboard - MCP server

Lets an AI agent (Claude Desktop, Claude Code, any MCP client) read the sales dashboard - pipeline,
accounts, visit calendar, team week, blockers - and, with a read & write key, log visits, raise
blockers and add accounts. It is a thin client over the dashboard's REST API (see `docs/API.md`);
all permissions are enforced by the dashboard for the API key's user.

## 1. Create an API key
Dashboard -> **Settings -> API keys & agents**: name it, pick the user it **acts as**, pick **Read-only**
or **Read & write**, click *Create key* and copy it (shown once; `pods_...`).

* A key gets exactly its user's permissions. Use a dedicated user: e.g. a *management* user for a
  read-only analyst agent, an *account manager* user for an agent that logs one AM's visits.
* **Read-only** blocks every change no matter the user's role. Revoke any key from the same page.

## 2. Install (Python 3.10+)
```bash
cd mcp_server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Connect your agent
**Claude Desktop** - `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "pods-dashboard": {
      "command": "/absolute/path/to/mcp_server/.venv/bin/python",
      "args": ["/absolute/path/to/mcp_server/pods_mcp.py"],
      "env": { "PODS_URL": "https://pods2.jphartogi.com", "PODS_API_KEY": "pods_xxx" }
    }
  }
}
```
**Claude Code:**
```bash
claude mcp add pods-dashboard -e PODS_URL=https://pods2.jphartogi.com -e PODS_API_KEY=pods_xxx \
  -- /absolute/path/to/mcp_server/.venv/bin/python /absolute/path/to/mcp_server/pods_mcp.py
```

## Tools
| Read | |
|---|---|
| `search` | opportunities + accounts by name |
| `list_opportunities`, `get_opportunity` | pipeline, filter by AM / stage / pillar / customer; full detail incl. strategy & proofs |
| `pipeline_summary` | totals vs target, by stage and AM |
| `list_accounts` | accounts with visit status, plan check, ongoing opportunities |
| `visit_overview`, `visit_analytics` | cadence totals per AM; weekly visit trends |
| `get_visit_tasks`, `team_week` | daily log; who is doing what this week |
| `list_blockers` | open blockers needing escalation |

| Write (needs a read & write key) | |
|---|---|
| `log_visit_task` | log / plan a task on an account's calendar |
| `raise_blocker` | raise a blocker |
| `add_account` | add a customer / prospect with no opportunity yet |

Try: *"Who is doing what this week?"*, *"Which priority accounts are slipping?"*, *"What's open on Kereta Api Indonesia?"*
