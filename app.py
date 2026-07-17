"""
H2 2026 Command Center - PODS 2
Deal Execution Tracker & Strategy Dashboard (SQLite-backed version)

Row-level access control: each Account Manager can only edit the opportunities
assigned to them; ADMIN can edit everything; MANAGEMENT is read-only.
"""
import io
import json
import os
import secrets
import sqlite3
from datetime import datetime, date
from functools import wraps

from flask import Flask, g, jsonify, render_template, request, send_file
from werkzeug.security import check_password_hash, generate_password_hash

# Keep the database next to app.py so it persists in a predictable location
# regardless of the host's working directory (Render, PythonAnywhere, Docker, etc.).
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("DB_PATH", os.path.join(BASE_DIR, "db.sqlite3"))

app = Flask(__name__)

# In-memory token store: token -> {user_id, username, role, full_name}
TOKENS = {}

VALID_ROLES = ("admin", "account_manager", "management")
VALID_STAGES = ("Prospecting", "Negotiation", "Closed", "Blocked")

DEFAULT_PILLARS = [
    "IoT Connectivity",
    "Device Bundling",
    "CCTV & Vision Analytics",
    "Enterprise Solutions",
    "Digital Reward",
]
DEFAULT_SQUADS = ["Volume Squad", "Tender Squad", "Strategic Squad"]

# Seed Account Managers: (username, password, full_name)
SEED_AMS = [
    ("anisa", "anisa123", "Anisa Rahmy"),
    ("arie", "arie123", "Arie Prabowo"),
    ("ashari", "ashari123", "Ashari"),
    ("dimas", "dimas123", "Dimas"),
]

# Example per-AM revenue targets for H2 2026 (admin can edit in Settings).
DEFAULT_AM_TARGETS = {
    "Anisa Rahmy": 15_000_000_000,
    "Arie Prabowo": 13_000_000_000,
    "Ashari": 14_000_000_000,
    "Dimas": 15_000_000_000,
}


def _hash(pw):
    return generate_password_hash(pw, method="pbkdf2:sha256")


# --------------------------------------------------------------------------
# Database helpers
# --------------------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


