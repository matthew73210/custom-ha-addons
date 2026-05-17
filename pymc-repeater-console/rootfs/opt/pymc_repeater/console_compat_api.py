#!/usr/bin/env python3
"""Wrapper-owned compatibility API for pyMC Console graph data.

The upstream pyMC_Repeater API remains untouched.  This small local service
fills the Console graph/history routes from the add-on's persistent SQLite DB
and normalizes packet rows for the Console packet cache.
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
from collections import Counter, defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


DB_PATH = Path(os.environ.get("PYMC_REPEATER_DB", "/config/pymc-repeater/repeater.db"))
HOST = os.environ.get("PYMC_COMPAT_HOST", "127.0.0.1")
PORT = int(os.environ.get("PYMC_COMPAT_PORT", "8090"))


PACKET_COLUMNS = [
    "timestamp",
    "type",
    "route",
    "length",
    "rssi",
    "snr",
    "score",
    "transmitted",
    "is_duplicate",
    "drop_reason",
    "src_hash",
    "dst_hash",
    "path_hash",
    "header",
    "transport_codes",
    "payload",
    "payload_length",
    "tx_delay_ms",
    "packet_hash",
    "original_path",
    "forwarded_path",
    "raw_packet",
]


def now_ts() -> float:
    return time.time()


def json_loads_maybe(value: Any) -> Any:
    if not isinstance(value, str) or not value:
        return value
    try:
        parsed = json.loads(value)
    except Exception:
        return value
    return parsed


def normalize_bool(value: Any) -> bool:
    return bool(value)


def normalize_packet(row: sqlite3.Row) -> dict[str, Any]:
    packet = {key: row[key] for key in row.keys()}
    packet["transmitted"] = normalize_bool(packet.get("transmitted"))
    packet["is_duplicate"] = normalize_bool(packet.get("is_duplicate"))
    if "lbt_channel_busy" in packet:
        packet["lbt_channel_busy"] = normalize_bool(packet.get("lbt_channel_busy"))

    for key in ("original_path", "forwarded_path", "transport_codes"):
        packet[key] = json_loads_maybe(packet.get(key))

    if packet.get("packet_origin") is None:
        packet["packet_origin"] = "tx_forward" if packet.get("transmitted") else "rx"

    packet.setdefault("route_type", packet.get("route"))
    packet.setdefault("payload_type", packet.get("type"))
    return packet


def connect_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=5)
    conn.row_factory = sqlite3.Row
    return conn


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return bool(row)


def existing_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    if not table_exists(conn, table):
        return []
    return [row["name"] for row in conn.execute(f"PRAGMA table_info({table})")]


def packet_select_columns(conn: sqlite3.Connection) -> list[str]:
    available = set(existing_columns(conn, "packets"))
    return [column for column in PACKET_COLUMNS if column in available]


def read_packets(params: dict[str, list[str]], mode: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    limit = max(1, min(int(first(params, "limit", "1000")), 10000))
    offset = max(0, int(first(params, "offset", "0")))
    start = optional_float(first(params, "start_timestamp", None))
    end = optional_float(first(params, "end_timestamp", None))
    packet_type = optional_int(first(params, "type", None))
    route = optional_int(first(params, "route", None))

    if not DB_PATH.exists():
        return [], {"error": f"database missing at {DB_PATH}"}

    with connect_db() as conn:
        columns = packet_select_columns(conn)
        if not columns:
            return [], {"error": "packets table missing or empty schema"}

        where: list[str] = []
        values: list[Any] = []
        if mode == "recent":
            pass
        else:
            if start is not None:
                where.append("timestamp >= ?")
                values.append(start)
            if end is not None:
                where.append("timestamp <= ?")
                values.append(end)
            if packet_type is not None:
                where.append("type = ?")
                values.append(packet_type)
            if route is not None:
                where.append("route = ?")
                values.append(route)

        query = f"SELECT {', '.join(columns)} FROM packets"
        if where:
            query += " WHERE " + " AND ".join(where)
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        values.extend([limit, offset])

        rows = conn.execute(query, values).fetchall()
        packets = [normalize_packet(row) for row in rows]

    meta = {
        "limit": limit,
        "offset": offset,
        "start_timestamp": start,
        "end_timestamp": end,
        "type": packet_type,
        "route": route,
    }
    return packets, meta


def first(params: dict[str, list[str]], key: str, default: str | None) -> str | None:
    values = params.get(key)
    return values[0] if values else default


def optional_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def optional_int(value: str | None) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def packet_identity(value: Any) -> str | None:
    if not value:
        return None
    return str(value).strip()


def packet_path(packet: dict[str, Any]) -> list[str]:
    path = packet.get("forwarded_path") or packet.get("original_path") or []
    if isinstance(path, str):
        path = json_loads_maybe(path)
    if not isinstance(path, list):
        return []
    return [str(item).upper() for item in path if str(item).strip()]


def latest_packets_for_topology(hours: int = 336, limit: int = 50000) -> list[dict[str, Any]]:
    params = {
        "start_timestamp": [str(now_ts() - hours * 3600)],
        "end_timestamp": [str(now_ts())],
        "limit": [str(limit)],
    }
    packets, _ = read_packets(params, "bulk")
    return packets


def advert_nodes(conn: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    if not table_exists(conn, "adverts"):
        return {}
    result: dict[str, dict[str, Any]] = {}
    rows = conn.execute(
        """
        SELECT pubkey, node_name, is_repeater, latitude, longitude, last_seen, rssi, snr, advert_count
        FROM adverts
        ORDER BY last_seen DESC
        """
    ).fetchall()
    for row in rows:
        key = str(row["pubkey"])
        if key not in result:
            result[key] = dict(row)
    return result


def build_topology() -> dict[str, Any]:
    packets = latest_packets_for_topology()
    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[tuple[str, str], dict[str, Any]] = {}

    with connect_db() as conn:
        adverts = advert_nodes(conn)

    def ensure_node(node_id: str, packet: dict[str, Any] | None = None) -> dict[str, Any]:
        node = nodes.get(node_id)
        advert = adverts.get(node_id)
        if node is None:
            label = (advert or {}).get("node_name") or node_id[:8]
            node = {
                "id": node_id,
                "hash": node_id,
                "nodeHash": node_id,
                "prefix": node_id[:2].upper(),
                "label": label,
                "name": label,
                "packetCount": 0,
                "lastSeen": 0,
                "nodeClass": "standard",
                "isRepeater": bool((advert or {}).get("is_repeater")),
                "latitude": (advert or {}).get("latitude"),
                "longitude": (advert or {}).get("longitude"),
            }
            nodes[node_id] = node
        node["packetCount"] += 1 if packet else 0
        ts = packet.get("timestamp", 0) if packet else (advert or {}).get("last_seen", 0)
        if ts and ts > node.get("lastSeen", 0):
            node["lastSeen"] = ts
        return node

    def add_edge(left: str, right: str, packet: dict[str, Any]) -> None:
        if not left or not right or left == right:
            return
        key = (left, right) if left <= right else (right, left)
        edge = edges.get(key)
        if edge is None:
            edge = {
                "id": f"{key[0]}-{key[1]}",
                "key": f"{key[0]}-{key[1]}",
                "source": key[0],
                "target": key[1],
                "fromHash": key[0],
                "toHash": key[1],
                "packetCount": 0,
                "weight": 0,
                "avgRssi": None,
                "avgSnr": None,
                "lastSeen": 0,
            }
            edges[key] = edge
        edge["packetCount"] += 1
        edge["weight"] = edge["packetCount"]
        edge["lastSeen"] = max(edge["lastSeen"], packet.get("timestamp", 0) or 0)
        for metric, column in (("avgRssi", "rssi"), ("avgSnr", "snr")):
            value = packet.get(column)
            if value is not None:
                current = edge.get(metric)
                edge[metric] = value if current is None else (current + value) / 2

    for pubkey in adverts:
        ensure_node(pubkey)

    for packet in packets:
        src = packet_identity(packet.get("src_hash"))
        dst = packet_identity(packet.get("dst_hash"))
        path = packet_path(packet)
        chain = [item for item in [src, *path, dst] if item]
        for node_id in chain:
            ensure_node(node_id, packet)
        for left, right in zip(chain, chain[1:]):
            add_edge(left, right, packet)

    node_list = sorted(nodes.values(), key=lambda item: item.get("packetCount", 0), reverse=True)
    edge_list = sorted(edges.values(), key=lambda item: item.get("packetCount", 0), reverse=True)
    return {
        "success": True,
        "generated_at": now_ts(),
        "nodes": node_list,
        "edges": edge_list,
        "topology": {"nodes": node_list, "edges": edge_list},
        "summary": {
            "node_count": len(node_list),
            "edge_count": len(edge_list),
            "packet_count": len(packets),
            "db_path": str(DB_PATH),
        },
    }


def bucketed_stats(params: dict[str, list[str]]) -> dict[str, Any]:
    preset = first(params, "preset", "1h") or "1h"
    presets = {
        "15m": (15, 15),
        "1h": (60, 30),
        "3h": (180, 36),
        "24h": (1440, 96),
        "7d": (10080, 168),
    }
    minutes, bucket_count = presets.get(preset, presets["1h"])
    end_time = int(now_ts())
    bucket_seconds = max(1, int(minutes * 60 / bucket_count))
    start_time = end_time - bucket_seconds * bucket_count

    params_for_packets = {
        "start_timestamp": [str(start_time)],
        "end_timestamp": [str(end_time)],
        "limit": ["10000"],
    }
    packets, _ = read_packets(params_for_packets, "bulk")

    def empty_bucket(index: int) -> dict[str, Any]:
        start = start_time + index * bucket_seconds
        return {
            "bucket": index,
            "start": start,
            "end": start + bucket_seconds,
            "count": 0,
            "airtime_ms": 0,
            "avg_snr": 0,
            "avg_rssi": 0,
        }

    received = [empty_bucket(i) for i in range(bucket_count)]
    unique_received = [empty_bucket(i) for i in range(bucket_count)]
    transmitted = [empty_bucket(i) for i in range(bucket_count)]
    forwarded = [empty_bucket(i) for i in range(bucket_count)]
    dropped = [empty_bucket(i) for i in range(bucket_count)]
    seen_hashes: list[set[str]] = [set() for _ in range(bucket_count)]

    for packet in packets:
        ts = packet.get("timestamp") or 0
        index = int((ts - start_time) / bucket_seconds)
        if index < 0 or index >= bucket_count:
            continue
        length = packet.get("length") or packet.get("payload_length") or 0
        airtime_ms = max(0, float(length)) * 10
        origin = packet.get("packet_origin")
        if origin == "tx_local":
            target = transmitted[index]
        elif origin == "tx_forward" or packet.get("transmitted"):
            target = forwarded[index]
        elif packet.get("drop_reason"):
            target = dropped[index]
        else:
            target = received[index]
            packet_hash = packet.get("packet_hash")
            if packet_hash and packet_hash not in seen_hashes[index]:
                seen_hashes[index].add(packet_hash)
                unique_received[index]["count"] += 1
                unique_received[index]["airtime_ms"] += airtime_ms

        target["count"] += 1
        target["airtime_ms"] += airtime_ms
        if packet.get("snr") is not None:
            target["avg_snr"] = packet.get("snr")
        if packet.get("rssi") is not None:
            target["avg_rssi"] = packet.get("rssi")

    return {
        "success": True,
        "preset": preset,
        "time_range_minutes": minutes,
        "bucket_count": bucket_count,
        "bucket_duration_seconds": bucket_seconds,
        "start_time": start_time,
        "end_time": end_time,
        "received": received,
        "unique_received": unique_received,
        "transmitted": transmitted,
        "forwarded": forwarded,
        "dropped": dropped,
        "data": {
            "received": received,
            "unique_received": unique_received,
            "transmitted": transmitted,
            "forwarded": forwarded,
            "dropped": dropped,
        },
    }


def db_summary() -> dict[str, Any]:
    summary: dict[str, Any] = {"db_path": str(DB_PATH), "exists": DB_PATH.exists(), "tables": {}}
    if not DB_PATH.exists():
        return summary
    with connect_db() as conn:
        for table in ("packets", "adverts", "noise_floor", "crc_errors", "companion_contacts"):
            if table_exists(conn, table):
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                table_summary: dict[str, Any] = {"count": count}
                if "timestamp" in existing_columns(conn, table):
                    row = conn.execute(
                        f"SELECT MIN(timestamp) AS oldest, MAX(timestamp) AS newest FROM {table}"
                    ).fetchone()
                    table_summary["oldest"] = row["oldest"]
                    table_summary["newest"] = row["newest"]
                summary["tables"][table] = table_summary
    return summary


class Handler(BaseHTTPRequestHandler):
    server_version = "pyMCConsoleCompat/0.2"

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[compat-api] {self.address_string()} {fmt % args}", flush=True)

    def send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, separators=(",", ":"), default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def auth_present(self) -> bool:
        return bool(self.headers.get("Authorization") or parse_qs(urlparse(self.path).query).get("token"))

    def require_auth(self) -> bool:
        if self.auth_present():
            return True
        self.send_json(401, {"success": False, "error": "Unauthorized - Authorization header or token query required"})
        return False

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        path = parsed.path

        if path == "/health":
            self.send_json(200, {"success": True, "db": str(DB_PATH), "db_exists": DB_PATH.exists()})
            return

        if not self.require_auth():
            return

        try:
            if path == "/api/recent_packets":
                packets, meta = read_packets(params, "recent")
                self.send_json(200, {"success": True, "data": packets, "count": len(packets), **meta})
            elif path == "/api/bulk_packets":
                packets, meta = read_packets(params, "bulk")
                self.send_json(200, {"success": True, "data": packets, "count": len(packets), "compressed": False, **meta})
            elif path == "/api/filtered_packets":
                packets, meta = read_packets(params, "filtered")
                self.send_json(200, {"success": True, "data": packets, "count": len(packets), "filters": meta})
            elif path == "/api/analytics/topology":
                self.send_json(200, build_topology())
            elif path == "/api/analytics/bucketed_stats":
                self.send_json(200, bucketed_stats(params))
            elif path == "/api/analytics/disambiguation":
                topology = build_topology()
                prefixes = Counter(node["prefix"] for node in topology["nodes"])
                collisions = [prefix for prefix, count in prefixes.items() if count > 1]
                self.send_json(200, {
                    "success": True,
                    "totalPrefixes": len(prefixes),
                    "highCollisionPrefixes": collisions,
                    "collisionRate": len(collisions) / max(1, len(prefixes)),
                    "avgConfidence": 1.0,
                })
            elif path == "/api/analytics/last_hop_neighbors":
                topology = build_topology()
                neighbors = defaultdict(int)
                for edge in topology["edges"]:
                    neighbors[edge["fromHash"]] += edge["packetCount"]
                    neighbors[edge["toHash"]] += edge["packetCount"]
                self.send_json(200, {"success": True, "neighbors": dict(neighbors)})
            elif path == "/api/analytics/neighbor_affinity":
                self.send_json(200, {"success": True, "affinity": []})
            elif path == "/api/analytics/mobile_nodes":
                self.send_json(200, {"success": True, "nodes": []})
            elif path == "/api/analytics/path_health":
                self.send_json(200, {"success": True, "paths": []})
            elif path == "/api/analytics/tx_recommendations":
                self.send_json(200, {"success": True, "recommendations": []})
            elif path == "/api/analytics/sparklines":
                self.send_json(200, {"success": True, "sparklines": {}})
            elif path == "/api/analytics/debug":
                self.send_json(200, {"success": True, "auth_present": self.auth_present(), "db": db_summary()})
            else:
                self.send_json(404, {"success": False, "error": "Not found"})
        except Exception as exc:
            self.send_json(500, {"success": False, "error": str(exc)})


def main() -> None:
    print(f"[compat-api] starting on {HOST}:{PORT}, db={DB_PATH}", flush=True)
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
