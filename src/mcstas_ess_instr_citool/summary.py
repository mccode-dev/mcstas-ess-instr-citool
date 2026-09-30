layout_pretty = { 'instr' : 'Classic McStas .instr files',
                  'instrpy' : 'McStasScript python files' }

def summary(info):
    from pathlib import Path
    def P(p):
        return Path(p).resolve().absolute()
    pdir = P(info['project_dir'])
    def prel(p):
        return str(P(p).relative_to(pdir))
    print()
    print("McStas instrument simulation project:")
    print()
    print(f"  Instrument project: {info['project_name']}")
    print(f"  Technology:  {layout_pretty[info['layout']]}")
    print(f"  Project directory:  {pdir}")
    print("  Instrument modes:")
    n = max(len(k) for k,v in info['setups'].items())
    indent = ' '*len('  Instrument modes:  ')
    for name,path in info['setups'].items():
        print(f"{indent}{name.ljust(n+1)}: {prel(path)}")
    if info['helper_modules']:
        print(f"  Helper modules:     {', '.join(info['helper_modules'])}")
    if info['pypkgname'] is not None:
        print('  Example python imports:')
        for path in info['setups'].values():
            p = P(path)
            assert p.parent.name == info['pypkgname']
            print(f"{indent}from {p.parent.name}.{p.stem} import make as make_instr")
    print()

