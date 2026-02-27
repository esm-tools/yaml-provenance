"""
Tests for _serialization.py – pickle reducers, YAML representers, JSON encoder.
"""

import json
import pickle
from io import StringIO

import pytest
from ruamel.yaml import YAML

from yaml_provenance import (
    load_yaml,
    register_pickle_reducers,
    register_yaml_representers,
    ProvenanceJSONEncoder,
    wrapper_with_provenance_factory,
    BoolWithProvenance,
    NoneWithProvenance,
    DictWithProvenance,
    ListWithProvenance,
)

FIXTURES_DIR = __import__("os").path.join(
    __import__("os").path.dirname(__file__), "fixtures"
)


@pytest.fixture()
def loaded_config():
    """Load example2.yaml and register serialization helpers."""
    path = __import__("os").path.join(FIXTURES_DIR, "nested", "example2.yaml")
    cfg = load_yaml(path)
    return cfg


# ── Pickle ────────────────────────────────────────────────────────────────


class TestPickleReducers:
    def test_str_roundtrip(self, loaded_config):
        register_pickle_reducers()
        val = loaded_config["echam"]["type"]
        data = pickle.dumps(val)
        restored = pickle.loads(data)
        assert restored == "atmosphere"
        assert isinstance(restored, str)

    def test_int_roundtrip(self, loaded_config):
        register_pickle_reducers()
        val = loaded_config["echam"]["files"]["greenhouse"]["a_list"][0]
        data = pickle.dumps(val)
        restored = pickle.loads(data)
        assert restored == 1
        assert isinstance(restored, int)

    def test_bool_roundtrip(self):
        register_pickle_reducers()
        val = BoolWithProvenance(True, {"yaml_file": "test", "line": 1, "col": 1,
                                         "category": None, "subcategory": None})
        data = pickle.dumps(val)
        restored = pickle.loads(data)
        assert restored is True

    def test_none_roundtrip(self):
        register_pickle_reducers()
        val = NoneWithProvenance(None, {"yaml_file": "test", "line": 1, "col": 1,
                                         "category": None, "subcategory": None})
        data = pickle.dumps(val)
        restored = pickle.loads(data)
        assert restored is None

    def test_list_roundtrip(self, loaded_config):
        register_pickle_reducers()
        val = loaded_config["echam"]["files"]["greenhouse"]["a_list"]
        data = pickle.dumps(val)
        restored = pickle.loads(data)
        assert restored == [1, 2, 3]
        assert isinstance(restored, list)

    def test_dict_roundtrip(self, loaded_config):
        register_pickle_reducers()
        data = pickle.dumps(loaded_config)
        restored = pickle.loads(data)
        assert isinstance(restored, dict)
        assert "echam" in restored

    def test_idempotent(self, loaded_config):
        """Calling register_pickle_reducers twice should be safe."""
        register_pickle_reducers()
        register_pickle_reducers()
        val = loaded_config["echam"]["type"]
        data = pickle.dumps(val)
        assert pickle.loads(data) == "atmosphere"


# ── YAML Representers ────────────────────────────────────────────────────


class TestYAMLRepresenters:
    def test_dump_str(self, loaded_config):
        register_yaml_representers()
        yml = YAML()
        buf = StringIO()
        yml.dump({"key": loaded_config["echam"]["type"]}, buf)
        assert "atmosphere" in buf.getvalue()

    def test_dump_int(self, loaded_config):
        register_yaml_representers()
        yml = YAML()
        buf = StringIO()
        yml.dump({"key": loaded_config["echam"]["files"]["greenhouse"]["a_list"][0]}, buf)
        assert "1" in buf.getvalue()

    def test_dump_bool(self):
        register_yaml_representers()
        val = BoolWithProvenance(True, {"yaml_file": "test", "line": 1, "col": 1,
                                         "category": None, "subcategory": None})
        yml = YAML()
        buf = StringIO()
        yml.dump({"key": val}, buf)
        assert "true" in buf.getvalue()

    def test_dump_none(self):
        register_yaml_representers()
        val = NoneWithProvenance(None, {"yaml_file": "test", "line": 1, "col": 1,
                                         "category": None, "subcategory": None})
        yml = YAML()
        buf = StringIO()
        yml.dump({"key": val}, buf)
        output = buf.getvalue()
        # ruamel.yaml represents None as empty string or "null" depending on mode
        assert "key:" in output

    def test_dump_list(self, loaded_config):
        register_yaml_representers()
        yml = YAML()
        buf = StringIO()
        yml.dump({"key": loaded_config["echam"]["files"]["greenhouse"]["a_list"]}, buf)
        output = buf.getvalue()
        assert "1" in output
        assert "2" in output
        assert "3" in output

    def test_dump_dict(self, loaded_config):
        register_yaml_representers()
        yml = YAML()
        buf = StringIO()
        yml.dump(dict(loaded_config), buf)
        assert "echam" in buf.getvalue()

    def test_idempotent(self, loaded_config):
        """Calling register_yaml_representers twice should be safe."""
        register_yaml_representers()
        register_yaml_representers()
        yml = YAML()
        buf = StringIO()
        yml.dump({"key": loaded_config["echam"]["type"]}, buf)
        assert "atmosphere" in buf.getvalue()


# ── JSON Encoder ──────────────────────────────────────────────────────────


class TestProvenanceJSONEncoder:
    def test_bool_serializes(self):
        val = BoolWithProvenance(False, {"yaml_file": "t", "line": 1, "col": 1,
                                          "category": None, "subcategory": None})
        result = json.dumps({"flag": val}, cls=ProvenanceJSONEncoder)
        assert json.loads(result) == {"flag": False}

    def test_none_serializes(self):
        val = NoneWithProvenance(None, {"yaml_file": "t", "line": 1, "col": 1,
                                         "category": None, "subcategory": None})
        result = json.dumps({"val": val}, cls=ProvenanceJSONEncoder)
        assert json.loads(result) == {"val": None}

    def test_normal_values_pass_through(self):
        """Non-provenance values should serialize normally."""
        result = json.dumps({"a": 1, "b": "hello"}, cls=ProvenanceJSONEncoder)
        assert json.loads(result) == {"a": 1, "b": "hello"}

    def test_unserializable_raises(self):
        """Objects that can't be serialized should still raise."""
        with pytest.raises(TypeError):
            json.dumps({"bad": object()}, cls=ProvenanceJSONEncoder)
