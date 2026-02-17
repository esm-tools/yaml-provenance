"""
Tests for the Provenance class.
"""

import copy

from yaml_provenance import Provenance


def test_provenance_init_with_dict():
    """Provenance wraps a single dict into a list."""
    prov = Provenance({"line": 1, "col": 2})
    assert len(prov) == 1
    assert prov[0] == {"line": 1, "col": 2}


def test_provenance_init_with_list():
    """Provenance accepts a list directly."""
    prov = Provenance([{"line": 1}, {"line": 2}])
    assert len(prov) == 2


def test_append_last_step_modified_by():
    """append_last_step_modified_by duplicates last entry with modified_by."""
    prov = Provenance({"line": 1, "col": 2})
    prov.append_last_step_modified_by("my_func")
    assert len(prov) == 2
    assert prov[-1]["modified_by"] == "my_func"
    assert prov[-1]["line"] == 1
    # Original should not be modified
    assert "modified_by" not in prov[0]


def test_extend_and_modified_by():
    """extend_and_modified_by extends provenance with extended_by label."""
    prov1 = Provenance({"line": 1})
    prov2 = Provenance({"line": 5})
    prov1.extend_and_modified_by(prov2, "merge_func")
    assert len(prov1) == 2
    assert prov1[-1]["extended_by"] == "merge_func"


def test_extend_and_modified_by_same_object():
    """When extending with self, should append_last_step_modified_by instead."""
    prov = Provenance({"line": 1})
    prov.extend_and_modified_by(prov, "self_func")
    assert len(prov) == 2
    assert prov[-1]["modified_by"] == "self_func"


def test_add_modified_by_none():
    """add_modified_by with None provenance_step returns None."""
    prov = Provenance({"line": 1})
    result = prov.add_modified_by(None, "func")
    assert result is None
