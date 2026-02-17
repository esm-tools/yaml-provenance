"""
Tests for the YAML loader with provenance.
"""

import os

import pytest

from yaml_provenance import (
    DictWithProvenance,
    ListWithProvenance,
    ProvenanceConfig,
    ProvenanceLoader,
    configure,
    load_yaml,
)


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def test_load_yaml_basic(example_path2):
    """Load a simple YAML file and verify structure."""
    config = load_yaml(example_path2)
    assert isinstance(config, DictWithProvenance)
    assert config["echam"]["type"] == "atmosphere"
    assert config["echam"]["files"]["greenhouse"]["kind"] == "input"


def test_load_yaml_provenance_tracking(example_path2):
    """Verify provenance contains line, col, yaml_file."""
    config = load_yaml(example_path2)
    prov = config["echam"]["type"].provenance[-1]
    assert prov["line"] == 2
    assert prov["col"] == 11
    assert prov["yaml_file"] == example_path2


def test_load_yaml_list_provenance(example_path2):
    """Verify provenance for list elements."""
    config = load_yaml(example_path2)
    a_list = config["echam"]["files"]["greenhouse"]["a_list"]
    assert isinstance(a_list, ListWithProvenance)
    prov = a_list.get_provenance()
    assert len(prov) == 3
    assert prov[0]["line"] == 8
    assert prov[1]["line"] == 9
    assert prov[2]["line"] == 10


def test_load_yaml_with_category_resolver(example_path2):
    """Category resolver maps file path to category."""
    def resolver(filepath):
        return ("components", "echam")

    config = load_yaml(example_path2, category_resolver=resolver)
    prov = config["echam"]["type"].provenance[-1]
    assert prov["category"] == "components"
    assert prov["subcategory"] == "echam"


def test_load_yaml_default_category(example_path2):
    """Default category resolver returns (None, None)."""
    config = load_yaml(example_path2)
    prov = config["echam"]["type"].provenance[-1]
    assert prov["category"] is None
    assert prov["subcategory"] is None


def test_load_yaml_complex(example_path1):
    """Load the complex example with nested dicts and lists."""
    config = load_yaml(example_path1)
    assert config["person"]["name"] == "Some Name With Surname"
    assert config["person"]["my_int2"] == 42
    assert config["person"]["my_bolean"] == True
    assert isinstance(config["person"]["list_with_dict_inside"], ListWithProvenance)


def test_load_empty_yaml(tmp_path):
    """Loading an empty YAML file returns an empty DictWithProvenance."""
    empty = tmp_path / "empty.yaml"
    empty.write_text("")
    config = load_yaml(str(empty))
    assert isinstance(config, DictWithProvenance)
    assert len(config) == 0


def test_provenance_loader_reusable(example_path1, example_path2):
    """ProvenanceLoader can be reused across files."""
    loader = ProvenanceLoader()
    c1 = loader.load(example_path1)
    c2 = loader.load(example_path2)
    assert "person" in c1
    assert "echam" in c2
