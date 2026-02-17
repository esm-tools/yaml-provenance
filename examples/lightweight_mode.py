"""
Lightweight mode example — provenance tracking with minimal overhead.

In lightweight mode (the default), provenance lists have at most 1 element.
No copy.deepcopy is used, making it much faster for large configurations.
"""

import os
import tempfile

from yaml_provenance import (
    ProvenanceConfig,
    configure,
    DictWithProvenance,
    load_yaml,
)

# Lightweight mode is the default (track_history=False)
configure(ProvenanceConfig(track_history=False))

yaml_content = """\
database:
    host: localhost
    port: 5432
"""

with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
    f.write(yaml_content)
    filepath = f.name

try:
    config = load_yaml(filepath)

    print("=== Lightweight mode ===")
    print(f"Value: {config['database']['host']}")
    print(f"Provenance: {config['database']['host'].provenance[-1]}")
    print(f"History length: {len(config['database']['host'].provenance)}")
    print()

    # Update still works — but history is not accumulated
    new_prov = {"line": 1, "yaml_file": "override.yaml"}
    override = DictWithProvenance({"host": "prod-db"}, {})
    override.set_provenance(new_prov)
    config["database"].update(override)

    print("=== After update (still at most 1 provenance entry) ===")
    print(f"Value: {config['database']['host']}")
    print(f"History length: {len(config['database']['host'].provenance)}")
    print(f"Current provenance: {config['database']['host'].provenance[-1]}")

finally:
    os.unlink(filepath)
