# yaml-provenance — Agent Context

This file provides a concise overview of the codebase for coding agents so they
don't need to read every file.

## What This Package Does

`yaml-provenance` tracks **where every value in a YAML configuration came from**
(file, line, column) and optionally its full history of changes. It wraps
standard Python types (str, int, float, bool, None, dict, list) with a
`.provenance` attribute that records origin metadata.

## Package Structure

```
src/yaml_provenance/
├── __init__.py         # Public API — all exports listed in __all__
├── _config.py          # ProvenanceConfig class + module-level configure()/get_config()
├── _exceptions.py      # ProvenanceError, CategoryConflictError
├── _provenance.py      # Provenance(list) — the history container
├── _wrapper.py         # Factory that creates TypeWithProvenance subclasses dynamically
├── _dict.py            # DictWithProvenance(dict) — recursive provenance on dicts
├── _list.py            # ListWithProvenance(list) — recursive provenance on lists
├── _decorator.py       # @keep_provenance_in_recursive_function decorator
├── _helpers.py         # clean_provenance(), wrap_computed(), transfer_provenance(), annotate_dict()
├── _serialization.py   # register_pickle_reducers(), register_yaml_representers(), ProvenanceJSONEncoder
├── yaml_loader.py      # ProvenanceConstructor, ProvenanceLoader, load_yaml()
└── _yaml_dumper.py     # dump_yaml(), _format_provenance_comment(), _add_eol_comments()
```

## Key Concepts

### Provenance

A `Provenance` is a `list` subclass where each element is a dict like:
```python
{"line": 3, "col": 9, "yaml_file": "config.yaml", "category": None, "subcategory": None}
```
The last element is the current provenance. Earlier elements are history
(only when `track_history=True`).

### WithProvenance Wrappers

Every leaf value gets wrapped so it has a `.provenance` attribute:
- `str` → `StrWithProvenance(str)` (created dynamically by the factory)
- `int` → `IntWithProvenance(int)` (created dynamically)
- `bool` → `BoolWithProvenance` (special class, bool can't be subclassed)
- `None` → `NoneWithProvenance` (special class)
- `dict` → `DictWithProvenance`
- `list` → `ListWithProvenance`

The factory is `wrapper_with_provenance_factory(value, provenance)` in `_wrapper.py`.
Dynamic classes are cached in `_wrapper_registry`.

### Lightweight vs Full History Mode

Controlled by `ProvenanceConfig.track_history` (default: `False`):
- **Lightweight** (`False`): `Provenance` list has at most 1 element. No
  `copy.deepcopy` calls. Very fast.
- **Full history** (`True`): Every change appends to the `Provenance` list.
  Uses `deepcopy` to preserve snapshots.

### Category Hierarchy

`ProvenanceConfig.category_hierarchy` is a list of category names ordered
low-to-high. `DictWithProvenance.__setitem__` uses this to decide whether
a new value should overwrite an existing one:
- Higher category always wins
- Same category with different values → `CategoryConflictError` (or warn/ignore)
- Default hierarchy is `[None]` (single level, no enforcement)

### Custom Conflict Resolution

`ProvenanceConfig.conflict_resolver` is an optional callback
`(key, old_val, new_val, old_prov, new_prov) -> action` where action is
`"raise"`, `"keep_old"`, `"keep_new"`, or `"ignore"`.

### YAML Loading

`yaml_loader.py` provides:
- `ProvenanceConstructor(RoundTripConstructor)` — captures `(data, (line, col))`
  tuples from ruamel.yaml nodes
- `ProvenanceLoader` — splits raw tuples into data + provenance dicts, produces
  `DictWithProvenance`
- `load_yaml(filepath)` — convenience function

A `category_resolver` callback maps file paths to `(category, subcategory)`.

## Dependencies

- `ruamel.yaml>=0.17` — YAML parsing with line/column info
- `loguru` — logging (used in `_dict.py` and `_config.py`)

## Testing

Tests live in `tests/`. Run with `pytest`. Key test files:
- `test_provenance.py` — Provenance class
- `test_dict.py` — DictWithProvenance (largest test file)
- `test_list.py` — ListWithProvenance
- `test_wrapper.py` — Factory and Bool/NoneWithProvenance
- `test_decorator.py` — @keep_provenance_in_recursive_function
- `test_config.py` — ProvenanceConfig and hierarchy
- `test_lightweight.py` — Lightweight mode behavior
- `test_yaml_loader.py` — YAML loading with provenance
- `test_yaml_dumper.py` — dump_yaml() with provenance comments
- `test_new_helpers.py` — wrap_computed(), transfer_provenance(), annotate_dict()
- `test_serialization.py` — pickle, JSON, and YAML serialization of WithProvenance types

Test fixtures are in `tests/fixtures/`.

## Origin

Extracted from the `esm_parser.provenance` module in
[ESM-Tools](https://github.com/esm-tools/esm_tools). Generalized to remove
ESM-Tools-specific dependencies (esm_calendar, esm_tools.user_error) and make
the category hierarchy configurable.

## Common Patterns for Contributors

### Adding provenance to a value
```python
from yaml_provenance import wrapper_with_provenance_factory
wrapped = wrapper_with_provenance_factory("hello", {"line": 1, "col": 1, "yaml_file": "test.yaml"})
print(wrapped.provenance[-1])  # {'line': 1, 'col': 1, 'yaml_file': 'test.yaml'}
```

### Creating a tracked dictionary
```python
from yaml_provenance import DictWithProvenance
data = {"key": "value"}
prov = {"key": {"line": 1, "col": 5, "yaml_file": "f.yaml"}}
d = DictWithProvenance(data, prov)
```

### Bypassing provenance tracking
Use `super_setitem(key, val)` on DictWithProvenance/ListWithProvenance to
set values without any provenance logic.

### Dumping to YAML with provenance comments
```python
from yaml_provenance import load_yaml, dump_yaml
from io import StringIO

cfg = load_yaml("config.yaml")
dump_yaml(cfg)                        # to stdout
dump_yaml(cfg, filepath="out.yaml")   # to file
buf = StringIO()
dump_yaml(cfg, stream=buf)            # to in-memory buffer
print(buf.getvalue())
```

Output example:
```yaml
echam:
  type: atmosphere  # config.yaml,line:2,col:11
  files:
    greenhouse:
      kind: input  # config.yaml,line:5,col:19
      a_list:
      - 1  # config.yaml,line:8,col:19
      - 2  # config.yaml,line:9,col:19
```

`_yaml_dumper.py` internals:
- `_format_provenance_comment(prov)` → `"file,line:N,col:N[,category:cat/sub]"`
- `_add_eol_comments(commented_map, prov_config)` — recursive walker
- `dump_yaml` cleans provenance, round-trips through ruamel.yaml to get a
  `CommentedMap`, then annotates each scalar with its provenance before writing.
