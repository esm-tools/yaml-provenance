Configuration
=============

yaml-provenance is configured via ``ProvenanceConfig``:

.. code-block:: python

   from yaml_provenance import ProvenanceConfig, configure

   configure(ProvenanceConfig(
       category_hierarchy=[None, "defaults", "components", "user"],
       on_conflict="raise",
       track_history=True,
   ))

Options
-------

``category_hierarchy``
   Ordered list of category names from lowest to highest priority.
   Default: ``[None]`` (single level, no hierarchy enforcement).

``on_conflict``
   What to do when two values at the same hierarchy level conflict:
   ``"raise"`` (default), ``"warn"``, or ``"ignore"``.

``track_history``
   Whether to keep the full provenance history. Default: ``False``.
   When off, provenance lists have at most 1 element.

``custom_type_handlers``
   Dict mapping types to handler functions for types that cannot be
   dynamically subclassed.

``conflict_resolver``
   Custom callback for conflict resolution. Receives
   ``(key, old_val, new_val, old_prov, new_prov)`` and returns
   ``"raise"``, ``"keep_old"``, ``"keep_new"``, or ``"ignore"``.
