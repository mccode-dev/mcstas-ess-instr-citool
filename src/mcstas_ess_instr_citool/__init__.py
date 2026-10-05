def version():
    """Version of the installed package, which is taken from the git tag it
    was built from (see the README)."""
    import importlib.metadata
    try:
        return importlib.metadata.version("mcstas-ess-instr-citool")
    except importlib.metadata.PackageNotFoundError:
        # Not installed (e.g. used directly from the source directory):
        return "unversioned_local_source"
