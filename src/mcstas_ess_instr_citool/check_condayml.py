from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

from .util import minimum_mcstas_version

# Every valid environment must contain these as conda dependencies.
minimal_requirements = {
    "mcstas",
    "pip",
    "python",
}


# Conda packages for which exact versions, upper bounds, or other
# non-lower-bound constraints are allowed.
#
# Lower bounds such as "mcstas >= 3.8.8" are allowed for every package.
conda_pinning_allowed = set({
    "nosuchpkgyet",
})


# Packages that are forbidden in both conda and pip dependency lists.
forbidden_requirements = {
    "conda",
    "conda-build",
    "mamba",
    "pip-tools",
}


# Packages that may appear in the YAML pip subsection because there is no
# conda-forge package:
pip_requirements_allowed = {
    "nosuchpkgyet",
}

# Pip packages for which exact versions, upper bounds, or other
# non-lower-bound constraints are allowed.
#
# Lower bounds such as "requests >= 2.31" are allowed for every package
# in pip_requirements_allowed.
pip_pinning_allowed = {
    "nosuchpkgyet",
}


_PACKAGE_NAME_RE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9_.-]*$"
)

# Conda also supports a bare version after the package name, like
# "numpy 1.26.*" or "numpy 1.26". These are treated as pinning constraints
# (represented with an empty operator).
_CONDA_BARE_VERSION_RE = re.compile(r"^[0-9][0-9A-Za-z.*+!_]*$")

_OPERATORS = (
    "==",
    ">=",
    "<=",
    "!=",
    "~=",
    ">",
    "<",
    "=",
)


def _normalise_pip_name(name: str) -> str:
    # PEP 503 name normalisation:
    return re.sub(r"[-_.]+", "-", name).lower()


def _version_tuple(version: str) -> tuple[int, ...] | None:
    parts = version.split(".")
    if not all(part.isdigit() for part in parts):
        return None
    return tuple(int(part) for part in parts)


def _runtime_error(path: Path, message: str) -> RuntimeError:
    return RuntimeError(f"{path}: {message}")


def _remove_yaml_comment(line: str) -> str:
    """
    Remove comments outside quoted strings.

    This is sufficient for the small YAML subset supported by this module.
    """
    quote: str | None = None
    escaped = False

    for index, character in enumerate(line):
        if escaped:
            escaped = False
            continue

        if character == "\\" and quote == '"':
            escaped = True
            continue

        if character in {"'", '"'}:
            if quote is None:
                quote = character
            elif quote == character:
                quote = None
            continue

        if character == "#" and quote is None:
            return line[:index]

    return line


def _parse_scalar(
    value: str,
    path: Path,
    line_number: int,
) -> str:
    value = value.strip()

    if not value:
        raise _runtime_error(
            path,
            f"line {line_number}: expected a non-empty scalar value",
        )

    if value[0] in {"'", '"'}:
        try:
            parsed = ast.literal_eval(value)
        except (SyntaxError, ValueError) as exc:
            raise _runtime_error(
                path,
                f"line {line_number}: invalid quoted scalar {value!r}",
            ) from exc

        if not isinstance(parsed, str):
            raise _runtime_error(
                path,
                f"line {line_number}: expected a string scalar, "
                f"but received {type(parsed).__name__}",
            )

        return parsed

    return value


def _parse_string_list(
    value: str,
    path: Path,
    line_number: int,
) -> list[str]:
    """
    Parse a simple inline YAML list such as:

        [nodefaults, conda-forge]
    """
    value = value.strip()

    if not value.startswith("[") or not value.endswith("]"):
        raise _runtime_error(
            path,
            f"line {line_number}: expected an inline YAML list enclosed "
            "in '[' and ']'",
        )

    inner = value[1:-1].strip()

    if not inner:
        return []

    return [
        _parse_scalar(item, path, line_number)
        for item in inner.split(",")
    ]


