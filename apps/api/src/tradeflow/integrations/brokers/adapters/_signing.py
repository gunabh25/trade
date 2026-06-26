"""HMAC signing helpers for broker REST APIs."""

from __future__ import annotations

import hashlib
import hmac
import time
import urllib.parse
from typing import Any


def binance_sign_params(params: dict[str, Any], api_secret: str) -> dict[str, Any]:
    signed = {**params, "timestamp": int(time.time() * 1000)}
    query = urllib.parse.urlencode(signed)
    signature = hmac.new(
        api_secret.encode(),
        query.encode(),
        hashlib.sha256,
    ).hexdigest()
    signed["signature"] = signature
    return signed


def bybit_sign_headers(
    api_key: str,
    api_secret: str,
    *,
    payload: str,
    recv_window: int = 5000,
) -> dict[str, str]:
    timestamp = str(int(time.time() * 1000))
    sign_payload = f"{timestamp}{api_key}{recv_window}{payload}"
    signature = hmac.new(
        api_secret.encode(),
        sign_payload.encode(),
        hashlib.sha256,
    ).hexdigest()
    return {
        "X-BAPI-API-KEY": api_key,
        "X-BAPI-SIGN": signature,
        "X-BAPI-SIGN-TYPE": "2",
        "X-BAPI-TIMESTAMP": timestamp,
        "X-BAPI-RECV-WINDOW": str(recv_window),
    }
