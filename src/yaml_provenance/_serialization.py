"""
Serialization support for yaml-provenance wrapper types.

Provides pickle reducers, YAML representers, and a JSON encoder so that
WithProvenance objects can be serialized by the standard library and
ruamel.yaml without errors.
"""

import json

from ._wrapper import ProvenanceClassForTheUnsubclassable

# Builtin types to reduce to (walking up MRO past ruamel scalars)
_BUILTIN_TYPES = (str, int, float, bytes, bytearray)


def _get_builtin_base(cls):
    """Return the first plain builtin ancestor of *cls* in its MRO."""
    for base in cls.__mro__:
        if base in _BUILTIN_TYPES:
            return base
    return cls.__bases__[0]


def register_pickle_reducers():
    """
    Patch ``__reduce__`` on every WithProvenance class so pickle can handle them.

    Safe to call multiple times; only patches classes not already patched.
    Should be called after every ``load_yaml()`` since ``_wrapper_registry``
    grows lazily.
    """
    from ._wrapper import _wrapper_registry, BoolWithProvenance, NoneWithProvenance
    from ._dict import DictWithProvenance
    from ._list import ListWithProvenance

    def _make_reduce(builtin_type):
        def __reduce__(self):
            return (builtin_type, (builtin_type(self),))
        return __reduce__

    # 1. Dynamic registry types
    for cls in _wrapper_registry.values():
        if not getattr(cls, "_pickle_patched", False):
            builtin = _get_builtin_base(cls)
            cls.__reduce__ = _make_reduce(builtin)
            cls._pickle_patched = True

    # 2. BoolWithProvenance
    if not getattr(BoolWithProvenance, "_pickle_patched", False):
        BoolWithProvenance.__reduce__ = lambda self: (bool, (self.value,))
        BoolWithProvenance._pickle_patched = True

    # 3. NoneWithProvenance
    if not getattr(NoneWithProvenance, "_pickle_patched", False):
        NoneWithProvenance.__reduce__ = lambda self: (type(None), ())
        NoneWithProvenance._pickle_patched = True

    # 4. ListWithProvenance
    if not getattr(ListWithProvenance, "_pickle_patched", False):
        ListWithProvenance.__reduce__ = lambda self: (list, (list(self),))
        ListWithProvenance._pickle_patched = True

    # 5. DictWithProvenance
    if not getattr(DictWithProvenance, "_pickle_patched", False):
        DictWithProvenance.__reduce__ = lambda self: (dict, (dict(self),))
        DictWithProvenance._pickle_patched = True


def register_yaml_representers():
    """Register WithProvenance types on ruamel.yaml representer classes.

    Safe to call multiple times; only patches types not already patched.
    Should be called after every ``load_yaml()`` since ``_wrapper_registry``
    grows lazily.
    """
    from ._wrapper import _wrapper_registry, BoolWithProvenance, NoneWithProvenance
    from ._dict import DictWithProvenance
    from ._list import ListWithProvenance

    try:
        from ruamel.yaml.representer import SafeRepresenter, RoundTripRepresenter
    except ImportError:
        return

    if not hasattr(register_yaml_representers, "_patched"):
        register_yaml_representers._patched = set()
    patched = register_yaml_representers._patched

    for repr_class in (SafeRepresenter, RoundTripRepresenter):
        # Dynamic registry types
        for cls_name, cls in _wrapper_registry.items():
            key = (repr_class, cls_name)
            if key in patched:
                continue
            builtin = _get_builtin_base(cls)
            fn = repr_class.yaml_representers.get(builtin)
            if fn:
                repr_class.add_representer(cls, fn)
                patched.add(key)

        # BoolWithProvenance
        key = (repr_class, "BoolWithProvenance")
        if key not in patched:
            bool_fn = repr_class.yaml_representers.get(bool)
            if bool_fn:
                repr_class.add_representer(
                    BoolWithProvenance,
                    lambda dumper, data, _fn=bool_fn: _fn(dumper, data.value),
                )
                patched.add(key)

        # NoneWithProvenance
        key = (repr_class, "NoneWithProvenance")
        if key not in patched:
            none_fn = repr_class.yaml_representers.get(type(None))
            if none_fn:
                repr_class.add_representer(
                    NoneWithProvenance,
                    lambda dumper, data, _fn=none_fn: _fn(dumper, None),
                )
                patched.add(key)

        # ListWithProvenance
        key = (repr_class, "ListWithProvenance")
        if key not in patched:
            list_fn = repr_class.yaml_representers.get(list)
            if list_fn:
                repr_class.add_representer(
                    ListWithProvenance,
                    lambda dumper, data, _fn=list_fn: _fn(dumper, list(data)),
                )
                patched.add(key)

        # DictWithProvenance
        key = (repr_class, "DictWithProvenance")
        if key not in patched:
            dict_fn = repr_class.yaml_representers.get(dict)
            if dict_fn:
                repr_class.add_representer(
                    DictWithProvenance,
                    lambda dumper, data, _fn=dict_fn: _fn(dumper, dict(data)),
                )
                patched.add(key)


class ProvenanceJSONEncoder(json.JSONEncoder):
    """JSON encoder that handles yaml-provenance wrapper types.

    ``BoolWithProvenance`` and ``NoneWithProvenance`` are subclasses of
    ``ProvenanceClassForTheUnsubclassable`` rather than ``bool``/``NoneType``,
    so the standard json encoder doesn't recognize them.
    """

    def default(self, obj):
        if isinstance(obj, ProvenanceClassForTheUnsubclassable):
            return obj.value
        return super().default(obj)
