import fnmatch
import keyword
import os
import pathlib
import re
import tomllib  # Python 3.11+ only

from .localfiles import subdir_patterns


def _is_ignored(fname: str) -> bool:
    # Hidden files (.DS_Store, .#emacs-lock, ...) and backup files (foo~)
    return fname.startswith('.') or fname.endswith('~')

def _instrument_name(path: str) -> str | None:
    """Name given by the (first) DEFINE INSTRUMENT statement of an .instr file,
    ignoring comments."""
    text = pathlib.Path(path).read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)
    text = re.sub(r"//[^\n]*", " ", text)
    m = re.search(r"\bDEFINE\s+INSTRUMENT\s+([A-Za-z_]\w*)", text)
    return m.group(1) if m else None

# Directories and files allowed at the top level of a project (in addition to
# hidden files like .gitignore or .gitlab-ci.yml, which are ignored):
ROOT_DIRS = ("instr", "instrpy", "extra", "extra_pytests")
ROOT_FILE_PATTERNS = ("conda.yml", "README*", "TODO*", "LICENSE*", "CHANGELOG*")
# Local directories which are not part of the project (not in git):
ROOT_IGNORED_DIRS = ("__pycache__", "venv")

def check_root_entries(project_dir: str) -> None:
    """Raise ValueError if the top level of the project contains anything
    else than the allowed directories and files."""
    for entry in sorted(os.listdir(project_dir)):
        path = os.path.join(project_dir, entry)
        if _is_ignored(entry) or ( entry in ROOT_IGNORED_DIRS
                                   and os.path.isdir(path) ):
            continue
        if entry in ROOT_DIRS:
            if not os.path.isdir(path):
                raise ValueError(f"'{entry}' in '{project_dir}' must be a directory.")
            continue
        if ( os.path.isfile(path)
             and any(fnmatch.fnmatchcase(entry, p) for p in ROOT_FILE_PATTERNS) ):
            continue
        raise ValueError(
            f"Unexpected file or directory '{entry}' in '{project_dir}'."
            " Only the directories " + ", ".join(f"{d}/" for d in ROOT_DIRS)
            + " and the files " + ", ".join(ROOT_FILE_PATTERNS)
            + " are allowed (anything else can be placed in extra/).")

