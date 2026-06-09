API Reference
=============

Configuration
-------------

.. autoclass:: yaml_provenance.ProvenanceConfig
   :members:

.. autofunction:: yaml_provenance.configure

.. autofunction:: yaml_provenance.get_config

Core Classes
------------

.. autoclass:: yaml_provenance.Provenance
   :members:

.. autoclass:: yaml_provenance.DictWithProvenance
   :members:

.. autoclass:: yaml_provenance.ListWithProvenance
   :members:

Wrapper Factory
---------------

.. autofunction:: yaml_provenance.wrapper_with_provenance_factory

.. autoclass:: yaml_provenance.BoolWithProvenance
   :members:

.. autoclass:: yaml_provenance.NoneWithProvenance
   :members:

YAML Loader
-----------

.. autofunction:: yaml_provenance.load_yaml

.. autoclass:: yaml_provenance.ProvenanceLoader
   :members:

.. autoclass:: yaml_provenance.ProvenanceConstructor
   :members:

YAML Dumper
-----------

.. autofunction:: yaml_provenance.dump_yaml

Exceptions
----------

.. autoclass:: yaml_provenance.ProvenanceError

.. autoclass:: yaml_provenance.CategoryConflictError
   :members:

Helpers
-------

.. autofunction:: yaml_provenance.clean_provenance

.. autofunction:: yaml_provenance.wrap_computed

.. autofunction:: yaml_provenance.transfer_provenance

.. autofunction:: yaml_provenance.annotate_dict

.. autofunction:: yaml_provenance.keep_provenance_in_recursive_function

Serialization
-------------

.. autofunction:: yaml_provenance.register_yaml_representers

.. autoclass:: yaml_provenance.ProvenanceJSONEncoder
   :members:
