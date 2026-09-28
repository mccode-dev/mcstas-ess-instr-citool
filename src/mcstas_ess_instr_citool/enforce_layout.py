import os
import re
from typing import Dict, List, Optional
import pathlib
import fnmatch

import tomllib  # Python 3.11+ only

def _is_ignored(fname: str) -> bool:
    # Hidden files (.DS_Store, .#emacs-lock, ...) and backup files (foo~)
    return fname.startswith('.') or fname.endswith('~')

def enforce_instr_layout(project_dir: str) -> Dict:
    """
    Enforce one of these layouts under `project_dir`:

    1) project_dir/instr/
       - exactly one PROJECT_main.instr
       - zero or more PROJECT_modeMODENAME.instr
       - optional files: includes/*.(h|c) and snippets/*.instr

    2) project_dir/instrpy/
       - must contain instrpy/pyproject.toml (PEP 621 only; [project].name required)
       - must contain a subdir instrpy/PROJECTNAME_instr/
         - empty __init__.py (size == 0)
         - exactly one PROJECT_main.py
         - zero or more PROJECT_modeMODENAME.py

    Hidden files (names starting with '.') and backup files (names ending
    with '~') are ignored. Other files are in general ignored.

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
                             subdirpatterns : list[str] | None = None ) -> Dict:
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
                for fextra in sorted(fabs.iterdir()):
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

        project_name: Optional[str] = None
        main_path: Optional[str] = None
        mode_names: List[str] = []
        mode_paths: List[str] = []
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

            errstr = (
                f"Unexpected file '{fname}' in '{base_dir}'. "
                f"Only PROJECT_main{ext} and PROJECT_modeMODENAME{ext} files are allowed"
            )
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

        if len(set(mode_names)) != len(mode_names):
            dupes = sorted({m for m in mode_names if mode_names.count(m) > 1})
            raise ValueError(f"Duplicate mode name(s) found: {dupes}")

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
                for mode, path in sorted(zip(mode_names, mode_paths), key=lambda x: x[0])
            ],
            "mode_names": sorted(mode_names),
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
                                       'snippets/*.instr'])
        return {
            "project_dir": project_dir,
            "layout": "instr",
            "base_dir": instr_dir,
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
    instrpy_subdir = os.path.join(instrpy_dir, subdir_name)

    init_path = os.path.join(instrpy_subdir, "__init__.py")
    if not os.path.isfile(init_path):
        raise ValueError("In 'instrpy/PROJECTNAME_instr', '__init__.py' must exist.")
    init_size = os.path.getsize(init_path)
    if init_size != 0:
        raise ValueError(f"In 'instrpy/PROJECTNAME_instr', '__init__.py' must be empty (size 0), got {init_size} bytes.")

    ext = ".py"
    payload = ensure_files_in_dir(instrpy_subdir, ext)

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
        "pyproject": {"path": pyproject_path, "declared_project_name": declared_project_name},
        **payload,
    }
