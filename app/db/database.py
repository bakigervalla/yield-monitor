import sqlite3
from datetime import datetime, timedelta, time

DB_PATH = "yield_monitor.db"

ALLOWED_PART_NUMBERS = ["001PN001", "002PN002", "003PN003"]


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS manual_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            serial_number TEXT NOT NULL,
            part_number TEXT NOT NULL,
            timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            status BOOLEAN NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def insert_test(serial_number: str, part_number: str, status: bool) -> int:
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO manual_tests (serial_number, part_number, timestamp, status) VALUES (?, ?, ?, ?)",
        (serial_number, part_number, datetime.utcnow().isoformat(), int(status)),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def get_all_tests() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, serial_number, part_number, timestamp, status FROM manual_tests ORDER BY timestamp DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stats() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT part_number,
               COUNT(*) AS total,
               SUM(status) AS passed
        FROM manual_tests
        GROUP BY part_number
        """
    ).fetchall()
    conn.close()

    data = {r["part_number"]: dict(r) for r in rows}
    result = []
    for pn in ALLOWED_PART_NUMBERS:
        if pn in data:
            total = data[pn]["total"]
            passed = int(data[pn]["passed"] or 0)
            failed = total - passed
            yield_pct = round(passed / total * 100, 1) if total > 0 else 0.0
        else:
            total = 0
            passed = 0
            failed = 0
            yield_pct = 0.0
        result.append({
            "part_number": pn,
            "total": total,
            "passed": passed,
            "failed": failed,
            "yield_percent": yield_pct,
        })
    return result


def get_stats_for_date(date: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT part_number,
               COUNT(*) AS total,
               SUM(status) AS passed
        FROM manual_tests
        WHERE DATE(timestamp) = ?
        GROUP BY part_number
        """,
        (date,)
    ).fetchall()
    conn.close()

    data = {r["part_number"]: dict(r) for r in rows}
    result = []
    for pn in ALLOWED_PART_NUMBERS:
        if pn in data:
            total = data[pn]["total"]
            passed = int(data[pn]["passed"] or 0)
            failed = total - passed
            yield_pct = round(passed / total * 100, 1) if total > 0 else 0.0
        else:
            total = 0
            passed = 0
            failed = 0
            yield_pct = 0.0
        result.append({
            "part_number": pn,
            "total": total,
            "passed": passed,
            "failed": failed,
            "yield_percent": yield_pct,
        })
    return result


def seed_db():
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM manual_tests").fetchone()[0]
    if count > 0:
        conn.close()
        return

    today = datetime.utcnow().date()
    day_plans = [
        {"001PN001": (2, 1), "002PN002": (3, 0), "003PN003": (1, 1)},
        {"001PN001": (3, 0), "002PN002": (4, 0), "003PN003": (2, 1)},
        {"001PN001": (2, 1), "002PN002": (3, 1), "003PN003": (1, 1)},
        {"001PN001": (3, 0), "002PN002": (4, 0), "003PN003": (1, 2)},
        {"001PN001": (2, 1), "002PN002": (3, 0), "003PN003": (2, 1)},
        {"001PN001": (3, 0), "002PN002": (3, 1), "003PN003": (2, 1)},
        {"001PN001": (1, 1), "002PN002": (3, 0), "003PN003": (2, 2)},
    ]
    serial_prefixes = {
        "001PN001": "SN-A",
        "002PN002": "SN-B",
        "003PN003": "SN-C",
    }
    serial_counts = {part_number: 1 for part_number in ALLOWED_PART_NUMBERS}
    records = []

    for day_index, plan in enumerate(day_plans):
        record_date = today - timedelta(days=6 - day_index)
        timestamp = datetime.combine(record_date, time(hour=8))

        for part_number in ALLOWED_PART_NUMBERS:
            passed_count, failed_count = plan[part_number]
            statuses = [True] * passed_count + [False] * failed_count

            for status in statuses:
                serial_number = f"{serial_prefixes[part_number]}{serial_counts[part_number]:03d}"
                records.append((serial_number, part_number, status, timestamp))
                serial_counts[part_number] += 1
                timestamp += timedelta(minutes=17)

    conn.executemany(
        "INSERT INTO manual_tests (serial_number, part_number, timestamp, status) VALUES (?, ?, ?, ?)",
        [(sn, pn, ts.isoformat(), int(st)) for sn, pn, st, ts in records],
    )
    conn.commit()
    conn.close()


def get_daily() -> list[dict]:
    conn = get_connection()
    today = datetime.utcnow().date()
    days = [(today - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]

    rows = conn.execute(
        """
        SELECT DATE(timestamp) AS date, COUNT(*) AS count
        FROM manual_tests
        WHERE DATE(timestamp) >= DATE('now', '-6 days')
        GROUP BY DATE(timestamp)
        """
    ).fetchall()
    conn.close()

    counts = {r["date"]: r["count"] for r in rows}
    return [{"date": d, "count": counts.get(d, 0)} for d in days]
