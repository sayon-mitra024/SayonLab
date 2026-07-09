"""
Publication styling for the SayonLab plotting subsystem.

Styling is applied *per figure*, scoped via ``matplotlib.rc_context()``,
never via a global ``plt.rcParams.update()`` at import time. This means
importing ``sayonlab`` does not silently change the appearance of a
researcher's own, unrelated Matplotlib figures — only figures created
through ``sayonlab.plots`` pick up SayonLab styling.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from typing import Iterator, Sequence

import matplotlib as mpl

# ---------------------------------------------------------------------------
# Colorblind-safe palette (Okabe & Ito, 2008) — the standard qualitative
# palette recommended for scientific publishing. Black is omitted from the
# default cycle (reserved for annotations/reference lines) but kept
# available for callers who want it explicitly.
# ---------------------------------------------------------------------------
OKABE_ITO_PALETTE: tuple[str, ...] = (
    "#E69F00",  # orange
    "#56B4E9",  # sky blue
    "#009E73",  # bluish green
    "#F0E442",  # yellow
    "#0072B2",  # blue
    "#D55E00",  # vermillion
    "#CC79A7",  # reddish purple
)
OKABE_ITO_BLACK: str = "#000000"


@dataclass(frozen=True)
class PlotStyle:
    """Immutable configuration for a SayonLab figure's appearance.

    Instances are frozen so a shared default (e.g. ``PUBLICATION_STYLE``)
    can never be mutated by one plot call in a way that leaks into
    another. Use :func:`dataclasses.replace` to derive a variant.

    Parameters
    ----------
    font_family : str, default "serif"
        Matches standard LaTeX/journal body fonts.
    font_size : int, default 11
        Base font size in points; other text sizes scale relative to this
        unless overridden.
    title_size : int, default 13
        Font size for axes titles.
    label_size : int, default 11
        Font size for axis labels.
    tick_size : int, default 9
        Font size for tick labels.
    legend_size : int, default 9
        Font size for legend text.
    dpi : int, default 300
        Figure resolution. 300 is the common journal minimum; use 600
        for line-art/vector-heavy figures if a venue requires it.
    grid : bool, default True
        Whether axes show a background grid.
    grid_alpha : float, default 0.4
        Grid line transparency, 0 (invisible) to 1 (opaque).
    grid_linestyle : str, default "--"
        Matplotlib linestyle string for the grid.
    palette : sequence of str, default Okabe-Ito palette
        Hex colors used as the axes color cycle.
    spines_top_right : bool, default False
        Whether to keep the top/right plot borders. Publication figures
        conventionally hide these (open-box style).

    Examples
    --------
    >>> style = PUBLICATION_STYLE
    >>> dark_variant = replace(style, grid_alpha=0.15)
    """

    font_family: str = "serif"
    font_size: int = 11
    title_size: int = 13
    label_size: int = 11
    tick_size: int = 9
    legend_size: int = 9
    dpi: int = 300
    grid: bool = True
    grid_alpha: float = 0.4
    grid_linestyle: str = "--"
    palette: Sequence[str] = field(default_factory=lambda: OKABE_ITO_PALETTE)
    spines_top_right: bool = False

    def to_rc_params(self) -> dict:
        """Translate this style into a Matplotlib rcParams-compatible dict.

        Returns
        -------
        dict
            Keys/values suitable for ``matplotlib.rc_context(rc=...)``.
        """
        return {
            "font.family": self.font_family,
            "font.size": self.font_size,
            "axes.titlesize": self.title_size,
            "axes.labelsize": self.label_size,
            "xtick.labelsize": self.tick_size,
            "ytick.labelsize": self.tick_size,
            "legend.fontsize": self.legend_size,
            "figure.dpi": self.dpi,
            "savefig.dpi": self.dpi,
            "axes.grid": self.grid,
            "grid.alpha": self.grid_alpha,
            "grid.linestyle": self.grid_linestyle,
            "axes.prop_cycle": mpl.cycler(color=list(self.palette)),
            "axes.spines.top": self.spines_top_right,
            "axes.spines.right": self.spines_top_right,
        }


#: Default style applied by every SayonLab plot function unless the
#: researcher passes a custom ``PlotStyle``.
PUBLICATION_STYLE = PlotStyle()


@contextmanager
def styled_context(style: PlotStyle = PUBLICATION_STYLE) -> Iterator[None]:
    """Temporarily apply a :class:`PlotStyle` via a scoped ``rc_context``.

    All Matplotlib calls made inside the ``with`` block use ``style``.
    Once the block exits, Matplotlib's rcParams revert to whatever they
    were before — this is what keeps SayonLab styling from leaking into
    the researcher's other, unrelated figures.

    Parameters
    ----------
    style : PlotStyle, optional
        The style to apply. Defaults to :data:`PUBLICATION_STYLE`.

    Yields
    ------
    None

    Examples
    --------
    >>> with styled_context(PUBLICATION_STYLE):
    ...     fig, ax = plt.subplots()
    ...     ax.plot([1, 2, 3], [1, 4, 9])
    """
    with mpl.rc_context(rc=style.to_rc_params()):
        yield


def get_color(style: PlotStyle, index: int) -> str:
    """Return the color at ``index`` in ``style``'s palette, cycling if needed.

    Centralizes color-cycling logic so every multi-series plot function
    (current and future) picks colors the same way instead of each
    re-implementing ``palette[index % len(palette)]``.

    Parameters
    ----------
    style : PlotStyle
        The style whose palette to draw from.
    index : int
        Zero-based series index (e.g. the second line plotted uses
        ``index=1``).

    Returns
    -------
    str
        A hex color string.

    Examples
    --------
    >>> get_color(PUBLICATION_STYLE, 0)
    '#E69F00'
    >>> get_color(PUBLICATION_STYLE, 7)  # wraps around
    '#E69F00'
    """
    palette = style.palette
    return palette[index % len(palette)]