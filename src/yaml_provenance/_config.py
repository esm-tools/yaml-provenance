"""
Global configuration for yaml-provenance.
"""

from loguru import logger

# Module-level default config, set via configure()
_default_config = None


class ProvenanceConfig:
    """
    Configuration for provenance tracking behavior.

    Parameters
    ----------
    category_hierarchy : list or None
        Ordered list of category names from lowest to highest priority.
        Default: ``[None]`` (single level, no hierarchy enforcement).
    on_conflict : str
        What to do when two values at the same hierarchy level conflict.
        One of ``"raise"``, ``"warn"``, or ``"ignore"``. Default: ``"raise"``.
    track_history : bool
        Whether to keep the full provenance history. When ``False`` (default),
        provenance lists have at most 1 element for minimal overhead.
    custom_type_handlers : dict or None
        Mapping of ``{type: callable(value, provenance) -> wrapped}`` for types
        that cannot be dynamically subclassed (e.g. custom Date classes).
    conflict_resolver : callable or None
        A callback ``(key, old_val, new_val, old_prov, new_prov) -> action`` for
        custom conflict resolution. Return ``"raise"``, ``"keep_old"``,
        ``"keep_new"``, or ``"ignore"``. If ``None``, uses the default behavior
        based on ``on_conflict``.
    """

    def __init__(
        self,
        category_hierarchy=None,
        on_conflict="raise",
        track_history=False,
        custom_type_handlers=None,
        conflict_resolver=None,
    ):
        if category_hierarchy is None:
            category_hierarchy = [None]
        self.category_hierarchy = category_hierarchy
        self.on_conflict = on_conflict
        self.track_history = track_history
        self.custom_type_handlers = custom_type_handlers or {}
        self.conflict_resolver = conflict_resolver

    def __repr__(self):
        return (
            f"ProvenanceConfig(category_hierarchy={self.category_hierarchy!r}, "
            f"on_conflict={self.on_conflict!r}, "
            f"track_history={self.track_history!r})"
        )


def configure(config=None):
    """
    Set the module-level default ``ProvenanceConfig``.

    Parameters
    ----------
    config : ProvenanceConfig or None
        The configuration to use as default. If ``None``, resets to default.
    """
    global _default_config
    _default_config = config


def get_config():
    """
    Get the current module-level default config, creating one if needed.

    Returns
    -------
    ProvenanceConfig
    """
    global _default_config
    if _default_config is None:
        _default_config = ProvenanceConfig()
    return _default_config
