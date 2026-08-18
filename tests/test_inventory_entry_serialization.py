"""Public inventory serialization does not emit internal archive locators."""

from __future__ import annotations

from synapse_msi.historical_corpus.inventory import (
    inventory_entry_to_dict,
    lookup_regime,
)


def _entry(regime_id: str):
    entry = lookup_regime(regime_id)
    assert entry is not None
    return entry


def test_inventory_entry_has_no_archive_locator_field():
    entry = _entry("binance.hybrid_book_reference.native_mark")
    assert not hasattr(entry, "archive_prefixes")
    serialized = inventory_entry_to_dict(entry)
    assert "archive_prefixes" not in serialized


def test_default_inventory_entry_to_dict_preserves_public_fields():
    entry = _entry("binance.hybrid_book_reference.native_mark")
    serialized = inventory_entry_to_dict(entry)
    for key in (
        "regime_id",
        "effective_start",
        "effective_end",
        "collector",
        "collector_service_name",
        "ingest_type",
        "transport",
        "field_provenance",
        "known_semantic_differences",
        "comparable_to",
        "venue",
        "classifier_label",
        "comparison_group",
        "current_production",
        "provenance_policy_version",
        "known_limitations",
        "methodology_version",
    ):
        assert key in serialized
    assert serialized["regime_id"] == entry.regime_id
    assert serialized["effective_start"] == entry.effective_start
    assert serialized["ingest_type"] == entry.ingest_type
