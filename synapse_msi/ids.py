"""Deterministic investigation identity helpers."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone


def _timestamp_to_iso(value: datetime) -> str:
    utc = value.astimezone(timezone.utc)
    return utc.strftime("%Y-%m-%dT%H:%M:%S") + (
        f".{utc.microsecond:06d}" if utc.microsecond else ""
    ) + "Z"


def _normalize_identity_timestamp(value: str | datetime) -> str:
    if isinstance(value, datetime):
        return _timestamp_to_iso(value)
    return str(value).strip()


def stable_investigation_id(
    instrument: str,
    start_timestamp: str | datetime,
    end_timestamp: str | datetime,
    cluster_id: str | None,
) -> str:
    """Deterministic investigation ID from operational episode identity fields."""
    payload = (
        f"{instrument}|"
        f"{_normalize_identity_timestamp(start_timestamp)}|"
        f"{_normalize_identity_timestamp(end_timestamp)}|"
        f"{cluster_id or ''}"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]
