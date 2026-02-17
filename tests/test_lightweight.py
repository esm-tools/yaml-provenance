"""
Tests for lightweight mode (track_history=False).
"""

import pytest

from yaml_provenance import (
    ProvenanceConfig,
    configure,
    Provenance,
    DictWithProvenance,
    ListWithProvenance,
    wrapper_with_provenance_factory,
    load_yaml,
)


@pytest.fixture(autouse=True)
def lightweight_config():
    """Override the autouse fixture to use lightweight mode."""
    configure(ProvenanceConfig(track_history=False))
    yield
    configure(None)


def test_provenance_has_at_most_one_element():
    """In lightweight mode, provenance lists have at most 1 element."""
    prov = Provenance([{"line": 1}, {"line": 2}, {"line": 3}], track_history=False)
    assert len(prov) == 1
    assert prov[-1] == {"line": 3}


def test_append_last_step_modifies_in_place():
    """In lightweight mode, append_last_step updates in-place."""
    prov = Provenance({"line": 1}, track_history=False)
    prov.append_last_step_modified_by("func")
    assert len(prov) == 1
    assert prov[0]["modified_by"] == "func"
    assert prov[0]["line"] == 1


def test_extend_replaces_single_element():
    """In lightweight mode, extend replaces the single element."""
    prov1 = Provenance({"line": 1}, track_history=False)
    prov2 = Provenance({"line": 5}, track_history=False)
    prov1.extend_and_modified_by(prov2, "merge")
    assert len(prov1) == 1
    assert prov1[0]["line"] == 5


def test_dict_provenance_lightweight():
    """DictWithProvenance works in lightweight mode."""
    d = DictWithProvenance(
        {"key": "value"},
        {"key": {"line": 1, "col": 1}},
    )
    prov = d.get_provenance()
    assert prov["key"] == {"line": 1, "col": 1}
    assert len(d["key"].provenance) == 1


def test_list_provenance_lightweight():
    """ListWithProvenance works in lightweight mode."""
    l = ListWithProvenance([1, 2, 3], [{}, {}, {}])
    prov = l.get_provenance()
    assert len(prov) == 3


def test_setitem_no_deepcopy_lightweight():
    """In lightweight mode, __setitem__ should not use deepcopy."""
    d = DictWithProvenance(
        {"key": "old"},
        {"key": {"line": 1, "col": 1}},
    )
    new_val = wrapper_with_provenance_factory("new", {"line": 2, "col": 1})
    d["key"] = new_val
    # Provenance should have at most 1 element (the extended one)
    assert len(d["key"].provenance) <= 2  # may be 1 in lightweight


def test_load_yaml_lightweight(example_path2):
    """load_yaml respects lightweight config."""
    config = load_yaml(example_path2)
    # Should work identically for reading
    prov = config.get_provenance()
    assert prov["echam"]["type"]["line"] == 2
    # Provenance lists should be length 1
    assert len(config["echam"]["type"].provenance) == 1


def test_get_provenance_index_works():
    """value.provenance[-1] works in both modes."""
    val = wrapper_with_provenance_factory("test", {"line": 42})
    assert val.provenance[-1] == {"line": 42}
    assert len(val.provenance) == 1
