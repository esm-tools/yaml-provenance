"""
Tests for ListWithProvenance.
"""

import pytest

from yaml_provenance import (
    DictWithProvenance,
    ListWithProvenance,
    Provenance,
    wrapper_with_provenance_factory,
    load_yaml,
)


def test_list_get_provenance(example_path1):
    """Check provenance of a list entry."""
    config = load_yaml(example_path1)
    prov = config["person"]["my_other_list"].get_provenance()
    assert len(prov) == 3
    for p in prov:
        assert p["yaml_file"] == example_path1
        assert p["line"] == 15


def test_list_set_provenance(example_path1):
    """Check set_provenance of a list entry."""
    config = load_yaml(example_path1)
    new_prov = {
        "line": 15,
        "col": 25,
        "yaml_file": "example.yaml",
        "category": "from_a_list",
        "subcategory": None,
    }
    check_prov = [new_prov, new_prov, new_prov]
    config["person"]["my_other_list"].set_provenance(new_prov)
    assert config["person"]["my_other_list"].get_provenance() == check_prov


def test_list_set_single_element_provenance(example_path1):
    """Check set_provenance of a single list entry."""
    config = load_yaml(example_path1)
    new_prov = {
        "line": 15,
        "col": 25,
        "yaml_file": "example.yaml",
        "category": "from_a_second_list",
        "subcategory": None,
    }
    config["person"]["my_other_list"][2].provenance = Provenance(new_prov)
    prov = config["person"]["my_other_list"].get_provenance()
    assert prov[2] == new_prov


def test_list_provenance_setter_raises_on_invalid():
    """Check ValueError when setting provenance to a non-Provenance object."""
    config = ListWithProvenance([1, 2, 3], [{}, {}, {}])
    with pytest.raises(
        ValueError,
        match="Provenance must be an instance of the provenance.Provenance class!",
    ):
        config[0].provenance = {"line": 1}


def test_list_with_dict_inside(example_path1):
    """Check that lists with dicts inside get proper provenance."""
    config = load_yaml(example_path1)
    elem = config["person"]["list_with_dict_inside"]
    assert isinstance(elem, ListWithProvenance)
    assert len(elem) == 3
    assert elem[0] == 1
    assert isinstance(elem[2], DictWithProvenance)
