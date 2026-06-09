"""
Serialization support for yaml-provenance wrapper types.

Provides a JSON encoder so that WithProvenance objects can be serialized
by the standard library without errors. YAML representers and pickle reducers
are registered automatically at class-creation time in ``_wrapper.py``,
``_dict.py``, and ``_list.py``.
"""

import json

from ._wrapper import ProvenanceClassForTheUnsubclassable


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
