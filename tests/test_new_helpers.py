"""
Tests for new helper functions and load_yaml file-object support.
"""

import os

import pytest

from yaml_provenance import (
    wrap_computed,
    transfer_provenance,
    annotate_dict,
    load_yaml,
    wrapper_with_provenance_factory,
)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


# ── wrap_computed ─────────────────────────────────────────────────────────


class TestWrapComputed:
    def test_wraps_string(self):
        val = wrap_computed("hello", "env.MY_VAR")
        assert val == "hello"
        assert hasattr(val, "provenance")
        assert val.provenance[-1]["yaml_file"] == "env.MY_VAR"

    def test_wraps_int(self):
        val = wrap_computed(42, "computed.timeout")
        assert val == 42
        assert val.provenance[-1]["yaml_file"] == "computed.timeout"
        assert val.provenance[-1]["line"] == 0

    def test_wraps_float(self):
        val = wrap_computed(3.14, "math.pi")
        assert val == 3.14
        assert val.provenance[-1]["yaml_file"] == "math.pi"

    def test_wraps_bool(self):
        val = wrap_computed(True, "flags.debug")
        assert val == True  # noqa: E712
        assert val.provenance[-1]["yaml_file"] == "flags.debug"

    def test_wraps_none(self):
        val = wrap_computed(None, "defaults.empty")
        assert val.value is None
        assert val.provenance[-1]["yaml_file"] == "defaults.empty"


# ── transfer_provenance ──────────────────────────────────────────────────


class TestTransferProvenance:
    def test_transfers_from_wrapped_str(self):
        original = wrap_computed("  hello  ", "src.greeting")
        result = transfer_provenance(original, "hello")
        assert result == "hello"
        assert hasattr(result, "provenance")
        assert result.provenance[-1]["yaml_file"] == "src.greeting"

    def test_no_provenance_returns_unchanged(self):
        result = transfer_provenance("plain", "UPPER")
        assert result == "UPPER"
        assert not hasattr(result, "provenance")

    def test_preserves_type(self):
        original = wrap_computed(42, "src.num")
        result = transfer_provenance(original, 84)
        assert result == 84
        assert hasattr(result, "provenance")


# ── annotate_dict ────────────────────────────────────────────────────────


class TestAnnotateDict:
    def test_flat_dict(self):
        d = {"a": 1, "b": "two"}
        result = annotate_dict(d, "cfg")
        assert result is d  # modified in-place
        assert hasattr(d["a"], "provenance")
        assert d["a"].provenance[-1]["yaml_file"] == "cfg.a"
        assert hasattr(d["b"], "provenance")
        assert d["b"].provenance[-1]["yaml_file"] == "cfg.b"

    def test_nested_dict(self):
        d = {"outer": {"inner": 99}}
        annotate_dict(d, "app")
        assert hasattr(d["outer"]["inner"], "provenance")
        assert d["outer"]["inner"].provenance[-1]["yaml_file"] == "app.inner"

    def test_skips_already_wrapped(self):
        val = wrap_computed("existing", "original.source")
        d = {"key": val}
        annotate_dict(d, "new_prefix")
        # Should keep the original provenance
        assert d["key"].provenance[-1]["yaml_file"] == "original.source"

    def test_returns_dict(self):
        d = {"x": 10}
        assert annotate_dict(d, "p") is d


# ── load_yaml with file objects ──────────────────────────────────────────


class TestLoadYamlFileObject:
    def test_accepts_file_object(self):
        path = os.path.join(FIXTURES_DIR, "nested", "example2.yaml")
        with open(path, "r") as f:
            cfg = load_yaml(f)
        assert "echam" in cfg
        assert cfg["echam"]["type"] == "atmosphere"

    def test_file_object_provenance_has_path(self):
        path = os.path.join(FIXTURES_DIR, "nested", "example2.yaml")
        with open(path, "r") as f:
            cfg = load_yaml(f)
        prov = cfg["echam"]["type"].provenance[-1]
        assert prov["yaml_file"] == path

    def test_path_string_still_works(self):
        path = os.path.join(FIXTURES_DIR, "nested", "example2.yaml")
        cfg = load_yaml(path)
        assert "echam" in cfg
