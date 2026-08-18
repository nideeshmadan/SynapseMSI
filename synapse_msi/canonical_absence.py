"""Narrow absence semantics for canonical fields that treat exact zero as unavailable.

Only fields listed in ``ZERO_UNAVAILABLE_FIELDS`` use this helper. Unrelated
numeric fields keep ordinary numeric semantics (including legitimate zeros).

Exact Decimal equality is required — no tolerances, no float epsilon, and no
conversion of small nonzero values to zero.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, FrozenSet, Optional

# Canonical fields whose consensus / eligibility paths treat exact zero as absent.
# See specifications/reconstruction-standard.md and specifications/canonical-field-specification.md:
# mark_price_consensus and funding_rate_consensus exclude null and exact zero.
ZERO_UNAVAILABLE_FIELDS: FrozenSet[str] = frozenset(
    {
        "mark_price",
        "native_mark_price",
        "funding_rate",
    }
)


def parse_exact_decimal(value: Any) -> Optional[Decimal]:
    """Parse a scalar to Decimal, or return None when absent / unparsable."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, Decimal):
        return value
    text = str(value).strip()
    if text == "":
        return None
    try:
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return None


def is_exact_zero(value: Any) -> bool:
    """True only when value parses and equals Decimal(0) exactly."""
    parsed = parse_exact_decimal(value)
    return parsed is not None and parsed == 0


def canonical_nonzero_decimal(field: str, value: Any) -> Optional[Decimal]:
    """Return a nonzero Decimal for a zero-unavailable field, else None.

    For fields outside ``ZERO_UNAVAILABLE_FIELDS``, returns the parsed Decimal
    including exact zero (caller must not use this helper for ordinary fields
    that accept zero).
    """
    if field not in ZERO_UNAVAILABLE_FIELDS:
        raise ValueError(
            f"canonical_nonzero_decimal is scoped to {sorted(ZERO_UNAVAILABLE_FIELDS)}; "
            f"got {field!r}"
        )
    parsed = parse_exact_decimal(value)
    if parsed is None or parsed == 0:
        return None
    return parsed


def mark_price_available(value: Any) -> bool:
    """Whether a mark_price / native_mark_price value is eligible as native mark."""
    return canonical_nonzero_decimal("mark_price", value) is not None
