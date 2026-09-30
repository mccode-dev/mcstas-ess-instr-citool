"""Analysis of the wavelength spectrum recorded by the ExPyExtra instrument."""

import numpy as np


def mean_wavelength(data):
    """Intensity-weighted mean wavelength [AA] of 1D McStasScript monitor
    data (e.g. from an L_monitor)."""
    wavelengths = np.asarray(data.xaxis, dtype=float)
    intensity = np.asarray(data.Intensity, dtype=float)
    return float(np.sum(wavelengths * intensity) / np.sum(intensity))
