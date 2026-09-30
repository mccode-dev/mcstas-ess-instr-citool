# Extra content of the ExPyExtra project

Everything in `extra/` is project-specific and not checked by
mcstas-ess-instr-citool. Here:

* `expyextra_analysis/`: a python package with analysis code (installable
  with `pip install -e extra`).
* `run_example.py`: runs the instrument and analyses the result.

The tests in `../extra_pytests/` use both the instrument package and this
analysis package.
