Quickstart
==========

Installation
------------

.. code-block:: bash

   pip install yaml-provenance

Basic Usage
-----------

Load a YAML file with provenance tracking:

.. code-block:: python

   from yaml_provenance import load_yaml, ProvenanceConfig, configure

   # Enable full history tracking (optional, off by default)
   configure(ProvenanceConfig(track_history=True))

   config = load_yaml("config.yaml")

   # Every value knows where it came from
   print(config["database"]["host"].provenance[-1])
   # {'line': 3, 'col': 9, 'yaml_file': 'config.yaml', 'category': None, 'subcategory': None}

Merging Configurations
-----------------------

When you update dictionaries, provenance history is preserved:

.. code-block:: python

   defaults = load_yaml("defaults.yaml")
   overrides = load_yaml("overrides.yaml")
   defaults.update(overrides)

   # See the full history of a value
   for step in config["key"].provenance:
       print(step)

Dumping to YAML with Provenance Comments
-----------------------------------------

:func:`~yaml_provenance.dump_yaml` serialises a provenance-tracked
configuration back to YAML. Each scalar value is annotated with an
end-of-line comment recording the file, line, and column it originated from.

.. code-block:: python

   from yaml_provenance import load_yaml, dump_yaml

   config = load_yaml("config.yaml")

   # Print to stdout
   dump_yaml(config)

   # Write to a file
   dump_yaml(config, filepath="config_with_provenance.yaml")

   # Capture as a string
   from io import StringIO
   buf = StringIO()
   dump_yaml(config, stream=buf)
   print(buf.getvalue())

Example output:

.. code-block:: yaml

   database:
     host: localhost  # config.yaml,line:3,col:9
     port: 5432       # config.yaml,line:4,col:9
   server:
     workers: 4       # overrides.yaml,line:2,col:12

Values that were added programmatically (without loading from a file) receive
a ``# no provenance`` comment. If a category resolver was used when loading
(see :doc:`configuration`), the category and subcategory are also included:

.. code-block:: yaml

   host: localhost  # config.yaml,line:3,col:9,category:components/mymodel
