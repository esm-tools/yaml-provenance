"""
Tests for ProvenanceConfig and configure().
"""

import pytest

from yaml_provenance import (
    ProvenanceConfig,
    configure,
    get_config,
    DictWithProvenance,
    CategoryConflictError,
    wrapper_with_provenance_factory,
)


def test_default_config():
    configure(None)
    config = get_config()
    assert config.category_hierarchy == [None]
    assert config.on_conflict == "raise"
    assert config.track_history is False
    assert config.custom_type_handlers == {}
    assert config.conflict_resolver is None


def test_configure_sets_global():
    custom = ProvenanceConfig(track_history=True, on_conflict="warn")
    configure(custom)
    assert get_config() is custom
    configure(None)


def test_custom_hierarchy_raises_on_conflict():
    configure(ProvenanceConfig(
        category_hierarchy=[None, "low", "high"],
        on_conflict="raise",
        track_history=True,
    ))

    d = DictWithProvenance(
        {"key": "old_value"},
        {"key": {"line": 1, "col": 1, "category": "low"}},
    )
    new_val = wrapper_with_provenance_factory(
        "new_value",
        {"line": 2, "col": 1, "category": "low"},
    )

    with pytest.raises(CategoryConflictError) as exc_info:
        d["key"] = new_val

    assert exc_info.value.key == "key"
    assert exc_info.value.category == "low"


def test_custom_hierarchy_higher_overwrites():
    configure(ProvenanceConfig(
        category_hierarchy=[None, "low", "high"],
        track_history=True,
    ))

    d = DictWithProvenance(
        {"key": "old_value"},
        {"key": {"line": 1, "col": 1, "category": "low"}},
    )
    new_val = wrapper_with_provenance_factory(
        "new_value",
        {"line": 2, "col": 1, "category": "high"},
    )

    d["key"] = new_val
    assert d["key"] == "new_value"


def test_custom_hierarchy_lower_keeps_old():
    configure(ProvenanceConfig(
        category_hierarchy=[None, "low", "high"],
        track_history=True,
    ))

    d = DictWithProvenance(
        {"key": "old_value"},
        {"key": {"line": 1, "col": 1, "category": "high"}},
    )
    new_val = wrapper_with_provenance_factory(
        "new_value",
        {"line": 2, "col": 1, "category": "low"},
    )

    d["key"] = new_val
    assert d["key"] == "old_value"


def test_on_conflict_warn(capfd):
    configure(ProvenanceConfig(
        category_hierarchy=[None, "same"],
        on_conflict="warn",
        track_history=True,
    ))

    d = DictWithProvenance(
        {"key": "old"},
        {"key": {"line": 1, "col": 1, "category": "same"}},
    )
    new_val = wrapper_with_provenance_factory(
        "new",
        {"line": 2, "col": 1, "category": "same"},
    )

    # Should not raise
    d["key"] = new_val
    assert d["key"] == "new"


def test_on_conflict_ignore():
    configure(ProvenanceConfig(
        category_hierarchy=[None, "same"],
        on_conflict="ignore",
        track_history=True,
    ))

    d = DictWithProvenance(
        {"key": "old"},
        {"key": {"line": 1, "col": 1, "category": "same"}},
    )
    new_val = wrapper_with_provenance_factory(
        "new",
        {"line": 2, "col": 1, "category": "same"},
    )

    d["key"] = new_val
    assert d["key"] == "new"


def test_custom_conflict_resolver():
    def always_keep_old(key, old_val, new_val, old_prov, new_prov):
        return "keep_old"

    configure(ProvenanceConfig(
        category_hierarchy=[None, "same"],
        conflict_resolver=always_keep_old,
        track_history=True,
    ))

    d = DictWithProvenance(
        {"key": "old"},
        {"key": {"line": 1, "col": 1, "category": "same"}},
    )
    new_val = wrapper_with_provenance_factory(
        "new",
        {"line": 2, "col": 1, "category": "same"},
    )

    d["key"] = new_val
    assert d["key"] == "old"


def test_custom_type_handler():
    """Test that custom type handlers are called by the factory."""

    class MyDate:
        def __init__(self, val):
            self.val = val

    def handle_mydate(value, provenance):
        from yaml_provenance import Provenance
        value._provenance = Provenance(provenance)
        value.value = value
        value.provenance = property(lambda self: self._provenance)
        # Simplified: just attach provenance directly
        return value

    configure(ProvenanceConfig(
        custom_type_handlers={MyDate: handle_mydate},
        track_history=True,
    ))

    date = MyDate("2024-01-01")
    result = wrapper_with_provenance_factory(date, {"line": 1})
    assert result is date
    assert hasattr(result, "_provenance")
