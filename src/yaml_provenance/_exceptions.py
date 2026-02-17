"""
Exceptions for yaml-provenance.
"""


class ProvenanceError(Exception):
    """Base exception for provenance-related errors."""

    pass


class CategoryConflictError(ProvenanceError):
    """
    Raised when two values at the same category hierarchy level conflict.

    Attributes
    ----------
    key : str
        The conflicting key.
    old_val : any
        The existing value.
    new_val : any
        The new value that conflicts.
    category : str
        The category at which the conflict occurs.
    old_provenance : list
        Provenance of the existing value.
    new_provenance : list
        Provenance of the new value.
    """

    def __init__(self, message, key=None, old_val=None, new_val=None, category=None,
                 old_provenance=None, new_provenance=None):
        super().__init__(message)
        self.key = key
        self.old_val = old_val
        self.new_val = new_val
        self.category = category
        self.old_provenance = old_provenance
        self.new_provenance = new_provenance
