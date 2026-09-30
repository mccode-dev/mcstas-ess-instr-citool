"""Run the ExPyExtra instrument and print the mean wavelength at the monitor.

Usage (with ExPyExtra_instr and expyextra_analysis available, e.g. after
"pip install -e instrpy -e extra" from the project directory):

    python extra/run_example.py
"""

import mcstasscript as ms

from ExPyExtra_instr.ExPyExtra_main import make
from expyextra_analysis.spectrum import mean_wavelength

instr = make()
instr.settings(ncount=1e5, output_path="run_example_data")
data = instr.backengine()
monitor = ms.name_search("lambda_monitor", data)
print(f"Mean wavelength at the monitor: {mean_wavelength(monitor):.3f} AA")
