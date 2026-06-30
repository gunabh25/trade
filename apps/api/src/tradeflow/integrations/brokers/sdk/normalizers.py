"""Normalize broker-specific WebSocket payloads into TradeFlow stream events."""

from __future__ import annotations

from typing import Any


def normalize_order_event(broker: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Map broker order update to `{type: order, ...}`."""
    if broker == "binance":
        event = payload.get("e")
        if event == "executionReport":
            return {
                "type": "order",
                "broker": broker,
                "order_id": str(payload.get("i", "")),
                "symbol": str(payload.get("s", "")),
                "side": str(payload.get("S", "")).lower(),
                "status": str(payload.get("X", "")).lower(),
                "quantity": payload.get("q"),
                "filled_quantity": payload.get("z"),
                "raw": payload,
            }
    if broker == "bybit":
        topic = str(payload.get("topic", ""))
        if topic.startswith("order"):
            data = payload.get("data")
            row = data[0] if isinstance(data, list) and data else data or {}
            if isinstance(row, dict):
                return {
                    "type": "order",
                    "broker": broker,
                    "order_id": str(row.get("orderId", "")),
                    "symbol": str(row.get("symbol", "")),
                    "side": str(row.get("side", "")).lower(),
                    "status": str(row.get("orderStatus", "")).lower(),
                    "quantity": row.get("qty"),
                    "filled_quantity": row.get("cumExecQty"),
                    "raw": payload,
                }
    if broker == "tradingview" and payload.get("type") == "order":
        return payload
    if payload.get("type") == "order":
        return payload
    return {"type": "order", "broker": broker, "raw": payload}


def normalize_position_event(broker: str, payload: dict[str, Any]) -> dict[str, Any]:
    if broker == "bybit":
        topic = str(payload.get("topic", ""))
        if topic.startswith("position"):
            data = payload.get("data")
            row = data[0] if isinstance(data, list) and data else data or {}
            if isinstance(row, dict):
                return {
                    "type": "position",
                    "broker": broker,
                    "symbol": str(row.get("symbol", "")),
                    "side": str(row.get("side", "")).lower(),
                    "quantity": row.get("size"),
                    "entry_price": row.get("avgPrice"),
                    "mark_price": row.get("markPrice"),
                    "unrealized_pnl": row.get("unrealisedPnl"),
                    "raw": payload,
                }
    if payload.get("type") == "position":
        return payload
    return {"type": "position", "broker": broker, "raw": payload}


def normalize_market_event(broker: str, payload: dict[str, Any]) -> dict[str, Any]:
    if broker == "binance":
        if payload.get("e") == "trade":
            return {
                "type": "quote",
                "broker": broker,
                "symbol": str(payload.get("s", "")),
                "price": payload.get("p"),
                "quantity": payload.get("q"),
                "timestamp": payload.get("T"),
                "raw": payload,
            }
        stream = payload.get("stream")
        data = payload.get("data", payload)
        if isinstance(data, dict) and data.get("e") == "trade":
            return normalize_market_event(broker, data)
        if stream and isinstance(data, dict):
            return normalize_market_event(broker, data)
    if broker == "bybit":
        topic = str(payload.get("topic", ""))
        if "tickers" in topic or "publicTrade" in topic:
            data = payload.get("data")
            row = data if isinstance(data, dict) else {}
            return {
                "type": "quote",
                "broker": broker,
                "symbol": str(row.get("symbol", "")),
                "price": row.get("lastPrice") or row.get("price"),
                "timestamp": row.get("ts") or payload.get("ts"),
                "raw": payload,
            }
    if payload.get("type") in {"quote", "market"}:
        return payload
    return {"type": "quote", "broker": broker, "raw": payload}
