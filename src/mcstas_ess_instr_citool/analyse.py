
from pathlib import Path

from .enforce_layout import enforce_instr_layout


def analyse_dir( project_dir, lenient = False ):
    info = enforce_instr_layout(project_dir, lenient = lenient)
    merged_modes = {'MAIN':info['main']['path']}
    merged_modes.update(dict(sorted( (m['mode'],m['path'])
                                     for m in info['modes'] )))
    info['setups'] = merged_modes
    if len(set(m.lower().strip() for m in merged_modes)) != len(merged_modes):
        raise ValueError('Clashing mode names detected')

    pypkgname = None
    if info['layout']=='instrpy':
        for v in merged_modes.values():
            ppn = Path(v).parent.name
            if pypkgname is None:
                pypkgname = ppn
            elif ppn != pypkgname:
                raise ValueError('Could not infer a consistent python pkg name')
    info['pypkgname'] = pypkgname
    return info
