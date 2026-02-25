"""
yaml-provenance: Track where every value in your YAML configuration came from.

This library provides two complementary approaches for provenance tracking:

1. **Wrapper Pattern** (original approach, 83% coverage):
   - Attaches provenance to values via subclassing
   - Provenance travels with values
   - Use load_yaml() to load with wrappers
   - Best for post-normalization tracking

2. **Registry Pattern** (new approach, 100% coverage):
   - Stores provenance separately in flat dictionary
   - Independent of data structures
   - Use load_yaml_with_tracking() to get (data, tracker)
   - Best for pre-normalization tracking

Example - Wrapper Pattern:
    >>> from yaml_provenance import load_yaml
    >>> config = load_yaml("config.yml")
    >>> print(config["key"].provenance[-1])  # Provenance attached to value

Example - Registry Pattern:
    >>> from yaml_provenance import load_yaml_with_tracking
    >>> data, tracker = load_yaml_with_tracking("config.yml")
    >>> prov = tracker.get("section.key")  # Provenance stored separately
    >>> print(f"From {prov.file} at line {prov.line}")

Both approaches can be used together or independently depending on your needs.
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
from ._helpers import clean_provenance
from .yaml_loader import ProvenanceConstructor, ProvenanceLoader, load_yaml
from ._yaml_dumper import dump_yaml

# Registry Pattern imports (new)
from .tracker import ProvenanceTracker, ProvEntry
from .tracking_helpers import (
    load_yaml_with_tracking,
    track_yaml_provenance,
    track_dict_keys_only,
    track_computed_parameter,
)

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
    # YAML I/O (Wrapper Pattern)
    "ProvenanceConstructor",
    "ProvenanceLoader",
    "load_yaml",
    "dump_yaml",
    # Registry Pattern (new)
    "ProvenanceTracker",
    "ProvEntry",
    "load_yaml_with_tracking",
    "track_yaml_provenance",
    "track_dict_keys_only",
    "track_computed_parameter",
]

__version__ = "0.1.0"
