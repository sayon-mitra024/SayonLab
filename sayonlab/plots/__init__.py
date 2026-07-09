"""
sayonlab.plots
===============
Publication-ready scientific plotting with minimal code.

Quick start
-----------
>>> import sayonlab as sl
>>> sl.plot.line([1, 2, 3], [1, 4, 9], title="Growth", save_path="fig.png")
>>> sl.plot.auto(categories, values)  # infers line/scatter/bar automatically

Public API
----------
- ``line``, ``scatter``, ``bar`` — explicit plot types.
- ``auto`` — infers a plot type from the data, or dispatches an explicit ``kind=``.
- ``PlotStyle`` / ``PUBLICATION_STYLE`` — customize or reuse the default visual style.
- ``SayonLabValidationError`` / ``SayonLabExportError`` — catch these for
  SayonLab-specific input/export failures distinct from generic Python errors.

Everything else in this subpackage (``base``, the internals of ``style``,
``validation``, ``export``) is implementation detail and not part of the
public API — it may change between minor versions without notice.
"""

from .core import auto, bar, line, scatter
from .export import SayonLabExportError
from .style import PlotStyle, PUBLICATION_STYLE
from .validation import SayonLabValidationError

__all__ = [
    "line",
    "scatter",
    "bar",
    "auto",
    "PlotStyle",
    "PUBLICATION_STYLE",
    "SayonLabValidationError",
    "SayonLabExportError",
]