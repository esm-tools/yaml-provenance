"""
Tests for DictWithProvenance — ported from esm_parser test_provenance.py.
"""

import copy

import pytest

from yaml_provenance import (
    DictWithProvenance,
    Provenance,
    ProvenanceConfig,
    configure,
    wrapper_with_provenance_factory,
    CategoryConflictError,
)


def test_get_provenance_from_yaml_loader(config, check_provenance):
    """Test 1: Checks for correct provenance entries from example2.yaml."""
    assert config.get_provenance() == check_provenance


def test_get_provenance_of_added_entry(config, check_provenance):
    """Test 2: Provenance of an added config entry is None."""
    config["fesom"] = True
    check_provenance["fesom"] = None
    assert config.get_provenance() == check_provenance


def test_get_provenance_of_added_nested_entry(config, check_provenance):
    """Test 3: Provenance of an added nested config entry is None."""
    config["fesom"] = {"asd": 0}
    check_provenance["fesom"] = None
    assert config.get_provenance() == check_provenance


def test_get_provenance_of_added_nested_entry_2(config, check_provenance):
    """Test 4: Provenance of added nested entry inside existing dict is None."""
    config["echam"]["test1"] = 17.0
    check_provenance["echam"]["test1"] = None
    assert config.get_provenance() == check_provenance


def test_set_provenance_for_leaf(config, check_provenance):
    """Test 5: Reset provenance of echam leaves."""
    new_prov = {
        "line": 2,
        "col": 11,
        "yaml_file": "someother.yaml",
        "category": "userdefined",
    }
    config["echam"].set_provenance(new_prov)
    check_provenance["echam"]["type"] = new_prov
    check_provenance["echam"]["files"]["greenhouse"]["kind"] = new_prov
    check_provenance["echam"]["files"]["greenhouse"]["path_in_computer"] = new_prov
    check_provenance["echam"]["files"]["greenhouse"]["a_list"] = [
        new_prov,
        new_prov,
        new_prov,
    ]
    assert config.get_provenance() == check_provenance


def test_set_provenance_for_leaf_of_new_branch(config, check_provenance):
    """Test 6: Reset provenance of leaves for a later added branch."""
    new_prov = {
        "line": 2,
        "col": 11,
        "yaml_file": "someother.yaml",
        "category": "debuginfo",
    }
    config["new_branch"] = DictWithProvenance({"loaded_from_file": None}, {})
    config["new_branch"].set_provenance(new_prov)
    check_provenance["new_branch"] = {"loaded_from_file": new_prov}
    assert config.get_provenance() == check_provenance


def test_set_provenance_for_leaf_to_a_string(config, check_provenance):
    """Test 7: Reset provenance of all echam leaves to a string."""
    new_prov = "a_string"
    config["echam"].set_provenance(new_prov)
    check_provenance["echam"]["type"] = new_prov
    check_provenance["echam"]["files"]["greenhouse"]["kind"] = new_prov
    check_provenance["echam"]["files"]["greenhouse"]["path_in_computer"] = new_prov
    check_provenance["echam"]["files"]["greenhouse"]["a_list"] = [
        new_prov,
        new_prov,
        new_prov,
    ]
    assert config.get_provenance() == check_provenance


def test_set_provenance_for_a_new_leaf(config, check_provenance):
    """Test 8: Set provenance of a new entry."""
    config["fesom"] = {"asd": 0}
    new_prov = {
        "line": 2,
        "col": 11,
        "yaml_file": "someother.yaml",
        "category": "set_for_unknown_leaf",
    }
    config["fesom"] = DictWithProvenance(config["fesom"], {})
    config["fesom"].set_provenance(new_prov)
    check_provenance["fesom"] = {"asd": None}
    check_provenance["fesom"]["asd"] = new_prov
    assert config.get_provenance() == check_provenance


def test_provenance_update(config, check_provenance, example_path2):
    """Test 9: update method preserves provenance history."""
    new_prov = {
        "line": 2,
        "col": 11,
        "yaml_file": "someother.yaml",
        "category": "set_for_unknown_leaf",
    }
    new_config = {
        "echam": DictWithProvenance({"type": "mpi_atmosphere"}, {})
    }
    new_config["echam"].set_provenance(new_prov)

    config["echam"].update(new_config["echam"])
    check_provenance["echam"]["type"] = new_prov
    assert config.get_provenance() == check_provenance
    # Checks that update preserves provenance history
    assert config["echam"]["type"].provenance == [
        {
            "line": 2,
            "col": 11,
            "yaml_file": example_path2,
            "category": None,
            "subcategory": None,
        },
        None,
        {
            "line": 2,
            "col": 11,
            "extended_by": "dict.update",
            "yaml_file": "someother.yaml",
            "category": "set_for_unknown_leaf",
        },
    ]


def test_set_provenance_for_a_list_leaf(config, check_provenance):
    """Test 10: Reset provenance of a list."""
    new_prov = {
        "line": 2,
        "col": 11,
        "yaml_file": "someother.yaml",
        "category": "this_is_for_a_list",
        "subcategory": None,
    }
    config["fesom"] = {"asd": 0}
    config["fesom"]["list"] = [30, 19]
    config["fesom"] = DictWithProvenance(config["fesom"], {})
    config["fesom"]["list"].set_provenance(new_prov)
    check_provenance["fesom"] = {}
    check_provenance["fesom"]["list"] = [new_prov, new_prov]
    check_provenance["fesom"]["asd"] = None
    assert config.get_provenance() == check_provenance


def test_error_in_setitem_if_same_category_and_hierarchy(config):
    """
    Check that setting a new value with the same category raises
    CategoryConflictError when hierarchy is configured.
    """
    # Configure a hierarchy so conflict enforcement kicks in
    configure(ProvenanceConfig(
        category_hierarchy=[None, "runscript", "backend"],
        track_history=True,
    ))

    echam = DictWithProvenance(
        {"type": "atmosphere"},
        {"type": {"line": 1, "col": 1, "category": "runscript"}},
    )

    new_val = wrapper_with_provenance_factory(
        "ocean",
        {"line": 2, "col": 1, "category": "runscript"},
    )

    with pytest.raises(CategoryConflictError):
        echam["type"] = new_val


def test_no_error_if_same_category_and_same_value(config):
    """
    Check that duplicate values at the same category level don't raise errors.
    """
    configure(ProvenanceConfig(
        category_hierarchy=[None, "runscript", "backend"],
        track_history=True,
    ))

    echam = DictWithProvenance(
        {"type": "atmosphere"},
        {"type": {"line": 1, "col": 1, "category": "runscript"}},
    )

    new_val = wrapper_with_provenance_factory(
        "atmosphere",
        {"line": 2, "col": 1, "category": "runscript"},
    )

    # Should not raise — same value
    echam["type"] = new_val
    assert echam["type"] == "atmosphere"


def test_provenance_setter_raises_on_invalid_type():
    """Check that setting provenance to a non-Provenance object raises ValueError."""
    d = DictWithProvenance({"key": "val"}, {"key": {"line": 1}})
    with pytest.raises(
        ValueError,
        match="Provenance must be an instance of the provenance.Provenance class!",
    ):
        d["key"].provenance = {"line": 2}
