# yaml-provenance

Track where every value in your YAML configuration came from — file, line, column — and its full history of changes.

## Installation

```bash
pip install yaml-provenance
```

## Quick Start

```python
from yaml_provenance import load_yaml, DictWithProvenance, ProvenanceConfig

# Load a YAML file with provenance tracking
config = load_yaml("config.yaml")

# Inspect where a value came from
print(config["database"]["host"].provenance[-1])
# {'line': 3, 'col': 9, 'yaml_file': 'config.yaml'}

# Merge configurations — provenance history is preserved
defaults = load_yaml("defaults.yaml")
config.update(defaults)

# See the full history
print(config["database"]["host"].provenance)
```

## Lightweight Mode

By default, history tracking is off for performance. Only the current provenance is stored:

```python
from yaml_provenance import configure, ProvenanceConfig

# Enable full history tracking
configure(ProvenanceConfig(track_history=True))
```

## Features

- Track file, line, and column for every YAML value
- Optional full history of changes (who modified what and when)
- Configurable category hierarchy for conflict resolution
- Works with any YAML-based configuration system
- Lightweight mode (default) for minimal overhead
- Serialization support — pickle, JSON (`ProvenanceJSONEncoder`), and ruamel.yaml roundtrip
- `copy.deepcopy` preserves provenance on all wrapper types
- Helper functions for computed / programmatic values (`wrap_computed`, `transfer_provenance`, `annotate_dict`)

## License

MIT
