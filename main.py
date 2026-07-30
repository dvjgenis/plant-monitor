from contextlib import contextmanager
from datetime import date, datetime
import csv
import json
import logging
import os
import re
import secrets
import sqlite3

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI(title="Plant Hydration Hub")

logger = logging.getLogger("plant-monitor")

DB_NAME = "plants.db"
CSV_NAME = "readings.csv"
PLANT_API_KEY = os.environ.get("PLANT_API_KEY", "").strip()
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "").strip()
VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "").strip()
VAPID_CONTACT = os.environ.get("VAPID_CONTACT", "mailto:plant-monitor@localhost").strip()
DRY_THRESHOLD = 20.0
CSV_HEADERS = [
    "timestamp",
    "plant_id",
    "plant_name",
    "raw_value",
    "moisture_percentage",
    "status_category",
]

# Friendly labels for known plant IDs (extend as you add sensors)
PLANT_NAMES = {
    1: "Gynura Aurantiaca",
    2: "Plant #2",
}

# Browser push subscribe/unsubscribe from the home PWA (no ESP32 key)
PUSH_OPEN_PATHS = {
    "/api/push/subscribe",
    "/api/push/unsubscribe",
}


def get_moisture_category(percentage: float) -> str:
    if percentage <= 20.0:
        return "Dry"
    if percentage <= 50.0:
        return "Moist"
    if percentage <= 80.0:
        return "Optimal"
    return "Soggy"


def plant_name(plant_id: int) -> str:
    return PLANT_NAMES.get(plant_id, f"Plant #{plant_id}")


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_sqlite_db():
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plant_id INTEGER NOT NULL,
                raw_value INTEGER NOT NULL,
                moisture_percentage REAL NOT NULL,
                status_category TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(readings)")}
        if "status_category" not in columns:
            conn.execute(
                "ALTER TABLE readings ADD COLUMN status_category TEXT NOT NULL DEFAULT 'Unknown'"
            )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS push_subscriptions (
                endpoint TEXT PRIMARY KEY,
                p256dh TEXT NOT NULL,
                auth TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS dry_alerts (
                plant_id INTEGER PRIMARY KEY,
                alerted_at TEXT NOT NULL
            )
            """
        )


def append_csv_reading(
    *,
    timestamp: str,
    plant_id: int,
    raw_value: int,
    moisture_percentage: float,
    status_category: str,
):
    """Append one reading to readings.csv (creates file + header if needed)."""
    write_header = not os.path.exists(CSV_NAME) or os.path.getsize(CSV_NAME) == 0
    with open(CSV_NAME, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        if write_header:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp": timestamp,
                "plant_id": plant_id,
                "plant_name": plant_name(plant_id),
                "raw_value": raw_value,
                "moisture_percentage": f"{moisture_percentage:.1f}",
                "status_category": status_category,
            }
        )


def reset_csv_file():
    """Rewrite readings.csv with only the header row."""
    with open(CSV_NAME, "w", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=CSV_HEADERS).writeheader()


def rebuild_csv_from_db() -> None:
    """Rewrite readings.csv from SQLite (repairs desync after failed append)."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT plant_id, raw_value, moisture_percentage, status_category, timestamp
            FROM readings
            ORDER BY id ASC
            """
        ).fetchall()

    reset_csv_file()
    for row in rows:
        append_csv_reading(
            timestamp=row["timestamp"],
            plant_id=row["plant_id"],
            raw_value=row["raw_value"],
            moisture_percentage=row["moisture_percentage"],
            status_category=row["status_category"],
        )


def sync_csv_from_db():
    """If CSV is missing/empty, export everything currently in SQLite."""
    if os.path.exists(CSV_NAME) and os.path.getsize(CSV_NAME) > 0:
        return

    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT plant_id, raw_value, moisture_percentage, status_category, timestamp
            FROM readings
            ORDER BY id ASC
            """
        ).fetchall()

    reset_csv_file()
    for row in rows:
        append_csv_reading(
            timestamp=row["timestamp"],
            plant_id=row["plant_id"],
            raw_value=row["raw_value"],
            moisture_percentage=row["moisture_percentage"],
            status_category=row["status_category"],
        )


