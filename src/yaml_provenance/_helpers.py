"""
Helper functions for provenance operations.
"""

from ._wrapper import wrapper_with_provenance_factory, NoneWithProvenance


def clean_provenance(data):
    """
    Recursively strips provenance from data, returning plain Python objects.

    Parameters
    ----------
    data : any
        Mapping or values with provenance.

    Returns
    -------
    any
        Values in their original format without provenance.
    """
    if hasattr(data, "value"):
        assert (
            data == data.value
        ), "The provenance object's value and the original value do not match!"
        return data.value
    elif isinstance(data, list):
        return [clean_provenance(item) for item in data]
    elif isinstance(data, dict):
        return {
            clean_provenance(key): clean_provenance(value)
            for key, value in data.items()
        }
    else:
        return data


def is_none_like(value):
    """
    True if *value* is ``None`` or a ``NoneWithProvenance`` wrapper.

    Use in place of ``x is None`` for values that may carry provenance:
    ``NoneWithProvenance is None`` is always ``False`` by design (it is a
    distinct object), so identity checks miss provenance-wrapped nulls.

    Parameters
    ----------
    value : any
        The value to test.

    Returns
    -------
    bool
        ``True`` for ``None`` and ``NoneWithProvenance``, ``False`` otherwise.
    """
    return value is None or isinstance(value, NoneWithProvenance)


def wrap_computed(value, source):
    """
    Wrap a value with provenance pointing to *source*.

    Used to give meaningful provenance to values injected programmatically
    (not loaded from a YAML file), such as environment variables, computed
    parameters, or configuration attributes.

    The *source* string is placed in the ``yaml_file`` field of the provenance.

    Parameters
    ----------
    value : any
        The value to annotate.
    source : str
        Human-readable source description.

    Returns
    -------
    object
        Provenance-wrapped value.
    """
    provenance = {
        "yaml_file": source,
        "line": 0,
        "col": 0,
        "category": None,
        "subcategory": None,
    }
    return wrapper_with_provenance_factory(value, provenance)


def transfer_provenance(original, result):
    """
    Return *result* wrapped with the provenance of *original*.

    Used when a string operation (``str.upper()``, ``str.strip()``, etc.)
    produces a plain ``str`` from a WithProvenance subclass, discarding the
    provenance.  This re-attaches the original provenance to the new value.

    If *original* has no provenance, returns *result* unchanged.

    Parameters
    ----------
    original : any
        The WithProvenance source value (before the operation).
    result : any
        The plain result of the operation.

    Returns
    -------
    object
        *result* with *original*'s full provenance history, or *result* as-is.
    """
    prov = getattr(original, "provenance", None)
    if not prov:
        return result
    return wrapper_with_provenance_factory(result, prov)


def annotate_dict(d, source_prefix):
    """
    Give every scalar leaf of *d* synthetic provenance recording its source.

    Purpose: values injected programmatically (env vars, computed defaults,
    CLI overrides) never passed through the YAML loader, so they carry no
    provenance.  This walks *d* and tags each leaf with a per-key source
    (e.g. ``myapp.config.key1``) so those values still appear with a
    meaningful origin in provenance dumps instead of ``"no provenance"``.

    For each key ``K``, the source is ``<source_prefix>.<K>``.
    Keys that contain a ``.`` are quoted (e.g. ``prefix["a.b"]``) to avoid
    ambiguity with nested-key notation.
    Recurses into nested dicts and lists (list elements use ``[i]`` in the
    source).  Leaves that already carry provenance are left untouched.

    Parameters
    ----------
    d : dict
        Dict to annotate (modified in-place and returned).
    source_prefix : str
        Base source string (e.g. ``"myapp.config"``).

    Returns
    -------
    dict
        The annotated dict.
    """
    for key, value in d.items():
        key_str = str(key)
        source_key = f'["{key_str}"]' if "." in key_str else f".{key_str}"
        source = f"{source_prefix}{source_key}"
        if isinstance(value, dict):
            annotate_dict(value, source)
        elif isinstance(value, list):
            _annotate_list(value, source)
        elif not hasattr(value, "provenance"):
            d[key] = wrap_computed(value, source)
    return d


def _annotate_list(lst, source_prefix):
    """
    Annotate list elements in-place, recursing into nested dicts and lists.

    Counterpart to :func:`annotate_dict` for list values.  Element ``i`` uses
    the source ``<source_prefix>[i]``.  Without this, a list handed to
    ``wrap_computed`` would be mangled into an empty wrapper (data loss).
    """
    for i, item in enumerate(lst):
        source = f"{source_prefix}[{i}]"
        if isinstance(item, dict):
            annotate_dict(item, source)
        elif isinstance(item, list):
            _annotate_list(item, source)
        elif not hasattr(item, "provenance"):
            lst[i] = wrap_computed(item, source)
