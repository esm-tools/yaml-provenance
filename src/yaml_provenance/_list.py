"""
ListWithProvenance — a list subclass with provenance tracking.
"""

import copy

from ._config import get_config
from ._provenance import Provenance
from ._wrapper import wrapper_with_provenance_factory


class ListWithProvenance(list):
    """
    A list subclass that tracks provenance for all nested values.

    Parameters
    ----------
    mylist : list
        The list to wrap with provenance.
    provenance : list
        Provenance data with matching structure to ``mylist``.
    config : ProvenanceConfig or None
        Configuration. If ``None``, uses the module-level default.
    """

    def __init__(self, mylist, provenance, config=None):
        super().__init__(mylist)
        self._config = config or get_config()
        self.custom_setitem = False
        self.put_provenance(provenance)
        self.custom_setitem = True

    def put_provenance(self, provenance):
        """
        Recursively transforms every value in ``ListWithProvenance`` into its
        corresponding WithProvenance object and appends its corresponding
        ``provenance``. Each value has its corresponding provenance defined in the
        ``provenance`` list, and this method just groups them together 1-to-1.

        Parameters
        ----------
        provenance : list
            The provenance that will be recursively assigned to all elements of the
            list. The provenance needs to be a ``list`` with the same number of elements
            as ``self`` (same structure) so that it can successfully transfer each
            provenance value to its corresponding value on ``self`` (1-to-1
            conrrespondance).
        """

        if not provenance:
            provenance = [{}] * len(self)

        for c, elem in enumerate(self):
            if isinstance(elem, dict):
                self[c] = DictWithProvenance(elem, provenance[c], config=self._config)
            elif isinstance(elem, list):
                self[c] = ListWithProvenance(elem, provenance[c], config=self._config)
            elif hasattr(elem, "provenance"):
                self[c].provenance.extend(provenance[c])
            else:
                self[c] = wrapper_with_provenance_factory(elem, provenance[c])

    def set_provenance(self, provenance, update_method="extend"):
        """
        Recursively transforms every value in ``ListWithProvenance`` into its
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

        for c, elem in enumerate(self):
            if isinstance(elem, dict):
                self[c] = DictWithProvenance(elem, {}, config=self._config)
                self[c].set_provenance(provenance, update_method=update_method)
            elif isinstance(elem, list):
                self[c] = ListWithProvenance(elem, [], config=self._config)
                self[c].set_provenance(provenance, update_method=update_method)
            elif hasattr(elem, "provenance"):
                if update_method == "extend":
                    self[c].provenance.extend(provenance)
                elif update_method == "update":
                    if self[c].provenance[-1]:
                        self[c].provenance[-1].update(provenance[-1])
                    else:
                        self[c].provenance[-1] = provenance[-1]
                elif update_method == "update_from_choose":
                    if self[c].provenance[-1]:
                        old_from_choose = self[c].provenance[-1].get("from_choose", [])
                        # Extend the from_choose list with the new entry
                        if old_from_choose:
                            provenance[-1]["from_choose"] = (
                                old_from_choose + provenance[-1].get("from_choose", [])
                            )
                        self[c].provenance[-1].update(provenance[-1])
                    else:
                        self[c].provenance[-1] = provenance[-1]
                else:
                    raise ValueError(
                        f"Unknown update method {update_method}. Use either 'extend' "
                        f"or 'update'"
                    )
            else:
                self[c] = wrapper_with_provenance_factory(elem, provenance)

    def get_provenance(self, index=-1):
        """
        Returns a list of provenance information with matching structure.

        Parameters
        ----------
        index : int
            Index into the provenance history. Default: ``-1`` (last/current).

        Returns
        -------
        provenance_list : list
            A list with a structure equivalent to that of the ``self`` list, but with
            the `values` of the provenance of each element
        """

        provenance_list = []
        for elem in self:
            if isinstance(elem, PROVENANCE_MAPPINGS):
                provenance_list.append(elem.get_provenance(index=index))
            elif hasattr(elem, "provenance"):
                provenance_list.append(elem.provenance[index])
            else:
                # The DictWithProvenance object might have dictionaries inside that
                # are not instances of that class (i.e. a dictionary added in the
                # backend). The provenance in this method is then defined as None
                provenance_list.append(None)

        return provenance_list

    def extract_first_nested_values_provenance(self):
        """
        Recursively loops through the list elements and returns the first provenance
        found in the nested values.

        Returns
        -------
        first_provenance : esm_parser.provenance.Provenance
            The first provenance found in the nested values
        """
        first_provenance = None
        for elem in self:
            if isinstance(elem, PROVENANCE_MAPPINGS):
                return elem.extract_first_nested_values_provenance()
            elif hasattr(elem, "provenance"):
                return elem.provenance[-1]

    def __setitem__(self, indx, val):
        """
        Extended ``__setitem__`` that preserves provenance history.
        """
        val_new = val
        config = self._config

        if (
            indx in self
            and not isinstance(self[indx], (dict, list))
            and hasattr(self[indx], "provenance")
            and hasattr(self, "custom_setitem")
            and self.custom_setitem
        ):
            new_provenance = self[indx].provenance
            if hasattr(val, "provenance"):
                new_provenance.extend_and_modified_by(
                    val.provenance, "dict.__setitem__"
                )
                if config.track_history:
                    val_new = copy.deepcopy(val)
                else:
                    val_new = val
                val_new.provenance = new_provenance

        super().__setitem__(indx, val_new)

    def super_setitem(self, indx, val):
        """
        Call the original ``list.__setitem__`` without provenance tracking.
        """
        super().__setitem__(indx, val)


from ._dict import DictWithProvenance  # noqa: E402 — deferred to break circular import

PROVENANCE_MAPPINGS = (DictWithProvenance, ListWithProvenance)
