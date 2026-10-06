"""Errors which are reported to the user without a Python traceback (unless
the --errtrace flag is used), since they are caused by the project or the
environment rather than by a bug in the tool. Other exceptions are always
reported with a traceback."""


class UserError(Exception):
    """Base class of errors reported without a traceback."""


class ProjectError(UserError, ValueError):
    """A problem in the project, e.g. a file not following the standard
    layout."""


class CheckFailed(UserError, RuntimeError):
    """A check or test of the project failed."""


class SetupError(UserError, RuntimeError):
    """A problem with the environment, e.g. a missing or too old McStas."""
