import argparse
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ACTIONS = ["generate", "generatepy", "runci", "list", "check", "json", "pprint",
           "repos", "repos-json"]
# Actions which do not need a project directory:
NO_PROJECT_ACTIONS = ["repos", "repos-json"]
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

    from . import version
    parser.add_argument('--version', action='version',
                        version=f'%(prog)s {version()}',
                        help='Show the version of the tool and exit.')

    parser.add_argument(
        "project_dir", nargs="?", default=None,
        help=('Path to a directory containing a "project" (not needed for'
              f' the actions {NO_PROJECT_ACTIONS}).'),
    )

    parser.add_argument(
        "-a",
        "--action",
        dest="action",
        choices=ACTIONS,
        default=DEFAULT_ACTION,
        help=(f'Action: {ACTIONS} (default: "{DEFAULT_ACTION}"). The actions'
              ' "repos" and "repos-json" list the instrument repositories at'
              ' DMSC (as a table, or as JSON).'),
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

    parser.add_argument('--lenient', action='store_true',
                        help=('Ignore (with a warning) unexpected files and'
                              ' directories in the project, e.g. temporary'
                              ' files in a working copy, instead of failing.'
                              ' Only for testing locally: not allowed in CI'
                              ' (when the CI environment variable is set).'))

    args = parser.parse_args(argv)
    if args.lenient and os.environ.get('CI'):
        parser.error('--lenient is not allowed in CI (the CI environment'
                     ' variable is set)')
    if args.mpi is not None and args.action != 'runci':
        parser.error('--mpi can only be used with action runci')
    if args.action == 'generatepy' and args.outdir is None:
        parser.error('--outdir is required for action generatepy')
    if args.action in NO_PROJECT_ACTIONS:
        if args.project_dir is not None:
            parser.error(f'action {args.action} does not take a project directory')
    else:
        if args.project_dir is None:
            parser.error(f'action {args.action} needs a project directory')
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
    if args.action == 'repos':
        from .repodb import print_table
        print_table()
        return
    if args.action == 'repos-json':
        import json

        from .repodb import repos
        print(json.dumps(repos()))
        return
    from .analyse import analyse_dir
    info = analyse_dir( args.project_dir, lenient = args.lenient )

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
    if info['ignored']:
        print(f"WARNING: {len(info['ignored'])} unexpected file(s) or"
              " directories were ignored (--lenient). CI will fail on them"
              " unless they are removed (or not committed).", file=sys.stderr)

if __name__ == "__main__":
    main()
