#!/usr/bin/env python3
"""Skill usage metrics tracking with SQLite time-series storage."""
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path.home() / ".claude" / "claudeception-metrics" / "skill-usage.db"

def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""CREATE TABLE IF NOT EXISTS usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        skill_name TEXT NOT NULL,
        project TEXT DEFAULT '',
        trigger_type TEXT DEFAULT 'auto'
    )""")
    conn.commit()
    return conn

def record_usage(skill_name, project="", trigger_type="auto"):
    conn = _connect()
    conn.execute(
        "INSERT INTO usage (timestamp, skill_name, project, trigger_type) VALUES (?, ?, ?, ?)",
        (datetime.now().isoformat(), skill_name, project, trigger_type),
    )
    conn.commit()
    conn.close()

def get_weekly_report():
    conn = _connect()
    cutoff = (datetime.now() - timedelta(days=7)).isoformat()
    rows = conn.execute(
        "SELECT skill_name, COUNT(*) as cnt FROM usage WHERE timestamp >= ? GROUP BY skill_name ORDER BY cnt DESC",
        (cutoff,),
    ).fetchall()
    conn.close()
    return rows

def get_usage_stats(days=30):
    conn = _connect()
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    rows = conn.execute(
        "SELECT skill_name, COUNT(*) as cnt FROM usage WHERE timestamp >= ? GROUP BY skill_name ORDER BY cnt DESC",
        (cutoff,),
    ).fetchall()
    total = sum(r[1] for r in rows)
    conn.close()
    if not rows:
        return {"total_uses": 0, "unique_skills": 0, "most_used": None, "least_used": None, "daily_average": 0.0}
    return {
        "total_uses": total,
        "unique_skills": len(rows),
        "most_used": rows[0][0],
        "least_used": rows[-1][0],
        "daily_average": round(total / days, 2),
    }

def _print_report():
    rows = get_weekly_report()
    if not rows:
        print("No usage data in the last 7 days.")
        return
    w = max(len(r[0]) for r in rows)
    print(f"{'Skill':<{w}}  Count")
    print(f"{'-'*w}  -----")
    for name, cnt in rows:
        print(f"{name:<{w}}  {cnt}")

def _print_stats(days):
    stats = get_usage_stats(days)
    if stats["total_uses"] == 0:
        print(f"No usage data in the last {days} days.")
        return
    print(f"Period:        last {days} days")
    print(f"Total uses:    {stats['total_uses']}")
    print(f"Unique skills: {stats['unique_skills']}")
    print(f"Most used:     {stats['most_used']}")
    print(f"Least used:    {stats['least_used']}")
    print(f"Daily average: {stats['daily_average']}")

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print("Usage: skill_metrics.py {record|report|stats} [args...]")
        sys.exit(1)
    cmd = args[0]
    if cmd == "record" and len(args) >= 2:
        record_usage(args[1], args[2] if len(args) > 2 else "", args[3] if len(args) > 3 else "auto")
        print(f"Recorded: {args[1]}")
    elif cmd == "report":
        _print_report()
    elif cmd == "stats":
        _print_stats(int(args[1]) if len(args) > 1 else 30)
    else:
        print("Usage: skill_metrics.py {record <skill> [project] [trigger]|report|stats [days]}")
        sys.exit(1)
