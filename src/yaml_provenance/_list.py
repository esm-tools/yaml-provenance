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
        Recursively transforms every element into its WithProvenance object with
        corresponding provenance (1-to-1 mapping).

        Parameters
        ----------
        provenance : list
            Provenance list with same length as ``self``.
        """
        from ._dict import DictWithProvenance

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

    def set_provenance(self, provenance):
        """
        Recursively sets the same ``provenance`` on all nested elements.

        Parameters
        ----------
        provenance : any
            New provenance value to set.
        """
        from ._dict import DictWithProvenance

        if not isinstance(provenance, list):
            provenance = [provenance]

        for c, elem in enumerate(self):
            if isinstance(elem, dict):
                self[c] = DictWithProvenance(elem, {}, config=self._config)
                self[c].set_provenance(provenance)
            elif isinstance(elem, list):
                self[c] = ListWithProvenance(elem, [], config=self._config)
                self[c].set_provenance(provenance)
            elif hasattr(elem, "provenance"):
                self[c].provenance.extend(provenance)
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
        list
            Provenance list.
        """
        from ._dict import DictWithProvenance
        PROVENANCE_MAPPINGS = (DictWithProvenance, ListWithProvenance)

        provenance_list = []
        for elem in self:
            if isinstance(elem, PROVENANCE_MAPPINGS):
                provenance_list.append(elem.get_provenance(index=index))
            elif hasattr(elem, "provenance"):
                provenance_list.append(elem.provenance[index])
            else:
                provenance_list.append(None)

        return provenance_list

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
