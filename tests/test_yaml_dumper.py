"""
Tests for the YAML dumper with provenance comments.
"""

import os
from io import StringIO

import pytest
from ruamel.yaml import YAML

from yaml_provenance import DictWithProvenance, load_yaml, dump_yaml
from yaml_provenance._yaml_dumper import _format_provenance_comment, _add_eol_comments


# ---------------------------------------------------------------------------
# _format_provenance_comment
# ---------------------------------------------------------------------------


def test_format_provenance_comment_basic():
    """Format a minimal provenance dict without category info."""
    prov = {"yaml_file": "config.yaml", "line": 3, "col": 9}
    assert _format_provenance_comment(prov) == "config.yaml,line:3,col:9"


def test_format_provenance_comment_with_category_and_subcategory():
    """Category and subcategory are both appended when present."""
    prov = {
        "yaml_file": "config.yaml",
        "line": 3,
        "col": 9,
        "category": "components",
        "subcategory": "echam",
    }
    assert _format_provenance_comment(prov) == (
        "config.yaml,line:3,col:9,category:components/echam"
    )


def test_format_provenance_comment_category_without_subcategory():
    """None subcategory is omitted; 'None' never appears in the string."""
    prov = {
        "yaml_file": "config.yaml",
        "line": 3,
        "col": 9,
        "category": "runscript",
        "subcategory": None,
    }
    comment = _format_provenance_comment(prov)
    assert comment == "config.yaml,line:3,col:9,category:runscript"
    assert "None" not in comment


def test_format_provenance_comment_computed_omits_line_col():
    """Computed values (line=0, col=0) omit the meaningless line/col suffix."""
    prov = {"yaml_file": "computed:BasicConfig.LOCAL_ROOT_DIR/t0ht", "line": 0, "col": 0}
    assert _format_provenance_comment(prov) == "computed:BasicConfig.LOCAL_ROOT_DIR/t0ht"


def test_format_provenance_comment_none_returns_no_provenance():
    assert _format_provenance_comment(None) == "no provenance"


def test_format_provenance_comment_empty_dict_returns_no_provenance():
    assert _format_provenance_comment({}) == "no provenance"


# ---------------------------------------------------------------------------
# dump_yaml — output routing
# ---------------------------------------------------------------------------


def test_dump_yaml_to_stream(example_path2):
    """dump_yaml writes YAML to the given stream."""
    config = load_yaml(example_path2)
    buf = StringIO()
    dump_yaml(config, stream=buf)
    assert "atmosphere" in buf.getvalue()


def test_dump_yaml_to_file(tmp_path, example_path2):
    """dump_yaml writes to a file when filepath is given."""
    config = load_yaml(example_path2)
    out_file = str(tmp_path / "out.yaml")
    dump_yaml(config, filepath=out_file)
    with open(out_file) as f:
        content = f.read()
    assert "atmosphere" in content


def test_dump_yaml_to_stdout(capsys, example_path2):
    """dump_yaml writes to stdout when no filepath or stream is provided."""
    config = load_yaml(example_path2)
    dump_yaml(config)
    captured = capsys.readouterr()
    assert "atmosphere" in captured.out


def test_dump_yaml_stream_takes_priority_over_filepath(tmp_path, example_path2):
    """When both stream and filepath are given, stream is used."""
    config = load_yaml(example_path2)
    out_file = str(tmp_path / "unused.yaml")
    buf = StringIO()
    dump_yaml(config, filepath=out_file, stream=buf)
    assert "atmosphere" in buf.getvalue()
    assert not os.path.exists(out_file)


# ---------------------------------------------------------------------------
# dump_yaml — provenance comments content
# ---------------------------------------------------------------------------


def test_dump_yaml_comment_contains_source_filename(example_path2):
    """The source filename appears in end-of-line comments."""
    config = load_yaml(example_path2)
    buf = StringIO()
    dump_yaml(config, stream=buf)
    assert os.path.basename(example_path2) in buf.getvalue()


def test_dump_yaml_comment_line_and_col_for_scalar(example_path2):
    """echam.type is at line 2, col 11 — both appear in the output."""
    config = load_yaml(example_path2)
    buf = StringIO()
    dump_yaml(config, stream=buf)
    output = buf.getvalue()
    assert "line:2" in output
    assert "col:11" in output


def test_dump_yaml_comment_nested_scalar(example_path2):
    """echam.files.greenhouse.kind is at line 5, col 19."""
    config = load_yaml(example_path2)
    buf = StringIO()
    dump_yaml(config, stream=buf)
    output = buf.getvalue()
    assert "line:5" in output
    assert "col:19" in output


