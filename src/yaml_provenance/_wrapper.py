"""
WithProvenance wrapper factory — creates provenance-aware subclasses dynamically.
"""

import copy

from ._provenance import Provenance
from ._config import get_config


# Registry of dynamically created WithProvenance classes
_wrapper_registry = {}

# Builtin types whose subclasses can be reduced to the builtin for pickling
_BUILTIN_TYPES = (str, int, float, bytes, bytearray)


def _get_builtin_base(cls):
    """Return the first plain builtin ancestor of *cls* in its MRO."""
    for base in cls.__mro__:
        if base in _BUILTIN_TYPES:
            return base
    return cls.__bases__[0]


def _make_pickle_reduce(builtin_type):
    """Create a ``__reduce__`` that reduces to the plain *builtin_type*."""
    def __reduce__(self):
        return (builtin_type, (builtin_type(self),))
    return __reduce__


def _try_register_yaml_representer(cls, base_type=None, value_fn=None):
    """Register *cls* with ruamel.yaml's SafeRepresenter and RoundTripRepresenter.

    No-op if ruamel.yaml is not installed.

    Parameters
    ----------
    cls : type
        The WithProvenance class to register.
    base_type : type or None
        Explicit base type to look up the representer for. If ``None``,
        uses ``_get_builtin_base(cls)``.
    value_fn : callable or None
        Called as ``value_fn(data)`` to produce the value passed to the
        base representer. If ``None``, passes *data* directly (works for
        subclassable builtins like ``str``, ``int``).
    """
    try:
        from ruamel.yaml.representer import SafeRepresenter, RoundTripRepresenter
    except ImportError:
        return
    for repr_class in (SafeRepresenter, RoundTripRepresenter):
        lookup_type = base_type if base_type is not None else _get_builtin_base(cls)
        fn = repr_class.yaml_representers.get(lookup_type)
        if fn:
            if value_fn is not None:
                repr_class.add_representer(
                    cls,
                    lambda dumper, data, _fn=fn, _vfn=value_fn: _fn(dumper, _vfn(data)),
                )
            else:
                repr_class.add_representer(cls, fn)


# ========================================================
# PROVENANCE WRAPPER FACTORY CLASS METHODS AND PROPERTIES
# ========================================================
@classmethod
def wrapper_with_provenance_new(cls, *args, **kwargs):
    """
    ``__new__`` method for WithProvenance classes. Required for ``copy.deepcopy``.
    """
    return super(cls, cls).__new__(cls, args[1])


def wrapper_with_provenance_init(self, value, provenance=None):
    """
    ``__init__`` method for WithProvenance classes. Adds the ``provenance``
    attribute as a ``Provenance`` instance.

    Parameters
    ----------
    value : any
        Value of the object.
    provenance : any
        The provenance information.
    """
    config = get_config()
    if isinstance(provenance, Provenance):
        self._provenance = provenance
    else:
        self._provenance = Provenance(provenance, track_history=config.track_history)
    self.value = value


@property
def prop_provenance(self):
    """Property getter for provenance."""
    return self._provenance


@prop_provenance.setter
def prop_provenance(self, new_provenance):
    """
    Setter for the ``provenance`` property. Ensures the value is a ``Provenance``
    instance.

    Raises
    ------
    ValueError
        If ``new_provenance`` is not a ``Provenance`` object.
    """
    if not isinstance(new_provenance, Provenance):
        raise ValueError(
            "Provenance must be an instance of the provenance.Provenance class!"
        )
    self._provenance = new_provenance


def wrapper_with_provenance_deepcopy(self, memo):
    """``__deepcopy__`` for WithProvenance subclasses.

    ``copy.deepcopy`` checks for ``__deepcopy__`` *before* falling back to
    ``__reduce__``.  The pickle reducers registered by
    The ``__reduce__`` method intentionally reduces to the plain builtin
    type (e.g. ``str``) so that pickle output is compact.  Without a
    ``__deepcopy__`` override, ``copy.deepcopy`` would use the same
    ``__reduce__`` path and silently discard provenance.
    """
    obj_id = id(self)
    if obj_id in memo:
        return memo[obj_id]
    new = wrapper_with_provenance_factory(
        type(self).__mro__[1](self),  # plain builtin value (str, int, …)
        copy.deepcopy(self._provenance, memo),
    )
    memo[obj_id] = new
    return new


