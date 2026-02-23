"""
DictWithProvenance — a dictionary subclass with provenance tracking.
"""

import copy

from loguru import logger

from ._config import get_config
from ._exceptions import CategoryConflictError
from ._provenance import Provenance
from ._wrapper import wrapper_with_provenance_factory


class DictWithProvenance(dict):
    """
    A dictionary subclass that tracks provenance for all nested values.

    Features:
    - Recursively transforms leaf values into provenance-aware objects
    - Extends ``__setitem__`` to preserve provenance history
    - Optionally enforces category hierarchy when configured
    - Extends ``update`` to preserve provenance history

    Parameters
    ----------
    dictionary : dict
        The dictionary to wrap with provenance.
    provenance : dict
        Provenance data with matching structure to ``dictionary``.
    config : ProvenanceConfig or None
        Configuration. If ``None``, uses the module-level default.
    """

    def __init__(self, dictionary, provenance, config=None):
        super().__init__(dictionary)
        self._config = config or get_config()
        self.custom_setitem = False
        self.put_provenance(provenance)
        self.custom_setitem = True

    def put_provenance(self, provenance):
        """
        Recursively transforms every value into its WithProvenance object with
        corresponding provenance from the ``provenance`` dict (1-to-1 mapping).

        Parameters
        ----------
        provenance : dict
            Provenance dict with same keys as ``self``.
        """
        from ._list import ListWithProvenance

        # Guard against None provenance
        if provenance is None:
            provenance = {}

        for key, val in self.items():
            if isinstance(val, dict):
                self[key] = DictWithProvenance(
                    val, provenance.get(key, {}) or {}, config=self._config
                )
            elif isinstance(val, list):
                self[key] = ListWithProvenance(
                    val, provenance.get(key, []) or [], config=self._config
                )
            elif hasattr(val, "provenance"):
                # Get provenance value for this key
                prov_val = provenance.get(key, {})
                # Only extend if prov_val is not None/empty
                if prov_val:
                    if isinstance(prov_val, list):
                        # If it's a list, extend with it
                        self[key].provenance.extend(prov_val)
                    else:
                        # If it's a single dict/other, append it (don't extend which adds keys as strings)
                        self[key].provenance.append(prov_val)
            else:
                self[key] = wrapper_with_provenance_factory(
                    val, provenance.get(key, None)
                )

    def set_provenance(self, provenance):
        """
        Recursively sets the same ``provenance`` on all nested values.

        Parameters
        ----------
        provenance : any
            New provenance value to set.
        """
        from ._list import ListWithProvenance

        if not isinstance(provenance, list):
            provenance = [provenance]

        for key, val in self.items():
            if isinstance(val, dict):
                self[key] = DictWithProvenance(val, {}, config=self._config)
                self[key].set_provenance(provenance)
            elif isinstance(val, list):
                self[key] = ListWithProvenance(val, [], config=self._config)
                self[key].set_provenance(provenance)
            elif hasattr(val, "provenance"):
                self[key].provenance.extend(provenance)
            else:
                self[key] = wrapper_with_provenance_factory(val, provenance)

    def get_provenance(self, index=-1):
        """
        Returns a dictionary of provenance information with matching structure.

        Parameters
        ----------
        index : int
            Index into the provenance history. Default: ``-1`` (last/current).

        Returns
        -------
        dict
            Provenance dictionary.
        """
        from ._list import ListWithProvenance
        PROVENANCE_MAPPINGS = (DictWithProvenance, ListWithProvenance)

        provenance_dict = {}
        for key, val in self.items():
            if isinstance(val, PROVENANCE_MAPPINGS):
                provenance_dict[key] = val.get_provenance(index=index)
            elif hasattr(val, "provenance"):
                provenance_dict[key] = val.provenance[index]
            else:
                provenance_dict[key] = None

        return provenance_dict

    def _has_real_hierarchy(self):
        """Check if the config has a non-trivial category hierarchy."""
        return len(self._config.category_hierarchy) > 1

    def __setitem__(self, key, val):
        """
        Extended ``__setitem__`` that preserves provenance history.

        When a category hierarchy is configured (more than just ``[None]``),
        also enforces category-based conflict resolution and hierarchy ordering.

        Raises
        ------
        CategoryConflictError
            If values at the same hierarchy level conflict (only when hierarchy
            is configured and ``on_conflict="raise"``).
        """
        val_new = val
        config = self._config

        if (
            key in self
            and not isinstance(self[key], (dict, list))
            and hasattr(self[key], "provenance")
            and hasattr(self, "custom_setitem")
            and self.custom_setitem
        ):
            old_val = self[key]
            old_prov = old_val.provenance

            # Capture categories BEFORE extending provenance (extend mutates)
            if old_prov[-1] and isinstance(old_prov[-1], dict):
                old_category = old_prov[-1].get("category", None)
            elif not old_prov[-1]:
                old_category = "backend"
            else:
                # old_prov[-1] is truthy but not a dict (e.g., string)
                old_category = None

            new_category = None
            if hasattr(val, "provenance") and val.provenance and val.provenance[-1]:
                if isinstance(val.provenance[-1], dict):
                    new_category = val.provenance[-1].get("category", None)

            # new_provenance is the same object as old_prov (a reference)
            new_provenance = old_prov

            if hasattr(val, "provenance"):
                new_provenance.extend_and_modified_by(
                    val.provenance, "dict.__setitem__"
                )

                if self._has_real_hierarchy():
                    hierarchy = config.category_hierarchy

                    if old_category in hierarchy and new_category in hierarchy:
                        old_idx = hierarchy.index(old_category)
                        new_idx = hierarchy.index(new_category)

                        if old_idx == new_idx and old_val != val:
                            # Same category — conflict
                            if config.conflict_resolver is not None:
                                action = config.conflict_resolver(
                                    key, old_val, val, old_prov, new_provenance
                                )
                                if action == "raise":
                                    raise CategoryConflictError(
                                        f"Key '{key}' exists at the same hierarchical "
                                        f"level ('{old_category}') with different values "
                                        f"('{old_val}':'{val}').",
                                        key=key, old_val=old_val, new_val=val,
                                        category=old_category,
                                        old_provenance=old_prov,
                                        new_provenance=new_provenance,
                                    )
                                elif action == "keep_old":
                                    val_new = copy.deepcopy(old_val) if config.track_history else old_val
                                elif action == "keep_new":
                                    val_new = copy.deepcopy(val) if config.track_history else val
                                else:
                                    val_new = val
                            elif config.on_conflict == "raise":
                                raise CategoryConflictError(
                                    f"Key '{key}' exists at the same hierarchical level "
                                    f"('{old_category}') with different values "
                                    f"('{old_val}':'{val}').",
                                    key=key, old_val=old_val, new_val=val,
                                    category=old_category,
                                    old_provenance=old_prov,
                                    new_provenance=new_provenance,
                                )
                            elif config.on_conflict == "warn":
                                logger.warning(
                                    f"Key '{key}' conflict at level '{old_category}': "
                                    f"'{old_val}' -> '{val}'"
                                )
                                val_new = copy.deepcopy(val) if config.track_history else val
                            else:
                                val_new = copy.deepcopy(val) if config.track_history else val

                        elif old_idx < new_idx or old_val is None:
                            # New category is higher — allow overwrite
                            val_new = copy.deepcopy(val) if config.track_history else val

                        else:
                            # Old category is higher — keep old value
                            val_new = copy.deepcopy(old_val) if config.track_history else old_val
                            new_provenance.extend_and_modified_by(
                                Provenance(
                                    {"category": old_category},
                                    track_history=config.track_history,
                                ),
                                "dict.__setitem__->reverted_by_hierarchy",
                            )
                            logger.trace(
                                f"Value {val} won't be assigned to key {key}, because "
                                f"the old value {old_val} comes from a category higher "
                                f"in the hierarchy ({old_val}:{old_category} > "
                                f"{val}:{new_category})"
                            )

                    val_new.provenance = new_provenance
                else:
                    # Simple mode: just extend provenance, no hierarchy checks
                    val_new = copy.deepcopy(val) if config.track_history else val
                    val_new.provenance = new_provenance

        super().__setitem__(key, val_new)

    def super_setitem(self, key, val):
        """
        Call the original ``dict.__setitem__`` without provenance tracking.
        """
        super().__setitem__(key, val)

    def update(self, dictionary, *args, **kwargs):
        """
        Extends ``dict.update`` to preserve provenance history.

        Parameters
        ----------
        dictionary : dict
            Dictionary to update from.
        """
        new_provs = {}

        for key, val in dictionary.items():
            if (
                key in self
                and not isinstance(self[key], (dict, list))
                and hasattr(self[key], "provenance")
                and hasattr(self, "custom_setitem")
                and self.custom_setitem
            ):
                new_provenance = self[key].provenance
                if hasattr(val, "provenance"):
                    new_provenance.extend_and_modified_by(val.provenance, "dict.update")
                    new_provs[key] = new_provenance

        super().update(dictionary, *args, **kwargs)

        for key, val in new_provs.items():
            self[key].provenance = val
