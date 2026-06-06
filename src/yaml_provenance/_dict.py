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
        Recursively transforms every value in ``DictWithProvenance`` into its
        corresponding WithProvenance object and appends its corresponding
        ``provenance``. Each value has its corresponding provenance defined in the
        ``provenance`` dictionary, and this method just groups them together 1-to-1.

        Parameters
        ----------
        provenance : dict
            The provenance that will be recursively assigned to all leaves of the
            dictionary tree. The provenance needs to be a ``dict`` with the same keys
            as ``self`` (same structure) so that it can successfully transfer each
            provenance value to its corresponding value on ``self`` (1-to-1
            conrrespondance).
        """

        for key, val in self.items():
            if isinstance(val, dict):
                self[key] = DictWithProvenance(
                    val, provenance.get(key, {}), config=self._config
                )
            elif isinstance(val, list):
                self[key] = ListWithProvenance(
                    val, provenance.get(key, []), config=self._config
                )
            elif hasattr(val, "provenance"):
                self[key].provenance.extend(provenance.get(key, {}))
            else:
                self[key] = wrapper_with_provenance_factory(
                    val, provenance.get(key, None)
                )

    def set_provenance(self, provenance, update_method="extend"):
        """
        Recursively transforms every value in ``DictWithProvenance`` into its
        corresponding WithProvenance object and appends the same ``provenance`` to it.
        Note that this method differs from ``put_provenance`` in that the same
        ``provenance`` value is applied to the different values of ``self``.

        Parameters
        ----------
        provenance : any
            New `provenance value` to be set
        update_method : str, optional
            Method to use when updating provenance of existing values. Can be either
            ``extend`` to append the new provenance to the existing one, or ``update``
            to update the last provenance entry with new values. Default is ``extend``.
        """
        if not isinstance(provenance, list):
            provenance = [provenance]

        for key, val in self.items():
            if isinstance(val, dict):
                self[key] = DictWithProvenance(val, {}, config=self._config)
                self[key].set_provenance(provenance, update_method=update_method)
            elif isinstance(val, list):
                self[key] = ListWithProvenance(val, [], config=self._config)
                self[key].set_provenance(provenance, update_method=update_method)
            elif hasattr(val, "provenance"):
                if update_method == "extend":
                    self[key].provenance.extend(provenance)
                elif update_method == "update":
                    if self[key].provenance[-1]:
                        self[key].provenance[-1].update(provenance[-1])
                    else:
                        self[key].provenance[-1] = provenance[-1]
                elif update_method == "update_from_switch":
                    if self[key].provenance[-1]:
                        old_from_switch = (
                            self[key].provenance[-1].get("from_switch", [])
                        )
                        # Extend the from_switch list with the new entry
                        if old_from_switch:
                            provenance[-1]["from_switch"] = (
                                old_from_switch + provenance[-1].get("from_switch", [])
                            )
                        self[key].provenance[-1].update(provenance[-1])
                    else:
                        self[key].provenance[-1] = provenance[-1]
                else:
                    raise ValueError(
                        f"Unknown update method {update_method}. Use either 'extend' or 'update'"
                    )
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
        provenance_dict : dict
            A dictionary with a structure and `keys` equivalent to the ``self``
            dictionary, but with `values` of the `key` leaves those of the provenance
        """

        provenance_dict = {}

        for key, val in self.items():
            if isinstance(val, PROVENANCE_MAPPINGS):
                provenance_dict[key] = val.get_provenance(index=index)
            elif hasattr(val, "provenance"):
                provenance_dict[key] = val.provenance[index]
            else:
                # The DictWithProvenance object might have dictionaries inside that
                # are not instances of that class (i.e. a dictionary added in the
                # backend). The provenance in this method is then defined as None
                provenance_dict[key] = None

        return provenance_dict

    def _has_real_hierarchy(self):
        """Check if the config has a non-trivial category hierarchy."""
        return len(self._config.category_hierarchy) > 1

    def extract_first_nested_values_provenance(self):
        """
        Recursively loops through the dictionary keys and returns the first provenance
        found in the nested values.

        Returns
        -------
        first_provenance : esm_parser.provenance.Provenance
            The first provenance found in the nested values
        """
        first_provenance = None
        for key, val in self.items():
            if isinstance(val, PROVENANCE_MAPPINGS):
                return val.extract_first_nested_values_provenance()
            elif hasattr(val, "provenance"):
                return val.provenance[-1]

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
            if old_prov[-1]:
                old_category = old_prov[-1].get("category", None)
            else:
                old_category = "backend"

            new_category = "backend"
            if hasattr(val, "provenance") and val.provenance and val.provenance[-1]:
                new_category = val.provenance[-1].get("category", None)

            # new_provenance is the same object as old_prov (a reference)
            new_provenance = old_prov

            # If the new value has provenance extend its provenance with the old one
            if hasattr(val, "provenance"):
                new_provenance.extend_and_modified_by(
                    val.provenance, "dict.__setitem__"
                )

                if self._has_real_hierarchy():
                    hierarchy = config.category_hierarchy

                    if old_category in hierarchy and new_category in hierarchy:
                        old_idx = hierarchy.index(old_category)
                        new_idx = hierarchy.index(new_category)

                        # Handle conflicts if the categories are the same
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


from ._list import ListWithProvenance  # noqa: E402 — deferred to break circular import

PROVENANCE_MAPPINGS = (DictWithProvenance, ListWithProvenance)