def _parse_conda_yaml(path: Path) -> dict[str, Any]:
    """
    Parse the supported YAML subset.

    Supported top-level keys:

        name:
        channels:
          - ...
        dependencies:
          - package
          - pip:
              - package

    Unsupported YAML features include anchors, aliases, multiline strings,
    arbitrary mappings, flow mappings, and nested sections other than pip.
    """
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise _runtime_error(
            path,
            f"could not read file: {exc}",
        ) from exc

    document: dict[str, Any] = {}
    current_section: str | None = None

    dependencies: list[Any] = []
    pip_dependencies: list[str] | None = None

    for line_number, raw_line in enumerate(lines, start=1):
        if "\t" in raw_line:
            raise _runtime_error(
                path,
                f"line {line_number}: tab characters are not supported; "
                "use spaces for YAML indentation",
            )

        line = _remove_yaml_comment(raw_line).rstrip()

        if not line.strip():
            continue

        indentation = len(line) - len(line.lstrip(" "))
        content = line.strip()

        # Top-level key.
        if indentation == 0:
            if ":" not in content:
                raise _runtime_error(
                    path,
                    f"line {line_number}: expected a top-level YAML key "
                    f"followed by ':', got {content!r}",
                )

            key, value = content.split(":", 1)
            key = key.strip()
            value = value.strip()

            if key in document:
                raise _runtime_error(
                    path,
                    f"line {line_number}: duplicate top-level key {key!r}",
                )

            supported_keys = {
                "name",
                "channels",
                "dependencies",
            }

            if key not in supported_keys:
                raise _runtime_error(
                    path,
                    f"line {line_number}: unsupported top-level key "
                    f"{key!r}. Supported keys are: "
                    + ", ".join(sorted(supported_keys))
                    + ".",
                )

            if key == "name":
                document[key] = _parse_scalar(
                    value,
                    path,
                    line_number,
                )
                current_section = None

            elif key == "channels":
                if value:
                    document[key] = _parse_string_list(
                        value,
                        path,
                        line_number,
                    )
                    current_section = None
                else:
                    document[key] = []
                    current_section = "channels"

            elif key == "dependencies":
                if value:
                    raise _runtime_error(
                        path,
                        f"line {line_number}: dependencies must be a "
                        "block list. Put each package on its own line "
                        "beginning with '-'.",
                    )

                document[key] = dependencies
                current_section = "dependencies"

            continue

        # channels:
        if current_section == "channels":
            if indentation != 2 or not content.startswith("- "):
                raise _runtime_error(
                    path,
                    f"line {line_number}: invalid channels entry. "
                    "Expected two spaces followed by '- channel-name'.",
                )

            channel = _parse_scalar(
                content[2:],
                path,
                line_number,
            )

            document["channels"].append(channel)
            continue

        # dependencies:

        # A two-space list item after the pip subsection means that the
        # pip subsection has ended and the parent dependencies list has
        # resumed.
        if (
            current_section == "pip"
            and indentation == 2
            and content.startswith("- ")
        ):
            current_section = "dependencies"

        if current_section == "dependencies":
            if indentation != 2 or not content.startswith("- "):
                raise _runtime_error(
                    path,
                    f"line {line_number}: invalid dependency entry. "
                    "Expected two spaces followed by '- package-spec'.",
                )

            item = content[2:].strip()

            if item == "pip:":
                if pip_dependencies is not None:
                    raise _runtime_error(
                        path,
                        f"line {line_number}: duplicate 'pip:' "
                        "dependency subsection",
                    )

                pip_dependencies = []
                dependencies.append({"pip": pip_dependencies})
                current_section = "pip"

            elif re.search(r":(\s|$)", item):
                # A mapping, but not a "channel::package" spec.
                raise _runtime_error(
                    path,
                    f"line {line_number}: unsupported dependency mapping "
                    f"{item!r}. The only supported nested dependency "
                    "mapping is 'pip:'.",
                )

            else:
                dependencies.append(
                    _parse_scalar(
                        item,
                        path,
                        line_number,
                    )
                )

            continue

        # pip:
        if current_section == "pip":
            if indentation != 4 or not content.startswith("- "):
                raise _runtime_error(
                    path,
                    f"line {line_number}: invalid pip dependency entry. "
                    "Expected four spaces followed by '- package-spec'.",
                )

            pip_dependencies.append(
                _parse_scalar(
                    content[2:],
                    path,
                    line_number,
                )
            )
            continue

        raise _runtime_error(
            path,
            f"line {line_number}: unexpected indentation or content. "
            "The parser was not inside a channels, dependencies, or pip "
            "list.",
        )

    return document


