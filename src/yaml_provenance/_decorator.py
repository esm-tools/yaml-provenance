"""
Decorator for preserving provenance in recursive functions.
"""

import copy

from ._config import get_config
from ._wrapper import wrapper_with_provenance_factory


def keep_provenance_in_recursive_function(func):
    """
    Decorator for recursive functions to preserve provenance through
    value transformations.

    The decorated function should accept ``(tree, rhs, *args, **kwargs)`` where
    ``rhs`` is the value being processed. The decorator:

    1. Temporarily disables ``custom_setitem`` on ``rhs`` if applicable
    2. Runs the function
    3. Preserves/extends provenance from ``rhs`` to the output

    Parameters
    ----------
    func : callable
        The function to decorate.
    """
    does_not_modify_prov = ["find_variable", "recursive_run_function"]
    modify_prov = func.__name__ not in does_not_modify_prov

    def inner(tree, rhs, *args, **kwargs):
        config = get_config()
        custom_setitem_was_turned_off_in_this_instance = False
        if hasattr(rhs, "custom_setitem") and rhs.custom_setitem:
            rhs.custom_setitem = False
            custom_setitem_was_turned_off_in_this_instance = True

        output = func(tree, rhs, *args, **kwargs)

        if hasattr(rhs, "provenance"):
            if config.track_history:
                provenance = copy.deepcopy(rhs.provenance)
            else:
                from ._provenance import Provenance
                provenance = Provenance(
                    [rhs.provenance[-1]], track_history=False
                )

            # Value was modified
            if type(rhs) != type(output) or rhs != output:
                if config.track_history:
                    output = copy.deepcopy(output)

                if hasattr(output, "provenance"):
                    if modify_prov:
                        provenance.extend_and_modified_by(output.provenance, func)
                    output.provenance = provenance
                elif provenance is not None:
                    if modify_prov:
                        provenance.append_last_step_modified_by(func)
                    output = wrapper_with_provenance_factory(output, provenance)

        if custom_setitem_was_turned_off_in_this_instance:
            rhs.custom_setitem = True

        return output

    return inner
