"""
Tests for the WithProvenance wrapper factory.
"""

from yaml_provenance import (
    wrapper_with_provenance_factory,
    BoolWithProvenance,
    NoneWithProvenance,
    Provenance,
    is_none_like,
)


def test_wrap_string():
    val = wrapper_with_provenance_factory("hello", {"line": 1})
    assert val == "hello"
    assert val.provenance[-1] == {"line": 1}
    assert isinstance(val, str)


def test_wrap_int():
    val = wrapper_with_provenance_factory(42, {"line": 2})
    assert val == 42
    assert val.provenance[-1] == {"line": 2}
    assert isinstance(val, int)


def test_wrap_float():
    val = wrapper_with_provenance_factory(3.14, {"line": 3})
    assert val == 3.14
    assert isinstance(val, float)


def test_wrap_bool():
    val = wrapper_with_provenance_factory(True, {"line": 4})
    assert val == True
    assert isinstance(val, BoolWithProvenance)
    assert isinstance(val, bool)
    assert val.provenance[-1] == {"line": 4}


def test_wrap_none():
    # The factory wraps None so its provenance is preserved (consistent with all
    # other values). `is None` intentionally fails — use is_none_like() instead.
    val = wrapper_with_provenance_factory(None, {"line": 5})
    assert isinstance(val, NoneWithProvenance)
    assert val.value is None
    assert val.provenance[-1] == {"line": 5}
    assert val is not None
    assert is_none_like(val)


def test_is_none_like():
    assert is_none_like(None)
    assert is_none_like(wrapper_with_provenance_factory(None, {"line": 1}))
    assert not is_none_like(0)
    assert not is_none_like("")
    assert not is_none_like(wrapper_with_provenance_factory("x", {"line": 1}))


def test_wrap_preserves_value():
    val = wrapper_with_provenance_factory("test", {"line": 1})
    assert val.value == "test"


def test_bool_hash():
    val = wrapper_with_provenance_factory(True, {"line": 1})
    assert hash(val) == hash(True)


def test_none_bool_is_false():
    val = wrapper_with_provenance_factory(None, {"line": 1})
    assert not bool(val)


def test_mappings_pass_through():
    """DictWithProvenance and ListWithProvenance should pass through."""
    from yaml_provenance import DictWithProvenance, ListWithProvenance
    d = DictWithProvenance({"a": 1}, {"a": {}})
    result = wrapper_with_provenance_factory(d)
    assert result is d

    l = ListWithProvenance([1], [{}])
    result = wrapper_with_provenance_factory(l)
    assert result is l