def _split_package_spec(
    raw_spec: str,
    path: Path,
    kind: str,
) -> tuple[str, list[tuple[str, str]]]:
    """
    Parse a conda or pip package specification.

    Examples accepted:

        python
        python >= 3.11
        numpy >= 1.24,<2
        requests==2.31.0

    Conda explicit channel selectors are accepted only with conda-forge:

        conda-forge::numpy
    """
    specification = raw_spec.strip()

    if "::" in specification:
        channel, specification = specification.split("::", 1)

        if channel.strip().lower() != "conda-forge":
            raise _runtime_error(
                path,
                f"invalid {kind} dependency {raw_spec!r}: explicit "
                f"channel {channel!r} is not allowed. Only "
                "'conda-forge' may be used.",
            )

    match = re.match(
        r"^([A-Za-z0-9][A-Za-z0-9_.-]*)(?:\s*(.*))?$",
        specification,
    )

    if not match:
        raise _runtime_error(
            path,
            f"invalid {kind} dependency specification {raw_spec!r}. "
            "Expected a package name optionally followed by version "
            "constraints, for example 'python >= 3.11'.",
        )

    package_name = match.group(1).lower()
    if kind == "pip":
        package_name = _normalise_pip_name(package_name)
    constraint_text = (match.group(2) or "").strip()

    if not _PACKAGE_NAME_RE.fullmatch(package_name):
        raise _runtime_error(
            path,
            f"invalid package name {package_name!r} in dependency "
            f"{raw_spec!r}",
        )

    if not constraint_text:
        return package_name, []

    constraints: list[tuple[str, str]] = []

    for clause in constraint_text.split(","):
        clause = clause.strip()

        operator = next(
            (
                candidate
                for candidate in _OPERATORS
                if clause.startswith(candidate)
            ),
            None,
        )

        if (
            operator is None
            and kind == "conda"
            and _CONDA_BARE_VERSION_RE.fullmatch(clause)
        ):
            constraints.append(("", clause))
            continue

        if operator is None:
            raise _runtime_error(
                path,
                f"unsupported version constraint {clause!r} in "
                f"{kind} dependency {raw_spec!r}. Supported operators "
                f"are: {', '.join(_OPERATORS)}"
                + (
                    " (or a bare conda version like '1.26.*')."
                    if kind == "conda"
                    else "."
                ),
            )

        version = clause[len(operator):].strip()

        if not version:
            raise _runtime_error(
                path,
                f"missing version after operator {operator!r} in "
                f"{kind} dependency {raw_spec!r}",
            )

        constraints.append((operator, version))

    return package_name, constraints


def _format_constraints(
    constraints: list[tuple[str, str]],
) -> str:
    if not constraints:
        return ""

    return ",".join(
        f"{operator}{version}"
        for operator, version in constraints
    )


def _validate_version_policy(
    package_name: str,
    constraints: list[tuple[str, str]],
    allowed_pinnings: set[str],
    path: Path,
    kind: str,
    raw_spec: str,
) -> None:
    """
    Lower bounds using '>' or '>=' are always allowed.

    Exact versions, upper bounds, exclusions, and compatible-release
    constraints require the package to be listed in allowed_pinnings.
    """
    disallowed_constraints = [
        (operator, version)
        for operator, version in constraints
        if operator not in {">", ">="}
    ]

    if not disallowed_constraints:
        return

    if package_name in allowed_pinnings:
        return

    attempted_constraints = ", ".join(
        f"{operator}{version}"
        for operator, version in disallowed_constraints
    )

    allowed_names = ", ".join(
        repr(name)
        for name in sorted(allowed_pinnings)
    )

    if not allowed_names:
        allowed_names = "(none)"

    raise _runtime_error(
        path,
        f"invalid {kind} dependency {raw_spec!r}: package "
        f"{package_name!r} uses disallowed version constraint(s): "
        f"{attempted_constraints}. This policy allows lower bounds "
        "using '>' or '>=' for every package, but exact versions, "
        "upper bounds, exclusions, and compatible-release constraints "
        f"are allowed only for these {kind} packages: {allowed_names}.",
    )