def enforce_instr_layout(project_dir: str) -> dict:
    """
    Enforce one of these layouts under `project_dir`:

    1) project_dir/instr/
       - exactly one PROJECT_main.instr
       - zero or more PROJECT_modeMODENAME.instr
       - optional files: includes/*.(h|c) and snippets/*.instr
       - optional local components localcomps/*.(comp|c|h) and data files
         localdata/* (only certain types, see localfiles.py)
       - the instrument in each main/mode file must be named after the file
         (e.g. DEFINE INSTRUMENT PROJECT_main)

    2) project_dir/instrpy/
       - must contain instrpy/pyproject.toml (PEP 621 only; [project].name required)
       - nothing else than pyproject.toml and PROJECTNAME_instr/ is allowed
         (except for __pycache__/ and *.egg-info/ created by python tools)
       - must contain a subdir instrpy/PROJECTNAME_instr/
         - empty __init__.py (size == 0)
         - exactly one PROJECT_main.py
         - zero or more PROJECT_modeMODENAME.py
         - zero or more helper modules MODULE.py (MODULE must be a valid
           python identifier, not starting with PROJECT_)
         - optional files: includes/*.(h|c), localcomps/*.(comp|c|h) and
           localdata/* (only certain types, see localfiles.py)

    The top level of project_dir may only contain conda.yml, the instr/ or
    instrpy/ directory, the optional directories extra/ (anything, with no
    rules) and extra_pytests/ (tests run with pytest), and files named
    README*, TODO*, LICENSE* or CHANGELOG*. If extra_pytests/ exists, pytest
    must be listed in conda.yml.

    Hidden files (names starting with '.') and backup files (names ending
    with '~') are ignored.

    PROJECTNAME: [A-Za-z][A-Za-z0-9]*
    MODENAME:     [A-Za-z][A-Za-z0-9]*

    Returns a dictionary with parsed/validated info.

    Raises ValueError on violations.
    """
    project_dir = os.path.abspath(project_dir)
    instr_dir = os.path.join(project_dir, "instr")
    instrpy_dir = os.path.join(project_dir, "instrpy")


    condareqfile = os.path.join(project_dir, "conda.yml")
    if not os.path.isfile(condareqfile):
        raise ValueError(f"Missing conda requirements file: {condareqfile}")

    from .check_condayml import validate_conda_requirements
    condareq = validate_conda_requirements(condareqfile)

    check_root_entries(project_dir)
    extra_dir = os.path.join(project_dir, "extra")
    extra_pytests_dir = os.path.join(project_dir, "extra_pytests")
    extras = {
        "extra_dir": extra_dir if os.path.isdir(extra_dir) else None,
        "extra_pytests_dir": extra_pytests_dir if os.path.isdir(extra_pytests_dir) else None,
    }
    if extras["extra_pytests_dir"] and not any(
            r["name"] == "pytest" for r in condareq):
        raise ValueError("pytest must be listed in conda.yml, since the"
                         " project has an extra_pytests/ directory.")

    has_instr = os.path.isdir(instr_dir)
    has_instrpy = os.path.isdir(instrpy_dir)

    if has_instr == has_instrpy:  # both True or both False
        raise ValueError(
            "Must have exactly one of directories: 'instr' or 'instrpy'. "
            f"Found: instr={has_instr}, instrpy={has_instrpy}."
        )

    project_re = r"(?P<project>[A-Za-z][A-Za-z0-9]*)"
    mode_re = r"(?P<mode>[A-Za-z][A-Za-z0-9]*)"

    def ensure_files_in_dir( base_dir: str,
                             ext: str,
                             subdirpatterns : list[str] | None = None,
                             allow_helpers : bool = False ) -> dict:
        main_pat = re.compile(rf"^{project_re}_main{re.escape(ext)}$")
        mode_pat = re.compile(rf"^{project_re}_mode{mode_re}{re.escape(ext)}$")

        all_files = [
            f for f in sorted(os.listdir(base_dir))
            if not _is_ignored(f) and not f=='__pycache__'
        ]

        subdirs = {}
        for e in (subdirpatterns or []):
            e = e.split('/',1)
            if e[0] not in subdirs:
                subdirs[e[0]] = [e[1]]
            else:
                subdirs[e[0]] += [e[1]]

        extra_files = {}
        allowed_subdirs_str = " ".join(subdirs.keys())

        for f in all_files:
            fabs = pathlib.Path(os.path.join(base_dir, f))
            if fabs.is_dir():
                dirname = fabs.name
                if dirname not in subdirs:
                    raise ValueError(f'Directory {dirname} not allowed in'
                                     f' {base_dir}. Only allowed subdirs'
                                     f' are: {allowed_subdirs_str or "<none>"}')
                for fextra in sorted(fabs.iterdir(), key=lambda f: f.name):
                    if _is_ignored(fextra.name):
                        continue
                    if fextra.is_dir():
                        raise ValueError(f'Forbidden subdir: {fextra}')
                    if not any(fnmatch.fnmatch(fextra.name, pat)
                               for pat in subdirs[dirname]):
                        raise ValueError(f'File {fextra.name} not allowed in'
                                         f' {fextra.parent}. Patterns allowed:'
                                         f' {subdirs[dirname]}')
                    extra_files.setdefault(dirname, []).append( fextra.name )

        project_name: str | None = None
        main_path: str | None = None
        helper_files: list[str] = []
        mode_names: list[str] = []
        mode_paths: list[str] = []
        main_count = 0


        for fname in all_files:
            if os.path.isdir(os.path.join(base_dir, fname)):
                # Allowed subdir (possibly empty), already validated above.
                continue

            if fname == "__init__.py":
                # Only valid under the instrpy/PROJECTNAME_instr/ subdir and validated elsewhere.
                continue

            m_main = main_pat.match(fname)
            if m_main:
                this_project = m_main.group("project")
                if project_name is None:
                    project_name = this_project
                elif this_project != project_name:
                    raise ValueError(
                        f"All main/mode files must share PROJECTNAME. "
                        f"Expected '{project_name}', got '{this_project}' in '{fname}'."
                    )
                main_count += 1
                main_path = os.path.join(base_dir, fname)
                continue

            m_mode = mode_pat.match(fname)
            if m_mode:
                this_project = m_mode.group("project")
                this_mode = m_mode.group("mode")

                if project_name is None:
                    project_name = this_project
                elif this_project != project_name:
                    raise ValueError(
                        f"All main/mode files must share PROJECTNAME. "
                        f"Expected '{project_name}', got '{this_project}' in '{fname}'."
                    )

                mode_names.append(this_mode)
                mode_paths.append(os.path.join(base_dir, fname))
                continue

            if allow_helpers and fname.endswith(ext):
                # Validated below, when the project name is known:
                helper_files.append(fname)
                continue

            errstr = (
                f"Unexpected file '{fname}' in '{base_dir}'. "
                f"Only PROJECT_main{ext} and PROJECT_modeMODENAME{ext} files are allowed"
            )
            if allow_helpers:
                errstr += f' (and helper modules named MODULE{ext})'
            if subdirs:
                errstr += f' - in addition to subdirs: {allowed_subdirs_str}.'
            else:
                errstr += '.'
            raise ValueError(errstr)

        if project_name is None:
            raise ValueError(f"No valid PROJECT_main{ext} file found in '{base_dir}'.")
        if main_count != 1:
            raise ValueError(
                f"Must have exactly one file named '{project_name}_main{ext}' in '{base_dir}'. "
                f"Found {main_count}."
            )

        helper_modules = []
        for fname in sorted(helper_files):
            stem = fname[:-len(ext)]
            if stem.startswith(f"{project_name}_"):
                raise ValueError(
                    f"Unexpected file '{fname}' in '{base_dir}'. Files named"
                    f" {project_name}_* must be either {project_name}_main{ext}"
                    f" or {project_name}_modeMODENAME{ext} (with MODENAME"
                    " matching [A-Za-z][A-Za-z0-9]*).")
            if not stem.isidentifier() or keyword.iskeyword(stem):
                raise ValueError(
                    f"Invalid helper module name '{fname}' in '{base_dir}'."
                    " Helper module names must be valid python identifiers.")
            helper_modules.append(stem)

        if len(set(mode_names)) != len(mode_names):
            dupes = sorted({m for m in mode_names if mode_names.count(m) > 1})
            raise ValueError(f"Duplicate mode name(s) found: {dupes}")

        if len(set(m.lower() for m in mode_names)) != len(mode_names):
            raise ValueError("Clashing mode names detected (mode names must"
                             " differ by more than upper/lower case):"
                             f" {sorted(mode_names)}")

        for pat in ['main','test']:
            if any( m.lower().strip()==pat for m in mode_names ):
                raise ValueError(f'"{pat}" is not allowed as a mode name')

        return {
            "project_name": project_name,
            "condareq" : condareq,
            "main": {"filename": f"{project_name}_main{ext}", "path": main_path},
            "extra_files" : extra_files,
            "modes": [
                {"mode": mode, "path": path}
                for mode, path in sorted(zip(mode_names, mode_paths, strict=True), key=lambda x: x[0])
            ],
            "mode_names": sorted(mode_names),
            "helper_modules": helper_modules,
        }

    def normalize_pkg_name(name: str) -> str:
        # PEP 503-ish normalization commonly used to compare distributions/packages.
        return re.sub(r"[-_.]+", "-", name.strip().lower()).strip("-")

    def require_pep621_project_name(pyproject_path: str) -> str:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)

        project_tbl = data.get("project")
        if not isinstance(project_tbl, dict):
            raise ValueError("In 'instrpy', pyproject.toml must use PEP 621 with a [project] table.")

        declared = project_tbl.get("name")
        if not isinstance(declared, str) or not declared.strip():
            raise ValueError("In 'instrpy', pyproject.toml [project].name is required and must be a non-empty string.")

        return declared.strip()

    # ---- instr layout ----
    if has_instr:
        ext = ".instr"
        payload = ensure_files_in_dir(instr_dir, ext,
                                      ['includes/*.h',
                                       'includes/*.c',
                                       'snippets/*.instr']
                                      + subdir_patterns())
        for path in ( [payload["main"]["path"]]
                      + [m["path"] for m in payload["modes"]] ):
            expected = pathlib.Path(path).stem
            found = _instrument_name(path)
            if found != expected:
                raise ValueError(
                    f"The instrument in '{path}' must be named after the"
                    f" file, i.e. 'DEFINE INSTRUMENT {expected}(...)'"
                    + (f" (found '{found}')." if found else
                       " (no DEFINE INSTRUMENT found)."))
        return {
            "project_dir": project_dir,
            "layout": "instr",
            "base_dir": instr_dir,
            **extras,
            **payload,
        }

    # ---- instrpy layout ----
    pyproject_path = os.path.join(instrpy_dir, "pyproject.toml")
    if not os.path.isfile(pyproject_path):
        raise ValueError("In 'instrpy', pyproject.toml must exist.")

    # Must contain exactly one subdir named PROJECTNAME_instr
    subdir_suffix = "_instr"
    subdirs = [
        d for d in sorted(os.listdir(instrpy_dir))
        if os.path.isdir(os.path.join(instrpy_dir, d))
    ]

    subdir_project_re = re.compile(rf"^{project_re}{re.escape(subdir_suffix)}$")

    candidates = []
    for d in subdirs:
        m = subdir_project_re.match(d)
        if m:
            candidates.append((m.group("project"), d))

    if len(candidates) != 1:
        raise ValueError(
            "In 'instrpy', there must be exactly one subdirectory named 'PROJECTNAME_instr'. "
            f"Found {len(candidates)} candidates."
        )

    project_name_from_subdir, subdir_name = candidates[0]

    # Nothing else is allowed in instrpy/, except for files and directories
    # created by python tools (like "pip install -e"):
    for entry in sorted(os.listdir(instrpy_dir)):
        if ( _is_ignored(entry) or entry == "__pycache__"
             or entry.endswith(".egg-info") ):
            continue
        if entry not in ("pyproject.toml", subdir_name):
            raise ValueError(
                f"Unexpected file or directory '{entry}' in '{instrpy_dir}'."
                f" Only pyproject.toml and {subdir_name}/ are allowed.")
    instrpy_subdir = os.path.join(instrpy_dir, subdir_name)

    init_path = os.path.join(instrpy_subdir, "__init__.py")
    if not os.path.isfile(init_path):
        raise ValueError("In 'instrpy/PROJECTNAME_instr', '__init__.py' must exist.")
    init_size = os.path.getsize(init_path)
    if init_size != 0:
        raise ValueError(f"In 'instrpy/PROJECTNAME_instr', '__init__.py' must be empty (size 0), got {init_size} bytes.")

    ext = ".py"
    payload = ensure_files_in_dir(instrpy_subdir, ext,
                                  ['includes/*.h',
                                   'includes/*.c']
                                  + subdir_patterns(),
                                  allow_helpers = True)

    if payload["project_name"] != project_name_from_subdir:
        raise ValueError(
            "PROJECTNAME must be consistent between the subdir name and filenames. "
            f"Subdir PROJECTNAME='{project_name_from_subdir}', but filenames PROJECTNAME='{payload['project_name']}'."
        )

    # Strict pyproject validation: PEP 621 [project].name only; it must match PROJECTNAME
    declared_project_name = require_pep621_project_name(pyproject_path)
    if normalize_pkg_name(declared_project_name) != normalize_pkg_name(payload["project_name"]):
        raise ValueError(
            "In 'instrpy', pyproject.toml [project].name must match PROJECTNAME. "
            f"Expected (normalized) '{normalize_pkg_name(payload['project_name'])}', "
            f"got '{declared_project_name}'."
        )

    return {
        "project_dir": project_dir,
        "layout": "instrpy",
        "base_dir": instrpy_subdir,
        **extras,
        "pyproject": {"path": pyproject_path, "declared_project_name": declared_project_name},
        **payload,
    }
