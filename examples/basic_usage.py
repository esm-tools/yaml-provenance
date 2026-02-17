"""
Basic usage of yaml-provenance.

This example demonstrates loading a YAML file with provenance tracking,
inspecting provenance, merging configurations, and viewing history.
"""

import os
import tempfile

from yaml_provenance import (
    ProvenanceConfig,
    configure,
    DictWithProvenance,
    load_yaml,
)

# Enable full history tracking
configure(ProvenanceConfig(track_history=True))

# Create a sample YAML file
yaml_content = """\
database:
    host: localhost
    port: 5432
    name: myapp
"""

with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
    f.write(yaml_content)
    filepath = f.name

try:
    # Load with provenance
    config = load_yaml(filepath)

    # Inspect where a value came from
    print("=== Provenance of database.host ===")
    print(f"Value: {config['database']['host']}")
    print(f"Provenance: {config['database']['host'].provenance[-1]}")
    print()

    # Get provenance for the whole structure
    print("=== Full provenance tree ===")
    prov = config.get_provenance()
    for key, val in prov["database"].items():
        print(f"  {key}: line {val['line']}, col {val['col']}")
    print()

    # Set new provenance
    new_prov = {"line": 1, "col": 1, "yaml_file": "overrides.yaml", "category": "user"}
    override = DictWithProvenance({"host": "production-db.example.com"}, {})
    override.set_provenance(new_prov)

    # Update — provenance history is preserved
    config["database"].update(override)

    print("=== After update ===")
    print(f"Value: {config['database']['host']}")
    print(f"Provenance history ({len(config['database']['host'].provenance)} entries):")
    for i, p in enumerate(config["database"]["host"].provenance):
        print(f"  [{i}] {p}")

finally:
    os.unlink(filepath)
