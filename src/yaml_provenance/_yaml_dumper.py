"""
YAML dumper with provenance comments.

Provides ``dump_yaml`` which serialises a provenance-tracked configuration
to YAML with inline end-of-line comments recording the origin of each value.

The output format mirrors the approach in ``esm_parser.dict_to_yaml`` from
ESM-Tools, generalised to work without any ESM-Tools-specific dependencies.

Typical usage::

    from yaml_provenance import load_yaml, dump_yaml

    cfg = load_yaml("config.yaml")
    dump_yaml(cfg)                        # print to stdout
    dump_yaml(cfg, filepath="out.yaml")   # write to file

    from io import StringIO
    buf = StringIO()
    dump_yaml(cfg, stream=buf)
    print(buf.getvalue())
"""

import sys
from io import StringIO

from ruamel.yaml import YAML

from ._dict import DictWithProvenance
from ._helpers import clean_provenance
from ._list import ListWithProvenance


def _format_provenance_comment(provenance):
    """
    Format a provenance dict as a short comment string.

    Parameters
    ----------
    provenance : dict or None
        Provenance dict with keys ``yaml_file``, ``line``, ``col``, and
        optionally ``category`` and ``subcategory``.

    Returns
    -------
    str
        A human-readable comment string, or ``"no provenance"`` if
        ``provenance`` is ``None`` or empty.
    """
    if not provenance:
        return "no provenance"

    # Check for required keys - handle incomplete provenance gracefully
    required_keys = ['yaml_file', 'line', 'col']
    if not all(key in provenance for key in required_keys):
        return "no provenance"

    comment = (
        f"{provenance['yaml_file']},"
        f"line:{provenance['line']},"
        f"col:{provenance['col']}"
    )

    category = provenance.get("category")
    if category is not None:
        subcategory = provenance.get("subcategory")
        if subcategory is not None:
            comment += f",category:{category}/{subcategory}"
        else:
            comment += f",category:{category}"

    return comment


def _add_eol_comments(commented_config, config):
    """
    Recursively add end-of-line provenance comments to a ruamel.yaml
    ``CommentedMap`` / ``CommentedSeq``.

    Parameters
    ----------
    commented_config : CommentedMap or CommentedSeq
        The ruamel.yaml structure to annotate (modified in-place).
    config : DictWithProvenance or ListWithProvenance
        The provenance-tracked config to read provenance from.
    """
    # Import at function level to avoid scoping issues
    from ._dict import DictWithProvenance
    import sys
    
    if isinstance(commented_config, dict):
        # Debug output using print to ensure visibility
        print(f"\n[TRACE-DUMPER] _add_eol_comments: Processing dict with {len(commented_config)} keys", file=sys.stderr, flush=True)
        print(f"[TRACE-DUMPER]   config type: {type(config).__name__}", file=sys.stderr, flush=True)
        print(f"[TRACE-DUMPER]   Is DictWithProvenance: {isinstance(config, DictWithProvenance)}", file=sys.stderr, flush=True)
        if hasattr(config, '_provenance_map'):
            print(f"[TRACE-DUMPER]   Has _provenance_map: True, size: {len(config._provenance_map)}", file=sys.stderr, flush=True)
            if config._provenance_map:
                sample_keys = list(config._provenance_map.keys())[:3]
                print(f"[TRACE-DUMPER]   Sample _provenance_map keys: {sample_keys}", file=sys.stderr, flush=True)
        else:
            print(f"[TRACE-DUMPER]   Has _provenance_map: False", file=sys.stderr, flush=True)
        
        for key, cvalue in commented_config.items():
            if not isinstance(config, dict):
                continue
            pvalue = config.get(key)
            if pvalue is None and key not in config:
                commented_config.yaml_add_eol_comment("no provenance", key)
                continue
            if isinstance(cvalue, (dict, list)):
                if isinstance(pvalue, (dict, list)):
                    _add_eol_comments(cvalue, pvalue)
            else:
                # Try to get provenance from shadow map first (for DictWithProvenance)
                print(f"[TRACE-DUMPER] Checking provenance for key: '{key}'", file=sys.stderr, flush=True)
                provenance = None
                if isinstance(config, DictWithProvenance) and hasattr(config, '_provenance_map'):
                    prov_entry = config._provenance_map.get(key)
                    print(f"[TRACE-DUMPER]   Key '{key}' in _provenance_map: {key in config._provenance_map}", file=sys.stderr, flush=True)
                    if prov_entry is not None:
                        print(f"[TRACE-DUMPER]   prov_entry type: {type(prov_entry).__name__}", file=sys.stderr, flush=True)
                        # prov_entry could be a Provenance list or a nested structure
                        if isinstance(prov_entry, list) and prov_entry:
                            provenance = prov_entry[-1]
                            print(f"[TRACE-DUMPER]   Extracted from list: {provenance}", file=sys.stderr, flush=True)
                        elif isinstance(prov_entry, dict):
                            # It's a single provenance dict (from get_provenance extraction)
                            provenance = prov_entry
                            print(f"[TRACE-DUMPER]   Using dict directly: {provenance}", file=sys.stderr, flush=True)
                        elif hasattr(prov_entry, 'provenance'):
                            # It's a wrapped value
                            if prov_entry.provenance:
                                provenance = prov_entry.provenance[-1]
                                print(f"[TRACE-DUMPER]   Extracted from wrapped value: {provenance}", file=sys.stderr, flush=True)
                    else:
                        print(f"[TRACE-DUMPER]   prov_entry is None for key '{key}'", file=sys.stderr, flush=True)
                
                # Fall back to extracting from value's .provenance attribute
                if provenance is None:
                    provenance_list = getattr(pvalue, "provenance", [])
                    if provenance_list:
                        provenance = provenance_list[-1]
                        print(f"[TRACE-DUMPER]   Fallback: extracted from pvalue.provenance: {provenance}", file=sys.stderr, flush=True)
                    else:
                        print(f"[TRACE-DUMPER]   Fallback: pvalue has no provenance or empty list", file=sys.stderr, flush=True)
                
                print(f"[TRACE-DUMPER]   Final provenance value: {provenance}", file=sys.stderr, flush=True)
                comment = _format_provenance_comment(provenance)
                print(f"[TRACE-DUMPER]   Comment: {comment}", file=sys.stderr, flush=True)
                commented_config.yaml_add_eol_comment(comment, key)

    elif isinstance(commented_config, list):
        for indx, cvalue in enumerate(commented_config):
            if not isinstance(config, list) or indx >= len(config):
                continue
            pvalue = config[indx]
            if isinstance(cvalue, (dict, list)):
                if isinstance(pvalue, (dict, list)):
                    _add_eol_comments(cvalue, pvalue)
            else:
                provenance_list = getattr(pvalue, "provenance", [])
                if provenance_list:
                    provenance = provenance_list[-1]
                else:
                    provenance = None
                comment = _format_provenance_comment(provenance)
                commented_config.yaml_add_eol_comment(comment, indx)


