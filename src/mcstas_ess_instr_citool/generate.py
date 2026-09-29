from pathlib import Path
import importlib
import multiprocessing as mp
import sys
import traceback
import os

# Max time (seconds) allowed for generating a single .instr file from a
# McStasScript python file:
DEFAULT_PYGEN_TIMEOUT = 600

def generate( info, outdir, pygen_timeout = DEFAULT_PYGEN_TIMEOUT ):
    assert outdir.is_dir()
    instrdir = outdir.joinpath('instr')
    if info['layout']=='instrpy':
        def genfct( name, srcpath, outdir ):
            return _genpy( name, srcpath, outdir, timeout = pygen_timeout )
    else:
        genfct = _gen
    setups = info['setups']
    if not setups:
        raise RuntimeError('No instruments found!')
    assert len(setups) == len(set(k for k in setups))
    instrdir.mkdir()
    for k,v in setups.items():
        d = instrdir.joinpath(k)
        d.mkdir()
        os.chdir(d)
        genfct( k, P(v), d )
        for subdirname, fns in sorted(info["extra_files"].items()):
            sd = d.joinpath(subdirname)
            sd_src = P(v).parent.joinpath(subdirname)
            assert sd_src.is_dir()
            print(f"Making directory {sd.name}/")
            sd.mkdir()
            os.chdir(sd)
            for fn in fns:
                _gen( k, sd_src.joinpath(fn), sd )

    return instrdir

def is_empty_dir(path: str | Path) -> bool:
    path = Path(path)
    return path.is_dir() and not any(path.iterdir())

def _worker(conn, name, srcpath, outdir):
    outdir = Path(outdir).resolve()
    srcpath = Path(srcpath)
    filename = Path(outdir).joinpath(srcpath.stem+'.instr').resolve()
    assert not filename.exists(), f"file already found: {filename}"
    try:
        srcpath = Path(srcpath).resolve()
        package, parts = srcpath.parent, [srcpath.stem]
        assert (package / "__init__.py").is_file()
        parts.insert(0, package.name)
        package = package.parent
        assert not (package / "__init__.py").is_file(), "spurious __init__.py"
        assert len(parts)==2
        # Do not write __pycache__ directories into the project:
        sys.dont_write_bytecode = True
        sys.path.insert(0, str(package))
        impname = ".".join(parts)
        print(f"Importing {impname}")
        mod = importlib.import_module(impname)
        print("   ... Calling .make()")
        instr = mod.make()
        if instr.name != filename.stem:
            raise ValueError(f'Instrument loaded from {srcpath} has '
                             f'unexpected name. Expected "{filename.stem}" '
                             f'but got "{instr.name}"')
        print("   ... Calling .write_full_instrument()")
        instr.write_full_instrument()
        ok = True
        for f in filename.parent.rglob('*'):
            if f.resolve() == filename:
                continue
            if is_empty_dir(f):
                print(f"   WARNING: Removing spurious empty directory {f.name}")
                f.rmdir()
            else:
                print(f"ERROR: Unexpected file generated: {f}")
                conn.send(("extrafiles", None))
                ok = False
        if not filename.exists():
            print(f"Did not find file:: {filename}")
            conn.send(("missingfile", None))
            ok = False
        if ok:
            conn.send(("ok", None))
    except BaseException:
        conn.send(("error", traceback.format_exc()))
    finally:
        conn.close()


def _genpy( name, srcpath, outdir, timeout = DEFAULT_PYGEN_TIMEOUT ):
    ctx = mp.get_context("spawn")
    parent, child = ctx.Pipe(duplex=False)
    process = ctx.Process(
        target=_worker,
        args=(child, str(name), str(srcpath), str(outdir) ),
    )
    process.start()
    child.close()
    try:
        if not parent.poll(timeout):
            process.terminate()
            process.join()
            raise TimeoutError(f"Process timed out after {timeout} seconds"
                               f" for instrument: {srcpath}")
        try:
            status, message = parent.recv()
        except EOFError:
            status, message = "error", (
                f"Child exited without reporting success "
                f"(exit code {process.exitcode})"
            )
    finally:
        parent.close()
    process.join()
    if status != "ok":
        raise RuntimeError(message)

def P(p):
    return Path(p).resolve().absolute()

def _gen( name, srcpath, outdir):
    print(f"Copying {srcpath.name}")
    outdir.joinpath(srcpath.name).write_text( srcpath.read_text() )
