"""
Tests for clean_provenance.
"""

from yaml_provenance import clean_provenance, wrapper_with_provenance_factory, DictWithProvenance


PROV = {"line": 1, "col": 0}


# --- scalar passthrough ---

def test_plain_string_passthrough():
    assert clean_provenance("hello") == "hello"
    assert type(clean_provenance("hello")) is str


def test_plain_int_passthrough():
    assert clean_provenance(42) == 42


def test_plain_none_passthrough():
    assert clean_provenance(None) is None


# --- wrapped scalars ---

def test_clean_wrapped_string():
    val = wrapper_with_provenance_factory("hello", PROV)
    result = clean_provenance(val)
    assert result == "hello"
    assert type(result) is str


def test_clean_wrapped_int():
    val = wrapper_with_provenance_factory(42, PROV)
    result = clean_provenance(val)
    assert result == 42
    assert type(result) is int


def test_clean_wrapped_float():
    val = wrapper_with_provenance_factory(3.14, PROV)
    result = clean_provenance(val)
    assert result == 3.14
    assert type(result) is float


def test_clean_wrapped_bool():
    val = wrapper_with_provenance_factory(True, PROV)
    result = clean_provenance(val)
    assert result is True
    assert type(result) is bool


def test_clean_wrapped_none():
    val = wrapper_with_provenance_factory(None, PROV)
    result = clean_provenance(val)
    assert result is None


# --- lists ---

def test_clean_list_of_wrapped_values():
    lst = [wrapper_with_provenance_factory(v, PROV) for v in ["a", 1, True]]
    result = clean_provenance(lst)
    assert result == ["a", 1, True]
    assert all(type(r) is type(v) for r, v in zip(result, ["a", 1, True]))


def test_clean_nested_list():
    inner = [wrapper_with_provenance_factory(i, PROV) for i in [1, 2]]
    outer = [wrapper_with_provenance_factory("x", PROV), inner]
    result = clean_provenance(outer)
    assert result == ["x", [1, 2]]


def test_clean_plain_list_passthrough():
    lst = [1, "two", 3.0]
    result = clean_provenance(lst)
    assert result == [1, "two", 3.0]


# --- dicts ---

def test_clean_dict_with_wrapped_values():
    d = {
        "key": wrapper_with_provenance_factory("value", PROV),
        "num": wrapper_with_provenance_factory(7, PROV),
    }
    result = clean_provenance(d)
    assert result == {"key": "value", "num": 7}
    assert type(result["key"]) is str
    assert type(result["num"]) is int


def test_clean_dict_with_wrapped_keys():
    key = wrapper_with_provenance_factory("mykey", PROV)
    d = {key: "plain_value"}
    result = clean_provenance(d)
    assert result == {"mykey": "plain_value"}
    assert type(list(result.keys())[0]) is str


def test_clean_plain_dict_passthrough():
    d = {"a": 1, "b": "two"}
    result = clean_provenance(d)
    assert result == {"a": 1, "b": "two"}


def test_clean_nested_dict():
    d = {
        "outer": {
            "inner": wrapper_with_provenance_factory("deep", PROV),
        }
    }
    result = clean_provenance(d)
    assert result == {"outer": {"inner": "deep"}}


# --- key_transform ---

def test_key_transform_applied():
    d = {"MyKey": wrapper_with_provenance_factory("val", PROV)}
    result = clean_provenance(d, key_transform=str.lower)
    assert "mykey" in result
    assert result["mykey"] == "val"


def test_key_transform_on_wrapped_key():
    key = wrapper_with_provenance_factory("MyKey", PROV)
    d = {key: "val"}
    result = clean_provenance(d, key_transform=str.upper)
    assert "MYKEY" in result


# --- DictWithProvenance ---

def test_clean_dict_with_provenance_object():
    d = DictWithProvenance({"x": wrapper_with_provenance_factory("hello", PROV)}, {})
    result = clean_provenance(d)
    assert result == {"x": "hello"}
    assert type(result) is dict


# --- objects with __dict__ ---

def test_clean_object_with_dict():
    class Obj:
        def __init__(self):
            self.x = wrapper_with_provenance_factory("v", PROV)
            self.n = 42

    obj = Obj()
    result = clean_provenance(obj)
    assert result is obj
    assert result.x == "v"
    assert type(result.x) is str
    assert result.n == 42