def dump_yaml(config, filepath=None, stream=None):
    """
    Dump a provenance-tracked config to YAML with end-of-line provenance
    comments.

    Each scalar value is annotated with an end-of-line comment showing the
    source file, line, and column where the value originated. Values added
    programmatically (without provenance) receive a ``# no provenance``
    comment.

    Output priority: ``stream`` > ``filepath`` > stdout.

    Parameters
    ----------
    config : DictWithProvenance or ListWithProvenance
        The provenance-tracked configuration to dump.
    filepath : str or Path or None
        Destination file path. Used when ``stream`` is not given.
        If both are ``None``, output goes to stdout.
    stream : file-like or None
        An output stream (e.g. ``StringIO``). Takes priority over
        ``filepath``. Useful for testing or in-memory processing.

    Examples
    --------
    >>> from yaml_provenance import load_yaml, dump_yaml
    >>> cfg = load_yaml("config.yaml")
    >>> dump_yaml(cfg)                        # to stdout
    >>> dump_yaml(cfg, filepath="out.yaml")   # to file
    >>> from io import StringIO
    >>> buf = StringIO()
    >>> dump_yaml(cfg, stream=buf)
    >>> print(buf.getvalue())
    """
    my_yaml = YAML()
    my_yaml.width = 10000

    # Register representers so DictWithProvenance / ListWithProvenance are
    # serialised as plain YAML mappings/sequences rather than custom tags.
    def _dict_representer(dumper, obj):
        return dumper.represent_mapping("tag:yaml.org,2002:map", obj)

    def _list_representer(dumper, obj):
        return dumper.represent_sequence("tag:yaml.org,2002:seq", obj)

    my_yaml.representer.add_representer(DictWithProvenance, _dict_representer)
    my_yaml.representer.add_representer(ListWithProvenance, _list_representer)

    # Strip provenance wrappers to get plain Python values.
    config_clean = clean_provenance(config)

    # Dump to an intermediate string so we can reload into a CommentedMap
    # (ruamel.yaml's round-trip type), which supports adding EOL comments.
    intermediate = StringIO()
    my_yaml.dump(config_clean, intermediate)

    intermediate.seek(0)
    config_with_comments = my_yaml.load(intermediate)

    # Walk both structures simultaneously and attach provenance comments.
    _add_eol_comments(config_with_comments, config)

    if stream is not None:
        my_yaml.dump(config_with_comments, stream)
    elif filepath is not None:
        with open(filepath, "w") as f:
            my_yaml.dump(config_with_comments, f)
    else:
        my_yaml.dump(config_with_comments, sys.stdout)