def validate_conda_requirements(
    path_value: str | Path,
) -> list[dict[str, str]]:
    """
    Validate a conda environment YAML file.

    The returned list contains one dictionary per dependency. For example:

        [
            {
                "name": "mcstas",
                "source": "conda",
                "requirement": ">=3.8.8",
            },
            {
                "name": "pip",
                "source": "conda",
                "requirement": "",
            },
            {
                "name": "python",
                "source": "conda",
                "requirement": ">=3.11",
            },
            {
                "name": "requests",
                "source": "pip",
                "requirement": ">=2.31",
            },
        ]

    Every validation failure raises RuntimeError with the file path and
    an explanation of the violated policy.
    """
    path = Path(path_value)

    if path.suffix.lower() not in {".yml", ".yaml"}:
        raise _runtime_error(
            path,
            f"unsupported file extension {path.suffix!r}. Expected a "
            "conda environment file ending in '.yml' or '.yaml'.",
        )

    document = _parse_conda_yaml(path)

    if "channels" not in document:
        raise _runtime_error(
            path,
            "missing required top-level key 'channels'. The file must "
            "explicitly declare exactly one 'nodefaults' entry and one "
            "'conda-forge' entry.",
        )

    channels = [
        str(channel).strip().lower()
        for channel in document["channels"]
    ]

    expected_channels = {
        "nodefaults",
        "conda-forge",
    }

    if len(channels) != len(set(channels)):
        duplicates = sorted(
            {
                channel
                for channel in channels
                if channels.count(channel) > 1
            }
        )

        raise _runtime_error(
            path,
            f"invalid channels list {channels!r}: duplicate channel "
            f"entry/entries {duplicates!r} are not allowed. The required "
            "channel list must contain exactly one 'nodefaults' entry and "
            "one 'conda-forge' entry.",
        )

    actual_channels = set(channels)

    if actual_channels != expected_channels:
        missing_channels = sorted(
            expected_channels - actual_channels
        )
        unexpected_channels = sorted(
            actual_channels - expected_channels
        )

        details: list[str] = []

        if missing_channels:
            details.append(
                "missing required channel(s): "
                + ", ".join(repr(channel) for channel in missing_channels)
            )

        if unexpected_channels:
            details.append(
                "unexpected channel(s): "
                + ", ".join(
                    repr(channel)
                    for channel in unexpected_channels
                )
            )

        raise _runtime_error(
            path,
            f"invalid channels list {channels!r}: "
            + "; ".join(details)
            + ". The policy requires exactly 'nodefaults' and "
              "'conda-forge', in either order. 'nodefaults' prevents "
              "conda's configured default channels from being used.",
        )

    if "dependencies" not in document:
        raise _runtime_error(
            path,
            "missing required top-level key 'dependencies'. The file "
            "must contain a dependency list, including the mandatory "
            "conda packages: "
            + ", ".join(sorted(minimal_requirements))
            + ".",
        )

    conda_specs: list[str] = []
    pip_specs: list[str] = []

    for item in document["dependencies"]:
        if isinstance(item, dict):
            if set(item) != {"pip"}:
                raise _runtime_error(
                    path,
                    f"unsupported nested dependency mapping {item!r}. "
                    "The only supported nested dependency mapping is "
                    "'pip:', containing a list of pip package specifications.",
                )

            pip_value = item["pip"]

            if not isinstance(pip_value, list):
                raise _runtime_error(
                    path,
                    f"invalid 'pip:' section value {pip_value!r}: "
                    "the value of 'pip:' must be a YAML list.",
                )

            pip_specs.extend(pip_value)

        else:
            conda_specs.append(item)

    conda_names: set[str] = set()
    pip_names: set[str] = set()
    result: list[dict[str, str]] = []

    for raw_spec in conda_specs:
        package_name, constraints = _split_package_spec(
            raw_spec,
            path,
            "conda",
        )

        if package_name in forbidden_requirements:
            raise _runtime_error(
                path,
                f"forbidden conda dependency {raw_spec!r}: package "
                f"{package_name!r} appears in the hardwired "
                f"forbidden_requirements list "
                f"{sorted(forbidden_requirements)!r}. Remove this "
                "package from the conda dependency list.",
            )

        if package_name in conda_names:
            raise _runtime_error(
                path,
                f"duplicate conda dependency {raw_spec!r}: package "
                f"{package_name!r} has already appeared in the conda "
                "dependency list. Each package may be listed only once.",
            )

        _validate_version_policy(
            package_name=package_name,
            constraints=constraints,
            allowed_pinnings=conda_pinning_allowed,
            path=path,
            kind="conda",
            raw_spec=raw_spec,
        )

        conda_names.add(package_name)

        result.append(
            {
                "name": package_name,
                "source": "conda",
                "requirement": _format_constraints(constraints),
            }
        )

    for raw_spec in pip_specs:
        package_name, constraints = _split_package_spec(
            raw_spec,
            path,
            "pip",
        )

        if package_name in forbidden_requirements:
            raise _runtime_error(
                path,
                f"forbidden pip dependency {raw_spec!r}: package "
                f"{package_name!r} appears in the hardwired "
                f"forbidden_requirements list "
                f"{sorted(forbidden_requirements)!r}. Remove this "
                "package from the 'pip:' section.",
            )

        if package_name not in {
            _normalise_pip_name(name) for name in pip_requirements_allowed
        }:
            allowed = ", ".join(
                repr(name)
                for name in sorted(pip_requirements_allowed)
            )

            raise _runtime_error(
                path,
                f"pip dependency {raw_spec!r} is not allowed by policy. "
                f"Only these packages may be installed with pip: "
                f"{allowed}. Add {package_name!r} to the hardwired "
                "'pip_requirements_allowed' set if this package is "
                "intentionally permitted.",
            )

        if package_name in {
            _normalise_pip_name(name) for name in conda_names
        }:
            raise _runtime_error(
                path,
                f"dependency-source conflict for package "
                f"{package_name!r}: it appears both as a conda "
                f"dependency and as a pip dependency ({raw_spec!r}). "
                "This policy prefers the conda-forge package when the "
                "package is available as a conda dependency. Remove "
                "the pip entry or remove the conda entry, as appropriate.",
            )

        if package_name in pip_names:
            raise _runtime_error(
                path,
                f"duplicate pip dependency {raw_spec!r}: package "
                f"{package_name!r} has already appeared in the 'pip:' "
                "section. Each package may be listed only once.",
            )

        _validate_version_policy(
            package_name=package_name,
            constraints=constraints,
            allowed_pinnings={
                _normalise_pip_name(name) for name in pip_pinning_allowed
            },
            path=path,
            kind="pip",
            raw_spec=raw_spec,
        )

        pip_names.add(package_name)

        result.append(
            {
                "name": package_name,
                "source": "pip",
                "requirement": _format_constraints(constraints),
            }
        )

    missing = minimal_requirements - conda_names

    if missing:
        missing_text = ", ".join(
            repr(package_name)
            for package_name in sorted(missing)
        )

        required_text = ", ".join(
            repr(package_name)
            for package_name in sorted(minimal_requirements)
        )

        raise _runtime_error(
            path,
            f"missing mandatory conda dependency/ies: {missing_text}. "
            f"Every valid file must list all of these packages as conda "
            f"dependencies: {required_text}. These requirements cannot "
            "be satisfied through the pip subsection.",
        )

    _validate_mcstas_lower_bound(path, conda_specs)

    return result


def _validate_mcstas_lower_bound(path: Path, conda_specs: list[str]) -> None:
    """
    The mcstas dependency must have an explicit lower bound of at least
    minimum_mcstas_version, e.g. "mcstas >= 3.8.8".
    """
    min_str = ".".join(str(i) for i in minimum_mcstas_version)
    for raw_spec in conda_specs:
        package_name, constraints = _split_package_spec(raw_spec, path, "conda")
        if package_name != "mcstas":
            continue
        for operator, version in constraints:
            if operator not in {">=", ">"}:
                continue
            version_tuple = _version_tuple(version)
            if version_tuple is None:
                raise _runtime_error(
                    path,
                    f"invalid mcstas dependency {raw_spec!r}: could not "
                    f"parse version {version!r} (expected e.g. {min_str!r}).",
                )
            if version_tuple >= minimum_mcstas_version:
                return
        raise _runtime_error(
            path,
            f"invalid mcstas dependency {raw_spec!r}: it must have an "
            f"explicit lower bound of at least {min_str}, for example "
            f"'mcstas >= {min_str}'.",
        )