# Seed opportunity dataset (PODS 2 real pipeline).
# Column order: deal_name, customer, assigned_am, squad, strategic_pillar,
#               estimated_value, target_quarter, stage, progress,
#               is_blocked, blocker_description, next_actions(JSON)
def _seed_deals():
    def na(items):
        return json.dumps([{"action": a, "done": d} for a, d in items])

    rows = [
        # ---------------- Anisa Rahmy ----------------
        ("Simcard IoT for DAOP (12 DAOP)", "PT Kereta Api Indonesia", "Anisa Rahmy",
         "Tender Squad", "IoT Connectivity", 600_000_000, "Q3 2026", "Negotiation", 40,
         0, "", na([("Confirm DAOP rollout scope", True), ("Finalize pricing", False)])),
        ("MDM – MS Connectivity + IoT (450 unit)", "PT Samsung Electronic Indonesia", "Anisa Rahmy",
         "Volume Squad", "Device Bundling", 2_400_000_000, "Q3 2026", "Negotiation", 50,
         0, "", na([("Align MDM spec", True), ("Commercial proposal", False)])),
        ("Tender IP Transit & Metronet Link 2", "PT Kereta Api Indonesia", "Anisa Rahmy",
         "Tender Squad", "Enterprise Solutions", 1_680_000_000, "Q3 2026", "Negotiation", 45,
         0, "", na([("Prepare tender docs", True), ("Target RFS Q3 2026", False)])),
        ("IoT Simcard – Wifi Kereta New Generation (450 unit)", "PT Kereta Api Indonesia", "Anisa Rahmy",
         "Volume Squad", "IoT Connectivity", 2_400_000_000, "Q3 2026", "Negotiation", 55,
         0, "", na([("Confirm August implementation", True), ("SIM provisioning plan", False)])),
        ("Simcard IoT for ADAS", "PT Trans Jakarta", "Anisa Rahmy",
         "Tender Squad", "IoT Connectivity", 1_250_000_000, "Q3 2026", "Prospecting", 30,
         0, "", na([("ADAS integration scoping", False), ("Target RFS Q3 2026", False)])),
        ("Connectivity HO", "GMF", "Anisa Rahmy",
         "Strategic Squad", "IoT Connectivity", 2_400_000_000, "Q3 2026", "Prospecting", 25,
         0, "", na([("HO connectivity survey", False)])),
        ("Fuel Management System", "PT Kereta Api Indonesia", "Anisa Rahmy",
         "Strategic Squad", "Enterprise Solutions", 4_000_000_000, "Q4 2026", "Prospecting", 20,
         0, "", na([("Complete POC (in progress)", False), ("2026 revenue plan", False)])),
        ("CCTV HO (Pengadaan Langsung)", "PT Trans Jakarta", "Anisa Rahmy",
         "Tender Squad", "CCTV & Vision Analytics", 200_000_000, "Q3 2026", "Prospecting", 30,
         0, "", na([("Prepare pengadaan langsung docs", False)])),

        # ---------------- Arie Prabowo ----------------
        ("Device Bundling Samsung A17 EE", "Glico Indonesia", "Arie Prabowo",
         "Volume Squad", "Device Bundling", 256_000_000, "Q3 2026", "Prospecting", 30,
         0, "", na([("Maintain fixed partner price", False), ("Confirm delivery timeline", False)])),
        ("Smart Asset Rental", "YIMM", "Arie Prabowo",
         "Strategic Squad", "Enterprise Solutions", 80_800_000, "Q3 2026", "Prospecting", 25,
         0, "", na([("Scope asset rental", False)])),
        ("Device Bundling Samsung A17 EE", "Karoseri Laksana", "Arie Prabowo",
         "Volume Squad", "Device Bundling", 1_300_000_000, "Q3 2026", "Prospecting", 35,
         0, "", na([("Lock partner price for large qty", False), ("Delivery schedule", False)])),
        ("Enterprise Asset Management", "Kobelindo Compressors", "Arie Prabowo",
         "Strategic Squad", "Enterprise Solutions", 385_000_000, "Q3 2026", "Prospecting", 30,
         0, "", na([("EAM requirement workshop", False)])),
        ("People Tracking Solution", "Triputra Agro Persada", "Arie Prabowo",
         "Strategic Squad", "Enterprise Solutions", 2_400_000_000, "Q4 2026", "Prospecting", 20,
         0, "", na([("Assign dedicated PIC", False)])),
        ("CCTV AI Crowd Analytics", "YIMM", "Arie Prabowo",
         "Strategic Squad", "CCTV & Vision Analytics", 180_000_000, "Q3 2026", "Prospecting", 30,
         0, "", na([("Frequent customer visit", False)])),
        ("CCTV Portable", "YIMM", "Arie Prabowo",
         "Volume Squad", "CCTV & Vision Analytics", 1_100_000_000, "Q3 2026", "Prospecting", 25,
         0, "", na([("Manage customer expectations", False)])),
        ("Smart Vehicle Monitoring System", "Triputra Agro Persada", "Arie Prabowo",
         "Strategic Squad", "Enterprise Solutions", 4_900_000_000, "Q4 2026", "Prospecting", 15,
         0, "", na([("Assign skilled implementation team", False)])),
        ("ESTA Vision", "Waresix", "Arie Prabowo",
         "Strategic Squad", "CCTV & Vision Analytics", 248_000_000, "Q3 2026", "Prospecting", 30,
         0, "", na([("ESTA vision demo", False)])),
        ("IoT Connectivity (Consortium)", "Consortium Mastrans Bandung", "Arie Prabowo",
         "Tender Squad", "IoT Connectivity", 1_200_000_000, "Q4 2026", "Prospecting", 20,
         0, "", na([("Consortium alignment", False)])),

        # ---------------- Ashari ----------------
        ("Strategic Account – AnterAja", "Tri Adi Bersama (AnterAja)", "Ashari",
         "Strategic Squad", "Enterprise Solutions", 7_300_000_000, "H2 2026", "Negotiation", 35,
         0, "", na([("Account plan", True), ("Solution proposal", False)])),
        ("Strategic Account – Mayora", "Cipta Niaga Semesta (Mayora Group)", "Ashari",
         "Strategic Squad", "Enterprise Solutions", 540_000_000, "H2 2026", "Prospecting", 25,
         0, "", na([("Discovery meeting", False)])),
        ("Strategic Account – IMP", "Integrasi Multi Persada (IMP)", "Ashari",
         "Strategic Squad", "Enterprise Solutions", 4_200_000_000, "H2 2026", "Prospecting", 25,
         0, "", na([("Needs assessment", False)])),
        ("Strategic Account – Cikarang Listrindo", "PT Cikarang Listrindo, Tbk.", "Ashari",
         "Strategic Squad", "Enterprise Solutions", 1_000_000_000, "H2 2026", "Prospecting", 20,
         0, "", na([("Intro meeting", False)])),
        ("Strategic Account – Indo Lysaght", "PT Indo Lysaght", "Ashari",
         "Strategic Squad", "Enterprise Solutions", 360_000_000, "H2 2026", "Prospecting", 20,
         0, "", na([("Qualify opportunity", False)])),

        # ---------------- Dimas ----------------
        ("Device Bundling – 2250 Drivers", "PT Green SM", "Dimas",
         "Volume Squad", "Device Bundling", 8_100_000_000, "Q3-Q4 2026", "Negotiation", 40,
         0, "", na([("Confirm 2250 unit rollout", True), ("Delivery scheduling", False)])),
        ("M2M IoT Simcard – Green SM Bike (10k)", "PT Green SM", "Dimas",
         "Volume Squad", "IoT Connectivity", 990_000_000, "Q3 2026", "Negotiation", 50,
         0, "", na([("August implementation plan", True), ("SIM activation", False)])),
        ("M2M IoT Simcard – Green SM EVEE Car (6k)", "PT Green SM", "Dimas",
         "Volume Squad", "IoT Connectivity", 691_000_000, "Q3 2026", "Negotiation", 45,
         0, "", na([("EVEE fleet onboarding", False)])),
        ("Device Bundling – Dexa & Ferron Pharma", "PT Dexa Group", "Dimas",
         "Volume Squad", "Device Bundling", 1_600_000_000, "Q3-Q4 2026", "Prospecting", 30,
         0, "", na([("Employee bundling scope", False)])),
        ("Digital Reward – 60TB", "PT Via Yotta Byte", "Dimas",
         "Strategic Squad", "Digital Reward", 1_900_000_000, "Q3 2026", "Negotiation", 40,
         0, "", na([("Q3 implementation", False)])),
        ("CCTV Analytics – 3 MOR Stores (30 titik)", "PT OT Group", "Dimas",
         "Strategic Squad", "CCTV & Vision Analytics", 500_000_000, "Q3 2026", "Prospecting", 30,
         0, "", na([("Site survey 3 lokasi", False), ("Installation plan 30 titik", False)])),
        ("Smart Water AI Inspection – Crystalin", "PT OT Group", "Dimas",
         "Strategic Squad", "CCTV & Vision Analytics", 332_000_000, "Q3 2026", "Prospecting", 25,
         0, "", na([("Label & coding inspection PoC", False)])),
        ("Smart Building Energy Saving", "PT Kawanlama Group", "Dimas",
         "Strategic Squad", "Enterprise Solutions", 400_000_000, "Q3 2026", "Prospecting", 25,
         0, "", na([("Energy saving assessment", False)])),
    ]
    return rows


