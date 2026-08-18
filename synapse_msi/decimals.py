"""Decimal quantization utilities for deterministic precision."""

from decimal import Decimal, ROUND_HALF_UP

QUANTIZATION_RULES = {
    "price": 2,
    "funding_rate": 8,
    "oi_usd": 2,
    "spread_bps": 1,
    "price_change_bps": 1,
    "score": 2,
}


def quantize(value: Decimal, field_type: str) -> Decimal:
    places = QUANTIZATION_RULES.get(field_type, 2)
    quantizer = Decimal(10) ** -places
    return value.quantize(quantizer, rounding=ROUND_HALF_UP)


def quantize_price(value) -> str:
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    return str(quantize(value, "price"))


def quantize_funding_rate(value) -> str:
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    return str(quantize(value, "funding_rate"))


def quantize_bps(value) -> str:
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    return str(quantize(value, "spread_bps"))
