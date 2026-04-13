#!/usr/bin/env python3
"""Hourly sync: growth.db + health.db -> andyOS PostgreSQL.

Reads from EC2 SQLite databases and POSTs rows to andyOS /api/sync/* endpoints.
Uses GROWTH_API_KEY for authentication. Idempotent -- safe to re-run.
"""
import sqlite3
import json
import os
import sys
import urllib.request
import urllib.error

API_BASE = "https://dashboard.andykaufman.net/api/sync"
API_KEY = os.environ.get("GROWTH_API_KEY", "")
GROWTH_DB = "/workspace/db/growth.db"
HEALTH_DB = "/workspace/db/health.db"

def sync_table(table_name, db_path, query, endpoint=None):
    """Read rows from SQLite, POST to andyOS sync endpoint."""
    endpoint = endpoint or table_name
    if not os.path.exists(db_path):
        print(f"SKIP {table_name}: {db_path} not found")
        return 0

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = [dict(r) for r in conn.execute(query).fetchall()]
    except Exception as e:
        print(f"ERROR {table_name}: {e}")
        conn.close()
        return 0
    conn.close()

    if not rows:
        print(f"SKIP {table_name}: 0 rows")
        return 0

    url = f"{API_BASE}/{endpoint}"
    data = json.dumps({"rows": rows}).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {API_KEY}")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            print(f"OK {table_name}: synced={result.get('synced', 0)} errors={len(result.get('errors', []))}")
            return result.get("synced", 0)
    except urllib.error.HTTPError as e:
        print(f"HTTP ERROR {table_name}: {e.code} {e.reason}")
        return 0
    except Exception as e:
        print(f"ERROR {table_name}: {e}")
        return 0

if __name__ == "__main__":
    if not API_KEY:
        print("ERROR: GROWTH_API_KEY not set")
        sys.exit(1)

    total = 0
    total += sync_table("habits", GROWTH_DB, "SELECT * FROM habits")
    total += sync_table("habit-logs", GROWTH_DB, "SELECT * FROM habit_logs", "habit-logs")
    total += sync_table("oura", HEALTH_DB, "SELECT * FROM health_snapshots", "oura")
    total += sync_table("commute-prompts", GROWTH_DB, "SELECT * FROM commute_prompts", "commute-prompts")
    total += sync_table("weekly-reviews", GROWTH_DB, "SELECT * FROM weekly_reviews", "weekly-reviews")

    print(f"TOTAL: {total} rows synced")
