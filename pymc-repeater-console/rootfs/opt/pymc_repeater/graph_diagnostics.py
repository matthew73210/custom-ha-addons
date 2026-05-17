#!/usr/bin/env python3
"""Authenticated graph/API diagnostics for the add-on startup log."""

from __future__ import annotations

import json
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


OPTIONS_PATH = Path("/data/options.json")
DB_PATH = Path("/config/pymc-repeater/repeater.db")
BACKEND_BASE = "http://127.0.0.1:8001"
DIRECT_BASE = "http://127.0.0.1:8000"
INGRESS_BASE = "http://127.0.0.1:8080"


ENDPOINTS = [
    "/api/stats",
    "/api/recent_packets?limit=5",
    "/api/bulk_packets?limit=5&start_timestamp=0&end_timestamp=4102444800",
    "/api/filtered_packets?limit=5",
    "/api/packet_type_graph_data?hours=24&resolution=average&types=all",
    "/api/metrics_graph_data?hours=24&resolution=average&metrics=rx_count,tx_count",
    "/api/noise_floor_history?hours=24",
    "/api/analytics/topology",
    "/api/analytics/bucketed_stats?preset=1h",
    "/api/analytics/debug",
]


def load_password() -> str:
    try:
        options = json.loads(OPTIONS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return ""
    return str(options.get("admin_password") or "")


def request_json(url: str, token: str | None = None, method: str = "GET", payload: dict[str, Any] | None = None) -> tuple[int, dict[str, str], Any]:
    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            raw = response.read()
            status = response.getcode()
            response_headers = dict(response.headers.items())
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        status = exc.code
        response_headers = dict(exc.headers.items())
    if not raw:
        return status, response_headers, None
    try:
        return status, response_headers, json.loads(raw.decode("utf-8", errors="replace"))
    except Exception:
        return status, response_headers, raw.decode("utf-8", errors="replace")[:500]


def login() -> str | None:
    password = load_password()
    if not password:
        print("auth: admin_password unavailable; authenticated graph probes skipped")
        return None
    payload = {"username": "admin", "password": password, "client_id": "wrapper-graph-diagnostics"}
    status, _, data = request_json(f"{BACKEND_BASE}/auth/login", method="POST", payload=payload)
    if status != 200 or not isinstance(data, dict) or not data.get("token"):
        error = data.get("error") if isinstance(data, dict) else data
        print(f"auth: login failed status={status} error={error}")
        return None
    print("auth: login succeeded; JWT acquired for graph probes")
    return str(data["token"])


def summarize_payload(data: Any) -> str:
    if not isinstance(data, dict):
        return f"type={type(data).__name__}"
    parts = []
    if "success" in data:
        parts.append(f"success={data.get('success')}")
    if "count" in data:
        parts.append(f"count={data.get('count')}")
    if isinstance(data.get("data"), list):
        parts.append(f"data_len={len(data['data'])}")
        if data["data"]:
            parts.append("data_keys=" + ",".join(sorted(data["data"][0].keys())[:12]))
    if isinstance(data.get("nodes"), list):
        parts.append(f"nodes={len(data['nodes'])}")
    if isinstance(data.get("edges"), list):
        parts.append(f"edges={len(data['edges'])}")
    if isinstance(data.get("received"), list):
        parts.append(f"received_buckets={len(data['received'])}")
        parts.append(f"received_count={sum(item.get('count', 0) for item in data['received'])}")
    if isinstance(data.get("forwarded"), list):
        parts.append(f"forwarded_count={sum(item.get('count', 0) for item in data['forwarded'])}")
    if isinstance(data.get("db"), dict):
        tables = data["db"].get("tables", {})
        parts.append("db_tables=" + ",".join(f"{k}:{v.get('count')}" for k, v in tables.items()))
    if "error" in data:
        parts.append(f"error={data.get('error')}")
    return " ".join(parts) if parts else "keys=" + ",".join(sorted(data.keys())[:16])


def db_summary() -> None:
    print(f"db: path={DB_PATH} exists={DB_PATH.exists()}")
    if not DB_PATH.exists():
        return
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            for table in ("packets", "adverts", "noise_floor", "companion_contacts"):
                exists = conn.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                    (table,),
                ).fetchone()
                if not exists:
                    continue
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                range_info = ""
                columns = [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]
                if "timestamp" in columns:
                    oldest, newest = conn.execute(
                        f"SELECT MIN(timestamp), MAX(timestamp) FROM {table}"
                    ).fetchone()
                    range_info = f" oldest={oldest} newest={newest}"
                print(f"db: {table} count={count}{range_info}")
    except Exception as exc:
        print(f"db: summary failed: {exc}")


def probe_endpoint(token: str, path: str) -> None:
    rows = []
    for label, base in (("backend", BACKEND_BASE), ("direct", DIRECT_BASE), ("ingress", INGRESS_BASE)):
        status, headers, data = request_json(base + path, token=token)
        content_type = headers.get("Content-Type", "")
        rows.append((label, status, content_type, summarize_payload(data)))
    direct = rows[1]
    ingress = rows[2]
    parity = "match" if direct[1:] == ingress[1:] else "diff"
    print(f"probe: {path}")
    for label, status, content_type, summary in rows:
        print(f"probe:   {label} status={status} content_type={content_type} {summary}")
    print(f"probe:   direct_vs_ingress={parity}")


def main() -> int:
    db_summary()
    token = login()
    if not token:
        return 0
    for path in ENDPOINTS:
        try:
            probe_endpoint(token, path)
        except Exception as exc:
            print(f"probe: {path} failed: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
