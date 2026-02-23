"""
The Provenance class — a list subclass that tracks the history of a value's provenance.
"""

import copy


class Provenance(list):
    """
    A subclass of list where each element represents the provenance of a value
    at a point in its history. Supports both full history tracking and lightweight
    mode (at most 1 element).

    Parameters
    ----------
    provenance_data : list or dict
        List of provenance elements, or a single provenance element.
    track_history : bool
        If ``False``, the list keeps at most 1 element (current provenance only).
        Default: ``True`` (full history).
    """

    def __init__(self, provenance_data, track_history=True):
        if isinstance(provenance_data, list):
            super().__init__(provenance_data)
        else:
            super().__init__([provenance_data])

        self._track_history = track_history

        # In lightweight mode, keep only the last element
        if not track_history and len(self) > 1:
            last = self[-1]
            self.clear()
            self.append(last)

    def append_last_step_modified_by(self, func):
        """
        Copies the last element in the provenance history and adds the entry
        ``modified_by`` with value ``func`` to the copy.

        In lightweight mode, updates the single element in-place instead of
        appending a copy.

        Parameters
        ----------
        func : str
            Function that is modifying the variable.
        """
        if self._track_history:
            new_provenance_step = copy.deepcopy(self[-1])
            new_provenance_step = self.add_modified_by(new_provenance_step, func)
            self.append(new_provenance_step)
        else:
            # Lightweight: update in-place
            self.add_modified_by(self[-1], func)

    def extend_and_modified_by(self, additional_provenance, func):
        """
        Extends the current provenance history with ``additional_provenance``.

        In lightweight mode, replaces the single element instead of extending.

        Parameters
        ----------
        additional_provenance : Provenance
            Additional provenance history.
        func : str
            Function triggering this method.
        """
        if self._track_history:
            new_additional_provenance = additional_provenance
            if new_additional_provenance is not self:
                for elem in new_additional_provenance:
                    new_additional_provenance.add_modified_by(
                        elem, func, modified_by="extended_by"
                    )
                self.extend(new_additional_provenance)
            else:
                self.append_last_step_modified_by(func)
        else:
            # Lightweight: replace with the last element of additional_provenance
            if additional_provenance is not self and additional_provenance:
                last = additional_provenance[-1]
                if isinstance(last, dict):
                    last = dict(last)  # shallow copy
                self.add_modified_by(last, func, modified_by="extended_by")
                self.clear()
                self.append(last)
            else:
                self.add_modified_by(self[-1], func)

    def add_modified_by(self, provenance_step, func, modified_by="modified_by"):
        """
        Adds a ``modified_by`` entry to the given provenance step.

        Parameters
        ----------
        provenance_step : dict
            Provenance entry of the current step.
        func : str
            Function triggering this method.
        modified_by : str
            Name of the key for labelling the type of modification.

        Returns
        -------
        provenance_step : dict
            The provenance step with the ``modified_by`` item added.
        """
        if provenance_step is not None and isinstance(provenance_step, dict):
            provenance_step[modified_by] = str(func)

        return provenance_step
