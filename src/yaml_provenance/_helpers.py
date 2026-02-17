"""
Helper functions for provenance operations.
"""


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
