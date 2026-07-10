"""
Shared pytest configuration for the SayonLab plotting test suite.

Sets Matplotlib to a headless backend before anything imports pyplot,
so tests run identically in CI, over SSH, or on a machine with no
display attached.
"""

import matplotlib

matplotlib.use("Agg")