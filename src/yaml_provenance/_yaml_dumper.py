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

    line = provenance['line']
    col = provenance['col']
    if line == 0 and col == 0:
        comment = f"{provenance['yaml_file']}"
    else:
        comment = (
            f"{provenance['yaml_file']},"
            f"line:{line},"
            f"col:{col}"
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
    if isinstance(commented_config, dict):
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
                provenance = getattr(pvalue, "provenance", [None])[-1]
                comment = _format_provenance_comment(provenance)
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
                provenance = getattr(pvalue, "provenance", [None])[-1]
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