init_sqlite_db()
sync_csv_from_db()


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Require X-API-Key on mutating /api/* routes when PLANT_API_KEY is set.

    GET stays open so the home dashboard (plant-pi.local) works without a key.
    POST/DELETE still need the key so random internet clients cannot spam or wipe.
    Push subscribe/unsubscribe stay open for the local PWA.
    """

    MUTATING = {"POST", "PUT", "PATCH", "DELETE"}

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if (
            PLANT_API_KEY
            and path.startswith("/api/")
            and path not in PUSH_OPEN_PATHS
            and request.method.upper() in self.MUTATING
        ):
            provided = request.headers.get("X-API-Key", "")
            if not secrets.compare_digest(provided, PLANT_API_KEY):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid or missing API key"},
                )
        return await call_next(request)


app.add_middleware(ApiKeyMiddleware)


class SensorData(BaseModel):
    plant_id: int = Field(ge=1)
    raw_value: int
    moisture_percentage: float = Field(ge=0, le=100)


class PushKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscriptionIn(BaseModel):
    endpoint: str = Field(min_length=8)
    keys: PushKeys


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def push_configured() -> bool:
    return bool(VAPID_PRIVATE_KEY and VAPID_PUBLIC_KEY)


def send_web_push(title: str, body: str, url: str = "/") -> dict:
    """Send a Web Push payload to every stored subscription."""
    if not push_configured():
        return {"sent": 0, "failed": 0, "removed": 0, "configured": False}

    try:
        from pywebpush import webpush
    except ImportError:
        logger.error("pywebpush is not installed; cannot send push notifications")
        return {"sent": 0, "failed": 0, "removed": 0, "configured": False}

    payload = json.dumps({"title": title, "body": body, "url": url})
    with get_db() as conn:
        subs = conn.execute(
            "SELECT endpoint, p256dh, auth FROM push_subscriptions"
        ).fetchall()

    sent = failed = removed = 0
    for sub in subs:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub["endpoint"],
                    "keys": {"p256dh": sub["p256dh"], "auth": sub["auth"]},
                },
                data=payload,
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims={"sub": VAPID_CONTACT},
            )
            sent += 1
        except Exception as exc:
            status = None
            response = getattr(exc, "response", None)
            status = getattr(response, "status_code", None)
            if status in (404, 410):
                with get_db() as conn:
                    conn.execute(
                        "DELETE FROM push_subscriptions WHERE endpoint = ?",
                        (sub["endpoint"],),
                    )
                removed += 1
                logger.info("Removed expired push subscription")
            else:
                failed += 1
                logger.warning("Web push failed: %s", exc)

    return {
        "sent": sent,
        "failed": failed,
        "removed": removed,
        "configured": True,
        "subscribers": len(subs),
    }


def maybe_notify_dry(plant_id: int, moisture_percentage: float, category: str) -> None:
    """Alert once when a plant enters Dry; clear latch when it recovers."""
    name = plant_name(plant_id)

    with get_db() as conn:
        if category != "Dry":
            conn.execute("DELETE FROM dry_alerts WHERE plant_id = ?", (plant_id,))
            return

        already = conn.execute(
            "SELECT 1 FROM dry_alerts WHERE plant_id = ?",
            (plant_id,),
        ).fetchone()
        if already:
            return

        conn.execute(
            "INSERT INTO dry_alerts (plant_id, alerted_at) VALUES (?, ?)",
            (plant_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )

    if not push_configured():
        logger.info(
            "Plant #%s is Dry (%.1f%%) but VAPID keys are not configured",
            plant_id,
            moisture_percentage,
        )
        return

    result = send_web_push(
        title="Plant needs water",
        body=f"{name} is Dry ({moisture_percentage:.1f}% ≤ {DRY_THRESHOLD:.0f}%)",
        url="/",
    )
    print(
        f"Dry alert for {name}: push sent={result.get('sent', 0)} "
        f"failed={result.get('failed', 0)}"
    )


def parse_day(value: str | None) -> str:
    """Return YYYY-MM-DD, defaulting to today. Raises 400 if invalid."""
    if value is None or value.strip() == "":
        return date.today().isoformat()
    value = value.strip()
    if not DATE_RE.match(value):
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid calendar date") from exc
    return value


def parse_timestamp(ts: str) -> datetime:
    """Parse SQLite / ISO timestamps without raising on minor format drift."""
    text = (ts or "").strip()
    if not text:
        return datetime.now()

    normalized = text.replace("Z", "").split("+")[0].strip()
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        pass

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue

    logger.warning("Could not parse timestamp %r; using now()", text)
    return datetime.now()


def format_timestamp(ts: str) -> dict:
    """Parse SQLite timestamp into display fields for the UI."""
    dt = parse_timestamp(ts)
    canonical = dt.strftime("%Y-%m-%d %H:%M:%S")
    return {
        "time_of_day": dt.strftime("%H:%M"),
        "hour_label": dt.strftime("%H:00"),
        "hour_fraction": dt.hour + dt.minute / 60.0 + dt.second / 3600.0,
        "full_timestamp": canonical,
        "iso_timestamp": dt.isoformat(),
        "date": dt.date().isoformat(),
    }


@app.get("/api/plants")
def list_plants():
    """Latest reading for every plant that has sent data."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT r.plant_id, r.raw_value, r.moisture_percentage,
                   r.status_category, r.timestamp
            FROM readings r
            INNER JOIN (
                SELECT plant_id, MAX(id) AS max_id
                FROM readings
                GROUP BY plant_id
            ) latest ON r.id = latest.max_id
            ORDER BY r.plant_id
            """
        ).fetchall()

    plants = []
    for row in rows:
        plants.append(
            {
                "plant_id": row["plant_id"],
                "name": plant_name(row["plant_id"]),
                "raw_value": row["raw_value"],
                "moisture_percentage": row["moisture_percentage"],
                "status_category": row["status_category"],
                **format_timestamp(row["timestamp"]),
            }
        )
    return {"plants": plants}


@app.post("/api/moisture")
def receive_moisture(data: SensorData):
    category = get_moisture_category(data.moisture_percentage)

    # Store local wall-clock time so the dashboard matches the room clock
    local_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO readings (
                plant_id, raw_value, moisture_percentage, status_category, timestamp
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                data.plant_id,
                data.raw_value,
                data.moisture_percentage,
                category,
                local_ts,
            ),
        )

    try:
        append_csv_reading(
            timestamp=local_ts,
            plant_id=data.plant_id,
            raw_value=data.raw_value,
            moisture_percentage=data.moisture_percentage,
            status_category=category,
        )
    except OSError as exc:
        logger.error("CSV append failed; rebuilding from DB: %s", exc)
        rebuild_csv_from_db()

    now = datetime.now().strftime("%H:%M")
    print(
        f"[{now}] Saved Plant #{data.plant_id} | "
        f"{data.moisture_percentage:.1f}% ({category})"
    )
    maybe_notify_dry(data.plant_id, data.moisture_percentage, category)
    return {"status": "success", "category": category}


@app.get("/api/plants/{plant_id}/history")
def get_plant_history(
    plant_id: int,
    day: str | None = Query(None, description="YYYY-MM-DD (defaults to today)"),
):
    selected_day = parse_day(day)
    today = date.today().isoformat()

    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT raw_value, moisture_percentage, status_category, timestamp
            FROM readings
            WHERE plant_id = ?
              AND date(timestamp) = ?
            ORDER BY timestamp ASC
            """,
            (plant_id, selected_day),
        ).fetchall()

        day_rows = conn.execute(
            """
            SELECT date(timestamp) AS day, COUNT(*) AS reading_count
            FROM readings
            WHERE plant_id = ?
            GROUP BY date(timestamp)
            ORDER BY day DESC
            """,
            (plant_id,),
        ).fetchall()

    history = [
        {
            "raw_value": row["raw_value"],
            "moisture_percentage": row["moisture_percentage"],
            "status_category": row["status_category"],
            **format_timestamp(row["timestamp"]),
        }
        for row in rows
    ]

    return {
        "plant_id": plant_id,
        "name": plant_name(plant_id),
        "day": selected_day,
        "today": today,
        "is_today": selected_day == today,
        "history": history,
        "available_days": [
            {"date": row["day"], "reading_count": row["reading_count"]}
            for row in day_rows
        ],
    }


@app.delete("/api/readings")
def wipe_readings():
    """Delete every stored reading so you can start clean."""
    with get_db() as conn:
        deleted = conn.execute("SELECT COUNT(*) AS n FROM readings").fetchone()["n"]
        conn.execute("DELETE FROM readings")
        conn.execute("DELETE FROM dry_alerts")
        try:
            conn.execute("DELETE FROM sqlite_sequence WHERE name = 'readings'")
        except sqlite3.OperationalError:
            # sqlite_sequence only exists after AUTOINCREMENT has been used
            pass
    reset_csv_file()
    print(f"Wiped {deleted} reading(s) from plants.db and {CSV_NAME}")
    return {"status": "success", "deleted": deleted}


@app.get("/api/push/status")
def push_status():
    """Whether Web Push is configured and how many devices are subscribed."""
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) AS n FROM push_subscriptions").fetchone()[
            "n"
        ]
    return {
        "configured": push_configured(),
        "subscribers": count,
        "dry_threshold": DRY_THRESHOLD,
        "secure_context_required": True,
    }


@app.get("/api/push/vapid-public-key")
def vapid_public_key():
    if not VAPID_PUBLIC_KEY:
        raise HTTPException(
            status_code=503,
            detail="Web Push is not configured on the Pi (missing VAPID_PUBLIC_KEY)",
        )
    return {"publicKey": VAPID_PUBLIC_KEY}


@app.post("/api/push/subscribe")
def push_subscribe(sub: PushSubscriptionIn):
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO push_subscriptions (endpoint, p256dh, auth, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(endpoint) DO UPDATE SET
                p256dh = excluded.p256dh,
                auth = excluded.auth,
                created_at = excluded.created_at
            """,
            (
                sub.endpoint,
                sub.keys.p256dh,
                sub.keys.auth,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
    return {"status": "subscribed"}


@app.post("/api/push/unsubscribe")
def push_unsubscribe(sub: PushSubscriptionIn):
    with get_db() as conn:
        conn.execute(
            "DELETE FROM push_subscriptions WHERE endpoint = ?",
            (sub.endpoint,),
        )
    return {"status": "unsubscribed"}


@app.post("/api/push/test")
def push_test():
    """Send a test notification to all subscribers (requires API key when set)."""
    if not push_configured():
        raise HTTPException(status_code=503, detail="VAPID keys are not configured")
    result = send_web_push(
        title="Plant Hydration Hub",
        body="Test alert — push notifications are working.",
        url="/",
    )
    return {"status": "ok", **result}


@app.get("/api/readings.csv")
def download_readings_csv():
    """Download the CSV log of all readings."""
    if not os.path.exists(CSV_NAME):
        reset_csv_file()
    return FileResponse(
        CSV_NAME,
        media_type="text/csv",
        filename="readings.csv",
    )


@app.get("/sw.js")
def service_worker():
    return FileResponse(
        "static/sw.js",
        media_type="application/javascript; charset=utf-8",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Service-Worker-Allowed": "/",
        },
    )


@app.get("/")
def read_index():
    return FileResponse(
        "static/index.html",
        media_type="text/html",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


# Mount after API routes so /static does not shadow them
app.mount("/static", StaticFiles(directory="static"), name="static")