# =======================================================
# CLASSES FOR THE UNSUBCLASSABLE CLASSES (BOOL AND NONE)
# =======================================================
class ProvenanceClassForTheUnsubclassable:
    """
    Base class for types that cannot be subclassed (``bool``, ``NoneType``).
    Stores the ``value`` and ``provenance`` attributes.
    """

    def __repr__(self):
        return f"{self.value}"

    def __bool__(self):
        return bool(self.value)

    def __eq__(self, other):
        if isinstance(other, BoolWithProvenance):
            return self.value == other.value
        return self.value == other

    def __hash__(self):
        return hash(self.value)


def _unsubclassable_deepcopy(self, memo):
    """``__deepcopy__`` for Bool/NoneWithProvenance."""
    obj_id = id(self)
    if obj_id in memo:
        return memo[obj_id]
    new = type(self)(self.value, copy.deepcopy(self._provenance, memo))
    memo[obj_id] = new
    return new


# Add the class attributes common to all WithProvenance classes
ProvenanceClassForTheUnsubclassable.__init__ = wrapper_with_provenance_init
ProvenanceClassForTheUnsubclassable.provenance = prop_provenance
ProvenanceClassForTheUnsubclassable.__deepcopy__ = _unsubclassable_deepcopy


class BoolWithProvenance(ProvenanceClassForTheUnsubclassable):
    """
    Class for emulating ``bool`` behaviour with provenance.

    ``isinstance(obj, bool)`` returns ``True``.
    """

    def __reduce__(self):
        return (bool, (self.value,))

    @property
    def __class__(self):
        return bool


class NoneWithProvenance(ProvenanceClassForTheUnsubclassable):
    """
    Class for emulating ``None`` behaviour with provenance.

    ``isinstance(obj, type(None))`` returns ``True``.
    """

    def __reduce__(self):
        return (type(None), ())

    @property
    def __class__(self):
        return type(None)


# ================================
# WRAPPER WITH PROVENANCE FACTORY
# ================================
def wrapper_with_provenance_factory(value, provenance=None):
    """
    Factory function that creates provenance-aware wrappers for any value type.

    For subclassable types, dynamically creates a ``{Type}WithProvenance`` subclass.
    For ``bool`` and ``NoneType`` (which cannot be subclassed), returns special
    wrapper instances. For types registered in ``config.custom_type_handlers``,
    delegates to the registered handler.

    Parameters
    ----------
    value : any
        Value to wrap with provenance.
    provenance : any
        The provenance information.

    Returns
    -------
    object
        The value wrapped with provenance tracking.
    """
    # Avoid circular import
    from ._dict import DictWithProvenance
    from ._list import ListWithProvenance
    PROVENANCE_MAPPINGS = (DictWithProvenance, ListWithProvenance)

    config = get_config()

    # Check custom type handlers first
    value_type = type(value)
    if value_type in config.custom_type_handlers:
        return config.custom_type_handlers[value_type](value, provenance)

    if value_type == bool:
        return BoolWithProvenance(value, provenance)

    elif value is None:
        # Return plain None so that `x is None` identity checks work as expected.
        # NoneWithProvenance breaks Python's idiomatic `is None` test (PEP 8).
        # Provenance on a None value is inaccessible anyway (None has no attributes).
        return None

    elif isinstance(value, PROVENANCE_MAPPINGS):
        return value

    else:
        subtype = type(value)
        class_name = f"{subtype}".split("'")[1]
        class_name = f"{class_name[0].upper()}{class_name[1:]}WithProvenance"

        if class_name not in _wrapper_registry:
            _wrapper_registry[class_name] = type(
                class_name,
                (subtype,),
                {
                    "_class_name": class_name,
                    "__new__": wrapper_with_provenance_new,
                    "__init__": wrapper_with_provenance_init,
                    "provenance": prop_provenance,
                    "__deepcopy__": wrapper_with_provenance_deepcopy,
                    "__reduce__": _make_pickle_reduce(_get_builtin_base(subtype)),
                },
            )
            _try_register_yaml_representer(_wrapper_registry[class_name])

        return _wrapper_registry[class_name](value, provenance)


# Register YAML representers for the unsubclassable types at definition time
_try_register_yaml_representer(BoolWithProvenance, base_type=bool, value_fn=lambda d: d.value)
_try_register_yaml_representer(NoneWithProvenance, base_type=type(None), value_fn=lambda d: None)


def get_wrapper_class(class_name):
    """
    Get a dynamically created WithProvenance class by name.

    Parameters
    ----------
    class_name : str
        The class name (e.g. ``"StrWithProvenance"``).

    Returns
    -------
    type or None
        The class, or ``None`` if not yet created.
    """
    return _wrapper_registry.get(class_name)
