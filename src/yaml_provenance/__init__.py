"""
yaml-provenance: Track where every value in your YAML configuration came from.
"""

from ._config import ProvenanceConfig, configure, get_config
from ._exceptions import CategoryConflictError, ProvenanceError
from ._provenance import Provenance
from ._wrapper import (
    BoolWithProvenance,
    NoneWithProvenance,
    wrapper_with_provenance_factory,
    get_wrapper_class,
)
from ._dict import DictWithProvenance
from ._list import ListWithProvenance
from ._decorator import keep_provenance_in_recursive_function
from ._helpers import clean_provenance, wrap_computed, transfer_provenance, annotate_dict
from .yaml_loader import ProvenanceConstructor, ProvenanceLoader, load_yaml
from ._yaml_dumper import dump_yaml
from ._serialization import ProvenanceJSONEncoder

__all__ = [
    # Config
    "ProvenanceConfig",
    "configure",
    "get_config",
    # Exceptions
    "ProvenanceError",
    "CategoryConflictError",
    # Core
    "Provenance",
    "wrapper_with_provenance_factory",
    "get_wrapper_class",
    "BoolWithProvenance",
    "NoneWithProvenance",
    # Mappings
    "DictWithProvenance",
    "ListWithProvenance",
    # Decorator
    "keep_provenance_in_recursive_function",
    # Helpers
    "clean_provenance",
    "wrap_computed",
    "transfer_provenance",
    "annotate_dict",
    # Serialization
    "ProvenanceJSONEncoder",
    # YAML I/O
    "ProvenanceConstructor",
    "ProvenanceLoader",
    "load_yaml",
    "dump_yaml",
]

__version__ = "0.1.0"
