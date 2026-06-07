"""
WithProvenance wrapper factory — creates provenance-aware subclasses dynamically.
"""

from ._provenance import Provenance
from ._config import get_config


# Registry of dynamically created WithProvenance classes
_wrapper_registry = {}

# Populated on first call to wrapper_with_provenance_factory to avoid circular imports
_PROVENANCE_MAPPINGS = None


# ========================================================
# PROVENANCE WRAPPER FACTORY CLASS METHODS AND PROPERTIES
# ========================================================
@classmethod
def wrapper_with_provenance_new(cls, *args, **kwargs):
    """
    ``__new__`` method for WithProvenance classes. Required for ``copy.deepcopy``,
    without this ``copy.deepcopy`` breaks.
    """
    return super(cls, cls).__new__(cls, args[1])


def wrapper_with_provenance_init(self, value, provenance=None):
    """
    ``__init__`` method for WithProvenance classes. Adds the ``provenance``
    attribute as a ``Provenance`` instance. It also stores the original ``value`` to the
    ``self.value`` attribute.

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
    """
    Property getter for provenance.

    Returns
    -------
    self._provenance : esm_parser.provenance.Provenance
        The provenance history stored in ``self._provenance``
    """
    return self._provenance


@prop_provenance.setter
def prop_provenance(self, new_provenance):
    """
    Setter for the ``provenance`` property. Ensures the value is a ``Provenance``
    instance.

    Parameters
    ----------
    new_provenance : esm_parser.provenance.Provenance
        New provenance history to be set

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


# Add the class attributes common to all WithProvenance classes
ProvenanceClassForTheUnsubclassable.__init__ = wrapper_with_provenance_init
ProvenanceClassForTheUnsubclassable.provenance = prop_provenance


class BoolWithProvenance(ProvenanceClassForTheUnsubclassable):
    """
    Class for emulating ``bool`` behaviour with provenance.

    * ``isinstance(<obj>, bool)`` returns ``True``
    * ``<True_obj> == True`` returns ``True``
    * ``<True_obj> is True`` returns ``False``. This is not reproducing the behavior!
    """

    @property
    def __class__(self):
        return bool


class NoneWithProvenance(ProvenanceClassForTheUnsubclassable):
    """
    Class for emulating ``None`` behaviour with provenance.

    * ``isinstance(<obj>, None)`` returns ``True``
    * ``<obj> == None`` returns ``True``
    * ``<obj> is None`` returns ``False``. This is not reproducing the behavior!
    """

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
    global _PROVENANCE_MAPPINGS
    if _PROVENANCE_MAPPINGS is None:
        from ._dict import DictWithProvenance
        from ._list import ListWithProvenance
        _PROVENANCE_MAPPINGS = (DictWithProvenance, ListWithProvenance)

    config = get_config()

    # Check custom type handlers first
    value_type = type(value)
    if value_type in config.custom_type_handlers:
        return config.custom_type_handlers[value_type](value, provenance)

    if value_type == bool:
        return BoolWithProvenance(value, provenance)

    elif value is None:
        return NoneWithProvenance(value, provenance)

    elif isinstance(value, _PROVENANCE_MAPPINGS):
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
                },
            )

        # Instantiate the subclass with the given value and provenance
        return _wrapper_registry[class_name](value, provenance)


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
