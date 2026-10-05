import pytest

from conftest import EXAMPLES, EXAMPLES_DIR
from mcstas_ess_instr_citool import check_condayml
from mcstas_ess_instr_citool.check_condayml import validate_conda_requirements

HEADER = """\
channels:
  - conda-forge
  - nodefaults
dependencies:
"""


def write(tmp_path, deps, header=HEADER, filename="conda.yml"):
    f = tmp_path / filename
    f.write_text(header + deps)
    return f


def check(tmp_path, deps, **kwargs):
    return validate_conda_requirements(write(tmp_path, deps, **kwargs))


def check_fails(tmp_path, deps, match, **kwargs):
    with pytest.raises(RuntimeError, match=match):
        check(tmp_path, deps, **kwargs)


BASE = """\
  - mcstas >= 3.9.0
  - python
  - pip
"""


@pytest.mark.parametrize("example", EXAMPLES)
def test_examples_valid(example):
    res = validate_conda_requirements(EXAMPLES_DIR / example / "conda.yml")
    assert {"name": "mcstas", "source": "conda",
            "requirement": ">=3.9.0"} in res


def test_minimal_valid(tmp_path):
    res = check(tmp_path, BASE)
    assert [r["name"] for r in res] == ["mcstas", "python", "pip"]


def test_inline_channels(tmp_path):
    header = "channels: [nodefaults, conda-forge]\ndependencies:\n"
    check(tmp_path, BASE, header=header)


@pytest.mark.parametrize("channels,match", [
    (["conda-forge"], "missing required channel"),
    (["conda-forge", "nodefaults", "defaults"], "unexpected channel"),
    (["conda-forge", "nodefaults", "conda-forge"], "duplicate channel"),
])
def test_bad_channels(tmp_path, channels, match):
    header = ("channels:\n" + "".join(f"  - {c}\n" for c in channels)
              + "dependencies:\n")
    check_fails(tmp_path, BASE, match, header=header)


def test_bad_extension(tmp_path):
    check_fails(tmp_path, BASE, "unsupported file extension",
                filename="conda.txt")


def test_tabs_rejected(tmp_path):
    check_fails(tmp_path, BASE + "\t- numpy\n", "tab characters")


def test_unsupported_key(tmp_path):
    check_fails(tmp_path, BASE, "unsupported top-level key",
                header=HEADER.replace("channels:", "variables:\n  - x\nchannels:"))


def test_missing_mandatory(tmp_path):
    check_fails(tmp_path, "  - mcstas >= 3.9.0\n  - python\n",
                "missing mandatory conda dependency.*'pip'")


def test_forbidden(tmp_path):
    check_fails(tmp_path, BASE + "  - mamba\n", "forbidden conda dependency")


def test_duplicate(tmp_path):
    check_fails(tmp_path, BASE + "  - numpy\n  - NumPy >= 1.2\n",
                "duplicate conda dependency")


def test_explicit_channel(tmp_path):
    check(tmp_path, BASE + "  - conda-forge::numpy\n")
    check_fails(tmp_path, BASE + "  - defaults::numpy\n",
                "explicit channel 'defaults' is not allowed")


def test_lower_bounds_allowed(tmp_path):
    res = check(tmp_path, BASE + "  - numpy >= 1.26,>1.0\n")
    assert res[-1] == {"name": "numpy", "source": "conda",
                       "requirement": ">=1.26,>1.0"}


@pytest.mark.parametrize("spec", [
    "numpy == 1.26", "numpy <2", "numpy >=1.2,<2", "numpy=1.26",
    "numpy 1.26.*", "numpy 1.26",
])
def test_pinning_disallowed(tmp_path, spec):
    check_fails(tmp_path, BASE + f"  - {spec}\n",
                "disallowed version constraint")


@pytest.mark.parametrize("spec", [
    "numpy ^1.2", "numpy 1.26 py311_0", "numpy >=",
])
def test_unparsable_constraint(tmp_path, spec):
    check_fails(tmp_path, BASE + f"  - {spec}\n",
                "unsupported version constraint|missing version")


def test_bare_conda_version_allowed_when_pinning_allowed(tmp_path, monkeypatch):
    monkeypatch.setattr(check_condayml, "conda_pinning_allowed", {"numpy"})
    res = check(tmp_path, BASE + "  - numpy 1.26.*\n")
    assert res[-1]["requirement"] == "1.26.*"


@pytest.mark.parametrize("spec,ok", [
    ("mcstas >= 3.9.0", True),
    ("mcstas >= 3.9", True),
    ("mcstas>=4.0.1", True),
    ("mcstas > 3.9.0", True),
    ("mcstas >= 3.8.8", False),
    ("mcstas > 3.8.8", False),
    ("mcstas >= 3.7.22", False),
    ("mcstas", False),
])
def test_mcstas_lower_bound(tmp_path, spec, ok):
    deps = f"  - {spec}\n  - python\n  - pip\n"
    if ok:
        check(tmp_path, deps)
    else:
        check_fails(tmp_path, deps, "explicit lower bound of at least 3.9.0")


def test_mcstas_unparsable_bound(tmp_path):
    check_fails(tmp_path, "  - mcstas >= 3.9.0a\n  - python\n  - pip\n",
                "could not parse version")


def test_pip_not_allowlisted(tmp_path):
    check_fails(tmp_path, BASE + "  - pip:\n    - requests\n",
                "is not allowed by policy")


def test_pip_names_normalised(tmp_path, monkeypatch):
    monkeypatch.setattr(check_condayml, "pip_requirements_allowed",
                        {"Foo_Bar"})
    res = check(tmp_path, BASE + "  - pip:\n    - foo.bar >= 1.0\n")
    assert res[-1] == {"name": "foo-bar", "source": "pip",
                       "requirement": ">=1.0"}
    check_fails(tmp_path, BASE + "  - pip:\n    - foo-bar\n    - FOO_BAR\n",
                "duplicate pip dependency")


def test_pip_conda_conflict_normalised(tmp_path, monkeypatch):
    monkeypatch.setattr(check_condayml, "pip_requirements_allowed",
                        {"foo-bar"})
    check_fails(tmp_path,
                BASE + "  - foo_bar\n  - pip:\n    - Foo.Bar\n",
                "dependency-source conflict")


def test_pip_section_then_more_conda(tmp_path, monkeypatch):
    monkeypatch.setattr(check_condayml, "pip_requirements_allowed", {"foo"})
    res = check(tmp_path, "  - mcstas >= 3.9.0\n  - pip:\n    - foo\n"
                          "  - python\n  - pip\n")
    assert [(r["name"], r["source"]) for r in res] == [
        ("mcstas", "conda"), ("python", "conda"), ("pip", "conda"),
        ("foo", "pip")]


def test_unsupported_mapping(tmp_path):
    check_fails(tmp_path, BASE + "  - foo: bar\n",
                "unsupported dependency mapping")
    check_fails(tmp_path, BASE + "  - foo:\n", "unsupported dependency mapping")
