"""
Helper functions for provenance operations.
"""


def clean_provenance(data, key_transform=None):
    """
    Recursively strips provenance from data, returning plain Python objects.

    Parameters
    ----------
    data : any
        Mapping or values with provenance.
    key_transform : callable, optional
        Applied to each cleaned dict key before it is inserted into the result.
        Useful for callers that need to remap keys (e.g. f90nml cogroups).

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
        return [clean_provenance(item, key_transform=key_transform) for item in data]
    elif isinstance(data, dict):
        result = {}
        for key, value in data.items():
            cleaned_key = clean_provenance(key, key_transform=key_transform)
            dict_key = key_transform(cleaned_key) if key_transform else cleaned_key
            result[dict_key] = clean_provenance(value, key_transform=key_transform)
        return result
    # Clean vars in objects
    elif hasattr(data, "__dict__"):
        for key, value in vars(data).items():
            setattr(data, key, clean_provenance(value, nested=True))
        return data
    else:
        return data
