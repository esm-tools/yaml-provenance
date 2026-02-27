"""
Tests for _serialization.py – pickle reducers, YAML representers, JSON encoder.
"""

import copy
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


# ── Deepcopy after pickle reducers ────────────────────────────────────────


class TestDeepcopyAfterPickleReducers:
    """``copy.deepcopy`` must preserve WithProvenance types even after
    ``register_pickle_reducers`` patches ``__reduce__``."""

    @pytest.fixture(autouse=True)
    def _register(self):
        register_pickle_reducers()

    def test_str_deepcopy(self):
        s = wrapper_with_provenance_factory(
            "hello",
            {"yaml_file": "f.yaml", "line": 1, "col": 2,
             "category": None, "subcategory": None},
        )
        s2 = copy.deepcopy(s)
        assert type(s2).__name__ == "StrWithProvenance"
        assert str(s2) == "hello"
        assert hasattr(s2, "_provenance")

    def test_int_deepcopy(self):
        i = wrapper_with_provenance_factory(
            42,
            {"yaml_file": "f.yaml", "line": 3, "col": 1,
             "category": None, "subcategory": None},
        )
        i2 = copy.deepcopy(i)
        assert type(i2).__name__ == "IntWithProvenance"
        assert int(i2) == 42
        assert hasattr(i2, "_provenance")

    def test_bool_deepcopy(self):
        b = BoolWithProvenance(
            True,
            {"yaml_file": "f.yaml", "line": 5, "col": 1,
             "category": None, "subcategory": None},
        )
        b2 = copy.deepcopy(b)
        assert isinstance(b2, BoolWithProvenance)
        assert b2.value is True
        assert hasattr(b2, "_provenance")

    def test_none_deepcopy(self):
        n = NoneWithProvenance(
            None,
            {"yaml_file": "f.yaml", "line": 7, "col": 1,
             "category": None, "subcategory": None},
        )
        n2 = copy.deepcopy(n)
        assert isinstance(n2, NoneWithProvenance)
        assert n2.value is None
        assert hasattr(n2, "_provenance")

    def test_dict_deepcopy(self, loaded_config):
        d2 = copy.deepcopy(loaded_config)
        assert type(d2).__name__ == "DictWithProvenance"
        for k in d2:
            assert hasattr(k, "_provenance"), f"key {k!r} lost provenance"

    def test_list_deepcopy(self):
        lst = ListWithProvenance(
            ["a", "b"],
            [
                {"yaml_file": "f.yaml", "line": 1, "col": 3,
                 "category": None, "subcategory": None},
                {"yaml_file": "f.yaml", "line": 2, "col": 3,
                 "category": None, "subcategory": None},
            ],
        )
        lst2 = copy.deepcopy(lst)
        assert type(lst2).__name__ == "ListWithProvenance"
        assert list(lst2) == ["a", "b"]
        for item in lst2:
            assert hasattr(item, "_provenance"), f"item {item!r} lost provenance"

    def test_deepcopy_dict_from_yaml(self):
        """End-to-end: load YAML, deepcopy, verify key provenance."""
        import os
        cfg = load_yaml(os.path.join(FIXTURES_DIR, "example.yaml"))
        cfg2 = copy.deepcopy(cfg)
        assert type(cfg2).__name__ == "DictWithProvenance"
        for k in cfg2:
            assert hasattr(k, "_provenance"), f"key {k!r} lost provenance after deepcopy"
