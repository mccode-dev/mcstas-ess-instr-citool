import argparse
import os
from pathlib import Path
from tempfile import TemporaryDirectory

ACTIONS = ["generate", "generatepy", "runci", "list", "check", "json", "pprint"]
DEFAULT_ACTION = "list"

assert DEFAULT_ACTION in ACTIONS

def output_dir(value):
    p = Path(value).expanduser()
    if p.exists():
        if not p.is_dir():
            raise argparse.ArgumentTypeError(f"{p} is not a directory")
        if any(p.iterdir()):
            raise argparse.ArgumentTypeError(f"{p} is not empty")
    elif not p.parent.is_dir():
        raise argparse.ArgumentTypeError(f"parent directory {p.parent} does not exist")
    return p

def mpi_value(value):
    if value == 'auto':
        return value
    try:
        n = int(value)
    except ValueError:
        n = 0
    if n < 1:
        raise argparse.ArgumentTypeError(
            f'invalid value {value!r} (must be a positive integer or "auto")')
    return n

def parse_args(argv=None,prog=None):
    if argv is None:
        import sys
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(prog=prog)

    parser.add_argument(
        "project_dir",
        help='Path to a directory containing a "project".',
    )

    parser.add_argument(
        "-a",
        "--action",
        dest="action",
        choices=ACTIONS,
        default=DEFAULT_ACTION,
        help=f'Action: {ACTIONS} (default: "{DEFAULT_ACTION}").',
    )

    parser.add_argument('--outdir','-o', type=output_dir, metavar='DIR',
                        default=None,
                        help=('Select output directory (when relevant).'
                              ' Must be empty or non-existing). Default is to'
                              ' use a temporarily and autocleaned directory.'))

    parser.add_argument('--mpi', type=mpi_value, metavar='N', default=None,
                        help=('Compile and run the instruments with MPI, using'
                              ' N processes (or "auto" for the number of'
                              ' available processors). Only for action runci.'
                              ' Default is to not use MPI.'))

    args = parser.parse_args(argv)
    if args.mpi is not None and args.action != 'runci':
        parser.error('--mpi can only be used with action runci')
    if args.action == 'generatepy' and args.outdir is None:
        parser.error('--outdir is required for action generatepy')
    args.project_dir = Path(args.project_dir)
    return args

class OutDirMgr:
    def __init__(self, outdir: Path | None):
        self._requested = outdir

    def __enter__(self) -> Path:
        self._cwd = Path.cwd()
        self._tmp = TemporaryDirectory() if self._requested is None else None
        if self._tmp:
            print(f"Created temporary directory {self._tmp.name}")

        self.outdir = ( Path(self._tmp.name)
                        if self._tmp else Path(self._requested).resolve() )
        try:
            self.outdir.mkdir(parents=True, exist_ok=True)
            os.chdir(self.outdir)
            return self.outdir
        except BaseException:
            if self._tmp:
                self._tmp.cleanup()
            raise

    def __exit__(self, *args) -> None:
        try:
            os.chdir(self._cwd)
        finally:
            if self._tmp:
                print(f"Cleaning temporary directory {self._tmp.name}")
                self._tmp.cleanup()

def main( argv = None ):
    args = parse_args(argv)
    from .analyse import analyse_dir
    info = analyse_dir( args.project_dir )

    if args.action=='json':
        import json
        print(json.dumps(info),end='')
    elif args.action=='pprint':
        import pprint
        pprint.pp(info)
    elif args.action=='list':
        from .summary import summary
        summary(info)
    elif args.action=='check':
        print("File and directory structure OK")
    elif args.action=='generatepy':
        from .generatepy import generatepy
        generatepy(info,args.outdir)
    elif args.action=='generate':
        from .generate import generate
        with OutDirMgr(args.outdir) as outdir:
            generate(info,outdir)
    else:
        assert args.action=='runci'
        from .runtest import runtest
        with OutDirMgr(args.outdir) as outdir:
            runtest(info,outdir,mpi=args.mpi)

if __name__ == "__main__":
    main()
