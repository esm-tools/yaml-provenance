"""
Tests for keep_provenance_in_recursive_function decorator.
"""

from yaml_provenance import (
    keep_provenance_in_recursive_function,
    wrapper_with_provenance_factory,
    DictWithProvenance,
)


def test_decorator_preserves_provenance(config, example_path2):
    """Test that provenance is preserved through a decorated function."""

    @keep_provenance_in_recursive_function
    def change_elem(tree, rhs):
        return wrapper_with_provenance_factory("new_val", {"modified": True})

    tree = []
    rhs1 = change_elem(tree, config["echam"]["type"])
    rhs2 = change_elem(tree, config["echam"]["files"]["greenhouse"]["a_list"][1])

    assert rhs1 == "new_val"
    assert rhs1.provenance[0] == {
        "line": 2,
        "col": 11,
        "yaml_file": example_path2,
        "category": None,
        "subcategory": None,
    }

    assert rhs2 == "new_val"
    assert rhs2.provenance[0] == {
        "line": 9,
        "col": 19,
        "yaml_file": example_path2,
        "category": None,
        "subcategory": None,
    }


def test_decorator_unchanged_value(config):
    """When output equals input, provenance should not change."""

    @keep_provenance_in_recursive_function
    def identity(tree, rhs):
        return rhs

    tree = []
    original_prov = list(config["echam"]["type"].provenance)
    result = identity(tree, config["echam"]["type"])
    assert result == config["echam"]["type"]


def test_decorator_with_plain_output(config):
    """When output has no provenance, wrap it with the old provenance."""

    @keep_provenance_in_recursive_function
    def to_upper(tree, rhs):
        return str(rhs).upper()

    tree = []
    result = to_upper(tree, config["echam"]["type"])
    assert result == "ATMOSPHERE"
    assert hasattr(result, "provenance")
    assert len(result.provenance) >= 1
