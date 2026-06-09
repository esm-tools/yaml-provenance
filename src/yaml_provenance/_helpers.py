"""
Helper functions for provenance operations.
"""

from ._wrapper import wrapper_with_provenance_factory


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
    Wrap every scalar leaf of *d* with a per-key provenance source in-place.

    For each key ``K``, the source is ``<source_prefix>.<K>``.
    Recurses into nested dicts.  Leaves that already carry provenance are
    left untouched.

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
        if isinstance(value, dict):
            annotate_dict(value, source_prefix)
        elif not hasattr(value, "provenance"):
            d[key] = wrap_computed(value, f"{source_prefix}.{key}")
    return d
