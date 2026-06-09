"""
YAML loader with provenance tracking.

Provides ``ProvenanceConstructor`` which captures file, line, and column
information for every value during YAML parsing.
"""

import os
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.constructor import RoundTripConstructor

from ._config import get_config
from ._dict import DictWithProvenance
from ._wrapper import wrapper_with_provenance_factory as _wrap


class ProvenanceConstructor(RoundTripConstructor):
    """
    A YAML constructor that captures provenance (line, column) for every node.

    Instead of returning plain values, returns ``(data, (line, col))`` tuples.
    These can then be split into a data dict and a provenance dict for use
    with ``DictWithProvenance``.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def construct_object(self, node, *args, **kwargs):
        data = super().construct_object(node, *args, **kwargs)
        provenance = (
            node.start_mark.line + 1,
            node.start_mark.column + 1,
        )
        return (data, provenance)


def _is_prov_tuple(val):
    """Check if a value is a (data, (line, col)) provenance tuple."""
    return (
        isinstance(val, tuple)
        and len(val) == 2
        and isinstance(val[1], tuple)
        and len(val[1]) == 2
        and isinstance(val[1][0], int)
        and isinstance(val[1][1], int)
    )


class ProvenanceLoader:
    """
    High-level YAML loader that produces ``DictWithProvenance`` objects.

    Parameters
    ----------
    category_resolver : callable or None
        A function ``(filepath: str) -> (category, subcategory)`` that maps
        file paths to categories. Default: returns ``(None, None)``.
    config : ProvenanceConfig or None
        Configuration for provenance tracking. If ``None``, uses module default.
    """

    def __init__(self, category_resolver=None, config=None):
        self._category_resolver = category_resolver or (lambda f: (None, None))
        self._config = config or get_config()
        self._yaml = YAML()
        self._yaml.Constructor = ProvenanceConstructor

    def load(self, filepath):
        """
        Load a YAML file and return a ``DictWithProvenance``.

        Parameters
        ----------
        filepath : str, Path, or file-like
            Path to the YAML file, or an open file object with a ``.name``
            attribute.

        Returns
        -------
        DictWithProvenance
            The loaded data with provenance tracking.
        """
        # Accept file-like objects by extracting their path.
        # pathlib.Path also has a ``.name`` attribute (the final component),
        # so we must exclude it to preserve the full path.
        if hasattr(filepath, 'name') and not isinstance(filepath, Path):
            filepath = filepath.name
        filepath = str(filepath)
        category, subcategory = self._category_resolver(filepath)

        with open(filepath, "r") as f:
            raw = self._yaml.load(f)

        if raw is None:
            return DictWithProvenance({}, {}, config=self._config)

        # The root node is also wrapped: (dict_with_tuples, (line, col))
        if _is_prov_tuple(raw):
            raw = raw[0]

        data, provenance = self._split_dict(raw, filepath, category, subcategory)

        return DictWithProvenance(data, provenance, config=self._config)

    def _split_dict(self, raw_dict, filepath, category, subcategory):
        """
        Recursively split a dict whose keys and values are provenance tuples
        into separate data and provenance dicts.
        """
        data = {}
        prov = {}

        for raw_key, raw_val in raw_dict.items():
            # Unwrap key — wrap string keys with provenance so that
            # even entries whose *values* are empty dicts or lists
            # still carry a provenance trace (on the key itself).
            if _is_prov_tuple(raw_key):
                raw_key_val = raw_key[0]
                key_line, key_col = raw_key[1]
                key = _wrap(raw_key_val, {
                    "line": key_line, "col": key_col,
                    "yaml_file": filepath,
                    "category": category,
                    "subcategory": subcategory,
                })
            else:
                key = raw_key

            # Unwrap value
            if _is_prov_tuple(raw_val):
                val, (line, col) = raw_val

                if isinstance(val, dict):
                    data[key], prov[key] = self._split_dict(
                        val, filepath, category, subcategory
                    )
                elif isinstance(val, list):
                    data[key], prov[key] = self._split_list(
                        val, filepath, category, subcategory
                    )
                else:
                    data[key] = val
                    prov[key] = {
                        "line": line,
                        "col": col,
                        "yaml_file": filepath,
                        "category": category,
                        "subcategory": subcategory,
                    }
            else:
                data[key] = raw_val
                prov[key] = {}

        return data, prov

    def _split_list(self, raw_list, filepath, category, subcategory):
        """
        Recursively split a list whose elements are provenance tuples.
        """
        data = []
        prov = []

        for item in raw_list:
            if _is_prov_tuple(item):
                val, (line, col) = item

                if isinstance(val, dict):
                    d, p = self._split_dict(val, filepath, category, subcategory)
                    data.append(d)
                    prov.append(p)
                elif isinstance(val, list):
                    d, p = self._split_list(val, filepath, category, subcategory)
                    data.append(d)
                    prov.append(p)
                else:
                    data.append(val)
                    prov.append({
                        "line": line,
                        "col": col,
                        "yaml_file": filepath,
                        "category": category,
                        "subcategory": subcategory,
                    })
            else:
                data.append(item)
                prov.append({})

        return data, prov


def load_yaml(filepath, category_resolver=None, config=None):
    """
    Convenience function to load a YAML file with provenance tracking.

    Parameters
    ----------
    filepath : str, Path, or file-like
        Path to the YAML file, or an open file object with a ``.name``
        attribute.
    category_resolver : callable or None
        Maps file paths to ``(category, subcategory)`` tuples.
    config : ProvenanceConfig or None
        Configuration for provenance tracking.

    Returns
    -------
    DictWithProvenance
        The loaded data with provenance.
    """
    loader = ProvenanceLoader(category_resolver=category_resolver, config=config)
    return loader.load(filepath)
