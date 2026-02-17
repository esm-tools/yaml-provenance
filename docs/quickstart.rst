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