def test_dump_yaml_list_items_have_provenance_comments(example_path2):
    """Each list item carries its own provenance comment (lines 8, 9, 10)."""
    config = load_yaml(example_path2)
    buf = StringIO()
    dump_yaml(config, stream=buf)
    output = buf.getvalue()
    assert "line:8" in output
    assert "line:9" in output
    assert "line:10" in output


def test_dump_yaml_no_provenance_comment():
    """Values with no provenance get a 'no provenance' comment."""
    config = DictWithProvenance({"key": "value", "number": 42}, {})
    buf = StringIO()
    dump_yaml(config, stream=buf)
    assert "no provenance" in buf.getvalue()


def test_dump_yaml_empty_dict_value_gets_key_provenance(example_path2):
    """An empty dict value gets a provenance comment from its key's provenance."""
    from yaml_provenance._wrapper import wrapper_with_provenance_factory

    prov = {"yaml_file": "jobs.yml", "line": 5, "col": 7, "category": None, "subcategory": None}
    key = wrapper_with_provenance_factory("DEPS", prov)
    config = DictWithProvenance({key: {}}, {})
    buf = StringIO()
    dump_yaml(config, stream=buf)
    output = buf.getvalue()
    assert "jobs.yml,line:5,col:7" in output


def test_dump_yaml_category_in_comment(example_path2):
    """Category and subcategory appear in comments when a resolver is used."""
    config = load_yaml(example_path2, category_resolver=lambda fp: ("components", "echam"))
    buf = StringIO()
    dump_yaml(config, stream=buf)
    assert "category:components/echam" in buf.getvalue()


# ---------------------------------------------------------------------------
# dump_yaml — round-trip correctness
# ---------------------------------------------------------------------------


def test_dump_yaml_output_is_valid_yaml(example_path2):
    """The dumped output can be reloaded as valid YAML."""
    config = load_yaml(example_path2)
    buf = StringIO()
    dump_yaml(config, stream=buf)
    buf.seek(0)
    reloaded = YAML().load(buf)
    assert reloaded["echam"]["type"] == "atmosphere"
    assert reloaded["echam"]["files"]["greenhouse"]["kind"] == "input"


def test_dump_yaml_values_preserved(example_path2):
    """All original values survive a dump → reload round-trip."""
    config = load_yaml(example_path2)
    buf = StringIO()
    dump_yaml(config, stream=buf)
    buf.seek(0)
    reloaded = YAML().load(buf)
    assert reloaded["echam"]["files"]["greenhouse"]["a_list"] == [1, 2, 3]
    assert reloaded["echam"]["files"]["greenhouse"]["path_in_computer"] == (
        "/my/path/in/computer"
    )


def test_dump_yaml_mixed_provenance(example_path2):
    """Config with both tracked and untracked values dumps without errors."""
    config = load_yaml(example_path2)
    config["new_key"] = "new_value"  # plain string, no provenance
    buf = StringIO()
    dump_yaml(config, stream=buf)
    output = buf.getvalue()
    assert "atmosphere" in output
    assert "new_value" in output


def test_dump_yaml_complex_example(example_path1):
    """Complex nested structure (example.yaml) dumps and reloads correctly."""
    config = load_yaml(example_path1)
    buf = StringIO()
    dump_yaml(config, stream=buf)
    buf.seek(0)
    reloaded = YAML().load(buf)
    assert reloaded["person"]["name"] == "Some Name With Surname"
    assert reloaded["person"]["my_int2"] == 42
    assert reloaded["person"]["my_bolean"] is True


# ---------------------------------------------------------------------------
# dump_yaml — empty dict values (e.g. DEPENDENCIES entries)
# ---------------------------------------------------------------------------


def test_dump_yaml_empty_dict_from_yaml_gets_key_provenance():
    """Empty dict values loaded from YAML carry provenance from the key."""
    deps_path = os.path.join(os.path.dirname(__file__), "fixtures", "dependencies.yaml")
    config = load_yaml(deps_path)
    buf = StringIO()
    dump_yaml(config, stream=buf)
    output = buf.getvalue()
    # SETUP: {} and INI: {} should get provenance from their key positions
    assert "dependencies.yaml" in output
    # Non-empty nested dict SIM-1 should have scalar provenance for STATUS
    assert "COMPLETED" in output
    # Empty dicts should NOT say "no provenance"
    lines = output.strip().split("\n")
    for line in lines:
        # Lines with "{}" value (empty dict) should have real provenance
        if ": {}" in line:
            assert "no provenance" not in line, f"Empty dict line has no provenance: {line}"
