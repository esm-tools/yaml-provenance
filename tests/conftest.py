"""
Shared fixtures for yaml-provenance tests.
"""

import os

import pytest

from yaml_provenance import (
    ProvenanceConfig,
    configure,
    DictWithProvenance,
    load_yaml,
)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture()
def example_path1():
    return os.path.join(FIXTURES_DIR, "example.yaml")


@pytest.fixture()
def example_path2():
    return os.path.join(FIXTURES_DIR, "nested", "example2.yaml")


@pytest.fixture(autouse=True)
def reset_config():
    """Reset the module-level config before each test."""
    configure(ProvenanceConfig(track_history=True))
    yield
    configure(None)


@pytest.fixture()
def config(example_path2):
    """Load example2.yaml with provenance using the YAML loader."""
    return load_yaml(example_path2)


@pytest.fixture()
def check_provenance(example_path2):
    return {
        "echam": {
            "type": {
                "line": 2,
                "col": 11,
                "yaml_file": example_path2,
                "category": None,
                "subcategory": None,
            },
            "files": {
                "greenhouse": {
                    "kind": {
                        "line": 5,
                        "col": 19,
                        "yaml_file": example_path2,
                        "category": None,
                        "subcategory": None,
                    },
                    "path_in_computer": {
                        "line": 6,
                        "col": 31,
                        "yaml_file": example_path2,
                        "category": None,
                        "subcategory": None,
                    },
                    "a_list": [
                        {
                            "line": 8,
                            "col": 19,
                            "yaml_file": example_path2,
                            "category": None,
                            "subcategory": None,
                        },
                        {
                            "line": 9,
                            "col": 19,
                            "yaml_file": example_path2,
                            "category": None,
                            "subcategory": None,
                        },
                        {
                            "line": 10,
                            "col": 19,
                            "yaml_file": example_path2,
                            "category": None,
                            "subcategory": None,
                        },
                    ],
                }
            },
        },
    }