def migrate_db(db):
    """Add columns introduced after the first release, without touching data."""
    def columns(table):
        return {r[1] for r in db.execute(f"PRAGMA table_info({table})")}

    deal_cols = columns("deals")
    if "revenue_2026" not in deal_cols:
        db.execute("ALTER TABLE deals ADD COLUMN revenue_2026 INTEGER DEFAULT 0")
        db.execute("UPDATE deals SET revenue_2026 = estimated_value WHERE revenue_2026 = 0")
    if "strategy" not in deal_cols:
        db.execute("ALTER TABLE deals ADD COLUMN strategy TEXT DEFAULT ''")

    config_cols = columns("config")
    if "am_targets" not in config_cols:
        db.execute("ALTER TABLE config ADD COLUMN am_targets TEXT DEFAULT '{}'")
        db.execute("UPDATE config SET am_targets = ?", (json.dumps(DEFAULT_AM_TARGETS),))
    if "current_achievement" not in config_cols:
        db.execute("ALTER TABLE config ADD COLUMN current_achievement INTEGER DEFAULT 0")
    if "recurring_revenue" not in config_cols:
        db.execute("ALTER TABLE config ADD COLUMN recurring_revenue INTEGER DEFAULT 0")


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS deals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deal_name TEXT NOT NULL,
            customer TEXT DEFAULT '',
            assigned_am TEXT DEFAULT '',
            squad TEXT NOT NULL,
            strategic_pillar TEXT NOT NULL,
            estimated_value INTEGER NOT NULL,
            revenue_2026 INTEGER DEFAULT 0,
            target_quarter TEXT DEFAULT '',
            stage TEXT NOT NULL,
            progress INTEGER DEFAULT 0,
            is_blocked BOOLEAN DEFAULT 0,
            blocker_description TEXT,
            next_actions TEXT,
            strategy TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'account_manager', 'management')),
            full_name TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_amount INTEGER DEFAULT 163000000000,
            strategic_pillars TEXT,
            squads TEXT,
            am_targets TEXT DEFAULT '{}',
            current_achievement INTEGER DEFAULT 0,
            recurring_revenue INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    # Safe, additive migrations for databases created by an earlier version.
    # ALTER only when the column is missing, so existing data is preserved.
    migrate_db(db)

    # Seed users if empty
    if db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        seed_users = [
            ("admin", "admin123", "admin", "Administrator"),
            ("exec", "exec123", "management", "Management Viewer"),
        ]
        for username, password, role, full_name in seed_users:
            db.execute(
                "INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)",
                (username, _hash(password), role, full_name),
            )
        for username, password, full_name in SEED_AMS:
            db.execute(
                "INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)",
                (username, _hash(password), "account_manager", full_name),
            )

    # Seed config if empty
    if db.execute("SELECT COUNT(*) FROM config").fetchone()[0] == 0:
        db.execute(
            "INSERT INTO config (target_amount, strategic_pillars, squads, am_targets) VALUES (?, ?, ?, ?)",
            (163_000_000_000, json.dumps(DEFAULT_PILLARS), json.dumps(DEFAULT_SQUADS),
             json.dumps(DEFAULT_AM_TARGETS)),
        )

    # Seed deals if empty
    if db.execute("SELECT COUNT(*) FROM deals").fetchone()[0] == 0:
        db.executemany(
            """INSERT INTO deals
               (deal_name, customer, assigned_am, squad, strategic_pillar,
                estimated_value, target_quarter, stage, progress,
                is_blocked, blocker_description, next_actions)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            _seed_deals(),
        )
        # Default 2026 realizable revenue to the full TCV; admin refines per deal.
        db.execute("UPDATE deals SET revenue_2026 = estimated_value")

    db.commit()
    db.close()


# --------------------------------------------------------------------------
# Auth helpers
# --------------------------------------------------------------------------
def get_current_user():
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "").strip() if auth else request.args.get("token", "")
    return TOKENS.get(token)


def login_required(roles=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({"error": "Unauthorized"}), 401
            if roles and user["role"] not in roles:
                return jsonify({"error": "Forbidden"}), 403
            g.current_user = user
            return f(*args, **kwargs)

        return wrapper

    return decorator


def can_edit_deal(user, deal_row):
    """ADMIN edits anything; an AM edits only opportunities assigned to them."""
    if user["role"] == "admin":
        return True
    if user["role"] == "account_manager":
        return (deal_row["assigned_am"] or "") == (user["full_name"] or "")
    return False


def deal_to_dict(row):
    return {
        "id": row["id"],
        "deal_name": row["deal_name"],
        "customer": row["customer"] or "",
        "assigned_am": row["assigned_am"] or "",
        "squad": row["squad"],
        "strategic_pillar": row["strategic_pillar"],
        "estimated_value": row["estimated_value"],
        "revenue_2026": row["revenue_2026"] if row["revenue_2026"] is not None else 0,
        "target_quarter": row["target_quarter"] or "",
        "stage": row["stage"],
        "progress": row["progress"],
        "is_blocked": bool(row["is_blocked"]),
        "blocker_description": row["blocker_description"] or "",
        "next_actions": json.loads(row["next_actions"] or "[]"),
        "strategy": (row["strategy"] if "strategy" in row.keys() else "") or "",
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


# --------------------------------------------------------------------------
# Views
# --------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


# --------------------------------------------------------------------------
# Auth API
# --------------------------------------------------------------------------
@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(force=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    db = get_db()
    row = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if not row or not check_password_hash(row["password"], password):
        return jsonify({"error": "Invalid username or password"}), 401

    token = secrets.token_hex(24)
    TOKENS[token] = {
        "user_id": row["id"],
        "username": row["username"],
        "role": row["role"],
        "full_name": row["full_name"] or row["username"],
    }
    return jsonify({
        "token": token,
        "role": row["role"],
        "username": row["username"],
        "full_name": row["full_name"] or row["username"],
    })


@app.route("/api/logout", methods=["POST"])
def api_logout():
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "").strip()
    TOKENS.pop(token, None)
    return jsonify({"ok": True})


# --------------------------------------------------------------------------
# Account Managers (for filters / assignment dropdowns) - any authenticated user
# --------------------------------------------------------------------------
@app.route("/api/account_managers", methods=["GET"])
@login_required()
def get_account_managers():
    db = get_db()
    rows = db.execute(
        "SELECT full_name FROM users WHERE role = 'account_manager' ORDER BY full_name"
    ).fetchall()
    names = [r["full_name"] for r in rows if r["full_name"]]
    return jsonify(names)


# --------------------------------------------------------------------------
# Deals API
# --------------------------------------------------------------------------
@app.route("/api/deals", methods=["GET"])
@login_required()
def get_deals():
    db = get_db()
    query = "SELECT * FROM deals WHERE 1=1"
    params = []
    for field, col in (("squad", "squad"), ("pillar", "strategic_pillar"),
                       ("am", "assigned_am"), ("stage", "stage"),
                       ("quarter", "target_quarter")):
        val = request.args.get(field)
        if val:
            query += f" AND {col} = ?"
            params.append(val)
    query += " ORDER BY estimated_value DESC"
    rows = db.execute(query, params).fetchall()
    return jsonify([deal_to_dict(r) for r in rows])


@app.route("/api/deals", methods=["POST"])
@login_required(roles=("admin", "account_manager"))
def create_deal():
    data = request.get_json(force=True) or {}
    user = g.current_user

    # An AM can only create opportunities assigned to themselves.
    if user["role"] == "account_manager":
        assigned_am = user["full_name"]
    else:
        assigned_am = data.get("assigned_am", "")

    est_value = int(data.get("estimated_value", 0) or 0)
    rev_2026 = data.get("revenue_2026")
    rev_2026 = int(rev_2026) if rev_2026 not in (None, "") else est_value

    db = get_db()
    cur = db.execute(
        """INSERT INTO deals
           (deal_name, customer, assigned_am, squad, strategic_pillar, estimated_value,
            revenue_2026, target_quarter, stage, progress, is_blocked, blocker_description,
            next_actions, strategy, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
        (
            data.get("deal_name", "Untitled Opportunity"),
            data.get("customer", ""),
            assigned_am,
            data.get("squad"),
            data.get("strategic_pillar"),
            est_value,
            rev_2026,
            data.get("target_quarter", ""),
            data.get("stage", "Prospecting"),
            int(data.get("progress", 0) or 0),
            1 if data.get("is_blocked") else 0,
            data.get("blocker_description", ""),
            json.dumps(data.get("next_actions", [])),
            data.get("strategy", ""),
        ),
    )
    db.commit()
    row = db.execute("SELECT * FROM deals WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(deal_to_dict(row)), 201


@app.route("/api/deals/<int:deal_id>", methods=["PUT"])
@login_required(roles=("admin", "account_manager"))
def update_deal(deal_id):
    data = request.get_json(force=True) or {}
    user = g.current_user
    db = get_db()
    row = db.execute("SELECT * FROM deals WHERE id = ?", (deal_id,)).fetchone()
    if not row:
        return jsonify({"error": "Deal not found"}), 404
    if not can_edit_deal(user, row):
        return jsonify({"error": "You can only edit opportunities assigned to you"}), 403

    # AMs cannot reassign a deal to someone else.
    if user["role"] == "account_manager":
        assigned_am = user["full_name"]
    else:
        assigned_am = data.get("assigned_am", row["assigned_am"])

    existing_strategy = row["strategy"] if "strategy" in row.keys() else ""
    db.execute(
        """UPDATE deals SET
             deal_name = ?, customer = ?, assigned_am = ?, squad = ?, strategic_pillar = ?,
             estimated_value = ?, revenue_2026 = ?, target_quarter = ?, stage = ?, progress = ?,
             is_blocked = ?, blocker_description = ?, next_actions = ?, strategy = ?,
             updated_at = CURRENT_TIMESTAMP
           WHERE id = ?""",
        (
            data.get("deal_name", row["deal_name"]),
            data.get("customer", row["customer"]),
            assigned_am,
            data.get("squad", row["squad"]),
            data.get("strategic_pillar", row["strategic_pillar"]),
            int(data.get("estimated_value", row["estimated_value"]) or 0),
            int(data.get("revenue_2026", row["revenue_2026"] or 0) or 0),
            data.get("target_quarter", row["target_quarter"]),
            data.get("stage", row["stage"]),
            int(data.get("progress", row["progress"]) or 0),
            1 if data.get("is_blocked", row["is_blocked"]) else 0,
            data.get("blocker_description", row["blocker_description"]),
            json.dumps(data.get("next_actions", json.loads(row["next_actions"] or "[]"))),
            data.get("strategy", existing_strategy),
            deal_id,
        ),
    )
    db.commit()
    row = db.execute("SELECT * FROM deals WHERE id = ?", (deal_id,)).fetchone()
    return jsonify(deal_to_dict(row))


@app.route("/api/deals/<int:deal_id>", methods=["DELETE"])
@login_required(roles=("admin", "account_manager"))
def delete_deal(deal_id):
    db = get_db()
    row = db.execute("SELECT * FROM deals WHERE id = ?", (deal_id,)).fetchone()
    if not row:
        return jsonify({"error": "Deal not found"}), 404
    if not can_edit_deal(g.current_user, row):
        return jsonify({"error": "You can only delete opportunities assigned to you"}), 403
    db.execute("DELETE FROM deals WHERE id = ?", (deal_id,))
    db.commit()
    return jsonify({"ok": True})


@app.route("/api/deals/<int:deal_id>/progress", methods=["PUT"])
@login_required(roles=("admin", "account_manager"))
def update_progress(deal_id):
    data = request.get_json(force=True) or {}
    progress = max(0, min(100, int(data.get("progress", 0))))
    db = get_db()
    row = db.execute("SELECT * FROM deals WHERE id = ?", (deal_id,)).fetchone()
    if not row:
        return jsonify({"error": "Deal not found"}), 404
    if not can_edit_deal(g.current_user, row):
        return jsonify({"error": "You can only edit opportunities assigned to you"}), 403
    db.execute(
        "UPDATE deals SET progress = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (progress, deal_id),
    )
    db.commit()
    row = db.execute("SELECT * FROM deals WHERE id = ?", (deal_id,)).fetchone()
    return jsonify(deal_to_dict(row))


@app.route("/api/deals/<int:deal_id>/blocker", methods=["PUT"])
@login_required(roles=("admin", "account_manager"))
def update_blocker(deal_id):
    data = request.get_json(force=True) or {}
    db = get_db()
    row = db.execute("SELECT * FROM deals WHERE id = ?", (deal_id,)).fetchone()
    if not row:
        return jsonify({"error": "Deal not found"}), 404
    if not can_edit_deal(g.current_user, row):
        return jsonify({"error": "You can only edit opportunities assigned to you"}), 403
    db.execute(
        """UPDATE deals SET is_blocked = ?, blocker_description = ?,
           updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
        (1 if data.get("is_blocked") else 0, data.get("blocker_description", ""), deal_id),
    )
    db.commit()
    row = db.execute("SELECT * FROM deals WHERE id = ?", (deal_id,)).fetchone()
    return jsonify(deal_to_dict(row))


# --------------------------------------------------------------------------
# Users API (ADMIN only)
# --------------------------------------------------------------------------
@app.route("/api/users", methods=["GET"])
@login_required(roles=("admin",))
def get_users():
    db = get_db()
    rows = db.execute(
        "SELECT id, username, role, full_name, created_at FROM users ORDER BY id"
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/users", methods=["POST"])
@login_required(roles=("admin",))
def create_user():
    data = request.get_json(force=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    role = data.get("role", "")
    full_name = data.get("full_name", "").strip() or username

    if not username or not password or role not in VALID_ROLES:
        return jsonify({"error": "username, password and a valid role are required"}), 400

    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if existing:
        return jsonify({"error": "Username already exists"}), 409

    cur = db.execute(
        "INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)",
        (username, _hash(password), role, full_name),
    )
    db.commit()
    row = db.execute(
        "SELECT id, username, role, full_name, created_at FROM users WHERE id = ?",
        (cur.lastrowid,),
    ).fetchone()
    return jsonify(dict(row)), 201


@app.route("/api/users/<int:user_id>", methods=["PUT"])
@login_required(roles=("admin",))
def update_user(user_id):
    data = request.get_json(force=True) or {}
    db = get_db()
    row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        return jsonify({"error": "User not found"}), 404

    role = data.get("role", row["role"])
    if role not in VALID_ROLES:
        return jsonify({"error": "Invalid role"}), 400

    full_name = data.get("full_name", row["full_name"])
    password_hash = row["password"]
    if data.get("password"):
        password_hash = _hash(data["password"])

    db.execute(
        "UPDATE users SET role = ?, full_name = ?, password = ? WHERE id = ?",
        (role, full_name, password_hash, user_id),
    )
    db.commit()
    row = db.execute(
        "SELECT id, username, role, full_name, created_at FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    return jsonify(dict(row))


@app.route("/api/users/<int:user_id>", methods=["DELETE"])
@login_required(roles=("admin",))
def delete_user(user_id):
    if g.current_user["user_id"] == user_id:
        return jsonify({"error": "Cannot delete your own account while logged in"}), 400
    db = get_db()
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    return jsonify({"ok": True})


# --------------------------------------------------------------------------
# Config API
# --------------------------------------------------------------------------
def config_to_dict(row):
    keys = row.keys()
    try:
        am_targets = json.loads(row["am_targets"] or "{}") if "am_targets" in keys else {}
    except (KeyError, TypeError):
        am_targets = {}
    return {
        "target_amount": row["target_amount"],
        "strategic_pillars": json.loads(row["strategic_pillars"]),
        "squads": json.loads(row["squads"]),
        "am_targets": am_targets,
        "current_achievement": (row["current_achievement"] if "current_achievement" in keys else 0) or 0,
        "recurring_revenue": (row["recurring_revenue"] if "recurring_revenue" in keys else 0) or 0,
        "updated_at": row["updated_at"],
    }


@app.route("/api/config", methods=["GET"])
@login_required()
def get_config():
    db = get_db()
    row = db.execute("SELECT * FROM config ORDER BY id DESC LIMIT 1").fetchone()
    return jsonify(config_to_dict(row))


@app.route("/api/config", methods=["PUT"])
@login_required(roles=("admin",))
def update_config():
    data = request.get_json(force=True) or {}
    db = get_db()
    row = db.execute("SELECT * FROM config ORDER BY id DESC LIMIT 1").fetchone()

    current = config_to_dict(row)
    target_amount = int(data.get("target_amount", row["target_amount"]) or 0)
    strategic_pillars = data.get("strategic_pillars", json.loads(row["strategic_pillars"]))
    squads = data.get("squads", json.loads(row["squads"]))
    am_targets = data.get("am_targets", current["am_targets"])
    am_targets = {k: int(v or 0) for k, v in am_targets.items()}
    current_achievement = int(data.get("current_achievement", current["current_achievement"]) or 0)
    recurring_revenue = int(data.get("recurring_revenue", current["recurring_revenue"]) or 0)

    db.execute(
        """UPDATE config SET target_amount = ?, strategic_pillars = ?, squads = ?,
           am_targets = ?, current_achievement = ?, recurring_revenue = ?,
           updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
        (target_amount, json.dumps(strategic_pillars), json.dumps(squads),
         json.dumps(am_targets), current_achievement, recurring_revenue, row["id"]),
    )
    db.commit()
    row = db.execute("SELECT * FROM config WHERE id = ?", (row["id"],)).fetchone()
    return jsonify(config_to_dict(row))


# --------------------------------------------------------------------------
# PDF Export
# --------------------------------------------------------------------------
def _fmt_idr(value):
    if value >= 1e9:
        return f"IDR {value/1e9:,.2f}B"
    if value >= 1e6:
        return f"IDR {value/1e6:,.1f}M"
    return f"IDR {value:,.0f}"


@app.route("/api/export/pdf", methods=["GET"])
@login_required()
def export_pdf():
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    db = get_db()
    deals = [deal_to_dict(r) for r in db.execute("SELECT * FROM deals").fetchall()]
    config = config_to_dict(db.execute("SELECT * FROM config ORDER BY id DESC LIMIT 1").fetchone())

    total_pipeline = sum(d["estimated_value"] for d in deals)
    total_rev_2026 = sum(d["revenue_2026"] for d in deals)
    weighted = sum(d["estimated_value"] * d["progress"] / 100 for d in deals)
    target = config["target_amount"]
    achieved = config.get("current_achievement", 0)
    recurring = config.get("recurring_revenue", 0)
    covered = achieved + recurring + total_rev_2026
    remaining_gap = max(target - covered, 0)
    gap = target - total_pipeline
    avg_deal = total_pipeline / len(deals) if deals else 0
    am_targets = config.get("am_targets", {})

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        leftMargin=1.6 * cm, rightMargin=1.6 * cm,
    )
    styles = getSampleStyleSheet()
    brand = colors.HexColor("#1a73e8")
    title_style = ParagraphStyle("TitleC", parent=styles["Title"], fontSize=18, textColor=brand)
    h2_style = ParagraphStyle("H2C", parent=styles["Heading2"], fontSize=13, textColor=brand,
                              spaceBefore=14, spaceAfter=6)
    body_style = styles["BodyText"]

    def make_table(data, col_widths):
        t = Table(data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), brand),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dadce0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f3f4")]),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        return t

    story = []
    story.append(Paragraph("H2 2026 Command Center - PODS 2", title_style))
    story.append(Paragraph("Deal Execution &amp; Strategy Report", styles["Heading3"]))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", body_style))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Executive Summary", h2_style))
    story.append(Paragraph(
        f"Against the full-year 2026 target of {_fmt_idr(target)}, the team has achieved "
        f"{_fmt_idr(achieved)} to date, expects {_fmt_idr(recurring)} in recurring revenue, and is "
        f"tracking {_fmt_idr(total_rev_2026)} of realizable 2026 pipeline across {len(deals)} "
        f"opportunities. That covers {_fmt_idr(covered)}, leaving a remaining gap of "
        f"{_fmt_idr(remaining_gap)} to close. Execution spans four Account Managers across IoT "
        f"Connectivity, Device Bundling, CCTV &amp; Vision Analytics, Enterprise Solutions and "
        f"Digital Reward.",
        body_style,
    ))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("Full-Year 2026 Coverage", h2_style))
    story.append(make_table([
        ["Metric", "Value"],
        ["Full-Year 2026 Target", _fmt_idr(target)],
        ["Achieved (YTD)", _fmt_idr(achieved)],
        ["Recurring (upcoming months)", _fmt_idr(recurring)],
        ["2026 Realizable Pipeline", _fmt_idr(total_rev_2026)],
        ["Total Covered", _fmt_idr(covered)],
        ["Remaining Gap to Close", _fmt_idr(remaining_gap)],
    ], [8 * cm, 8 * cm]))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Pipeline KPIs", h2_style))
    story.append(make_table([
        ["Metric", "Value"],
        ["Current Pipeline (TCV)", _fmt_idr(total_pipeline)],
        ["Weighted Pipeline", _fmt_idr(weighted)],
        ["Total Opportunities", str(len(deals))],
        ["Average Deal Size", _fmt_idr(avg_deal)],
    ], [8 * cm, 8 * cm]))
    story.append(Spacer(1, 0.4 * cm))

    # By Account Manager (with target attainment on 2026 revenue)
    story.append(Paragraph("Account Manager Target vs Pipeline", h2_style))
    am_val = {}
    am_rev = {}
    am_cnt = {}
    for d in deals:
        am_val[d["assigned_am"]] = am_val.get(d["assigned_am"], 0) + d["estimated_value"]
        am_rev[d["assigned_am"]] = am_rev.get(d["assigned_am"], 0) + d["revenue_2026"]
        am_cnt[d["assigned_am"]] = am_cnt.get(d["assigned_am"], 0) + 1
    am_rows = [["Account Manager", "Opps", "TCV Pipeline", "2026 Rev", "Target", "Attain."]]
    for am in sorted(am_val, key=lambda k: am_val[k], reverse=True):
        tgt = am_targets.get(am, 0)
        attain = f"{(am_rev[am]/tgt*100):.0f}%" if tgt else "-"
        am_rows.append([am, str(am_cnt[am]), _fmt_idr(am_val[am]),
                        _fmt_idr(am_rev[am]), _fmt_idr(tgt) if tgt else "-", attain])
    story.append(make_table(am_rows, [4.5 * cm, 1.3 * cm, 3.2 * cm, 3.2 * cm, 3.2 * cm, 1.6 * cm]))
    story.append(Spacer(1, 0.4 * cm))

    # By stage
    story.append(Paragraph("Deals by Stage", h2_style))
    stage_counts = {}
    for d in deals:
        stage_counts[d["stage"]] = stage_counts.get(d["stage"], 0) + 1
    story.append(make_table(
        [["Stage", "Count"]] + [[k, str(v)] for k, v in stage_counts.items()],
        [8 * cm, 8 * cm],
    ))
    story.append(Spacer(1, 0.4 * cm))

    # By pillar
    story.append(Paragraph("Pipeline by Strategic Pillar", h2_style))
    pillar_values = {}
    for d in deals:
        pillar_values[d["strategic_pillar"]] = pillar_values.get(d["strategic_pillar"], 0) + d["estimated_value"]
    story.append(make_table(
        [["Strategic Pillar", "Pipeline Value"]] +
        [[k, _fmt_idr(v)] for k, v in sorted(pillar_values.items(), key=lambda x: x[1], reverse=True)],
        [10 * cm, 6 * cm],
    ))
    story.append(Spacer(1, 0.4 * cm))

    # Opportunity detail
    story.append(Paragraph("Opportunity Detail", h2_style))
    detail_rows = [["Opportunity", "Customer", "AM", "Value", "Stage", "Prog."]]
    for d in sorted(deals, key=lambda x: x["estimated_value"], reverse=True):
        detail_rows.append([
            Paragraph(d["deal_name"], ParagraphStyle("s", parent=body_style, fontSize=7.5)),
            Paragraph(d["customer"], ParagraphStyle("s", parent=body_style, fontSize=7.5)),
            d["assigned_am"].split(" ")[0],
            _fmt_idr(d["estimated_value"]),
            d["stage"],
            f"{d['progress']}%",
        ])
    story.append(make_table(detail_rows, [5 * cm, 4 * cm, 2.2 * cm, 2.6 * cm, 2.2 * cm, 1.2 * cm]))
    story.append(Spacer(1, 0.4 * cm))

    # Strategy playbook — the AM's how-to-close per opportunity
    strat_deals = [d for d in deals if (d.get("strategy") or "").strip()]
    if strat_deals:
        story.append(Paragraph("Strategy &amp; How to Close", h2_style))
        small = ParagraphStyle("sm", parent=body_style, fontSize=8)
        strat_rows = [["Opportunity / AM", "Strategy to win &amp; close"]]
        for d in sorted(strat_deals, key=lambda x: x["assigned_am"]):
            label = f"<b>{d['deal_name']}</b><br/>{d['customer']} &middot; {d['assigned_am']}"
            strat_rows.append([Paragraph(label, small), Paragraph(d["strategy"], small)])
        story.append(make_table(strat_rows, [6 * cm, 10 * cm]))
        story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Recommendations for H2 Execution", h2_style))
    blocked = [d for d in deals if d["is_blocked"]]
    recs = [
        "Prioritize Negotiation-stage opportunities with the highest weighted value to accelerate close.",
        "Protect large device-bundling deals by locking fixed partner pricing and delivery timelines.",
        "Assign dedicated, skilled implementation PICs to the largest Enterprise Solutions pursuits.",
        "Maintain frequent customer engagement and manage expectations on CCTV & Vision projects.",
    ]
    if gap > 0:
        recs.insert(0, f"Portfolio is {_fmt_idr(gap)} short of the H2 target - sustain pipeline "
                       f"generation across all four Account Managers.")
    if blocked:
        recs.insert(1, f"{len(blocked)} opportunity(ies) blocked; assign executive sponsors this week.")
    for r in recs:
        story.append(Paragraph(f"&#8226; {r}", body_style))

    doc.build(story)
    buf.seek(0)
    filename = f"deal_tracker_report_{date.today().isoformat()}.pdf"
    return send_file(buf, mimetype="application/pdf", as_attachment=True, download_name=filename)


# --------------------------------------------------------------------------
# Bootstrap
# --------------------------------------------------------------------------
init_db()

if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
