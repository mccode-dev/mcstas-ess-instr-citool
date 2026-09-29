"""Dimensions of the ExPyHelpers beamline (all lengths in meters)."""

# Source:
SOURCE_RADIUS = 0.02

# Distance from source to guide entrance:
SOURCE_TO_GUIDE = 2.0

# Guide cross section:
GUIDE_WIDTH = 0.03
GUIDE_HEIGHT = 0.05

# Distance from guide exit to the sample position:
GUIDE_TO_SAMPLE = 0.5


def sample_distance(guide_length):
    """Distance from the guide entrance to the sample position."""
    return guide_length + GUIDE_TO_SAMPLE
