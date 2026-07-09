"""
Internal plotting engine for the SayonLab plotting subsystem.

This module is not part of the public API. Researchers never construct
or interact with anything defined here directly — ``core.py`` uses these
primitives internally to create, style, and safely dispose of figures.

Keeping this separate from ``core.py`` means the smart-figure-creation,
auto-layout, and memory-safety logic is written and tested once, and
every current and future public plot function (line, scatter, bar,
statistical, ml, image, ...) gets it for free by using ``figure_scope``.
"""

from __future__ import annotations

import warnings
from contextlib import contextmanager
from typing import Iterator, Tuple

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from .style import PlotStyle, PUBLICATION_STYLE, styled_context


def apply_auto_layout(fig: Figure) -> None:
    """Apply the best available automatic layout to a figure.

    Tries ``constrained_layout`` first, since it generally handles
    multi-axes figures, legends, and colorbars better than
    ``tight_layout``. Falls back to ``tight_layout`` if constrained
    layout is unavailable for this figure. A layout failure never
    raises — it degrades gracefully with a warning, since a slightly
    imperfect layout is far less disruptive to a researcher's workflow
    than an exception in the middle of figure generation.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The figure to lay out. Modified in place.

    Examples
    --------
    >>> fig, ax = plt.subplots()
    >>> apply_auto_layout(fig)
    """
    try:
        fig.set_layout_engine("constrained")
    except (ValueError, AttributeError):
        try:
            fig.tight_layout()
        except Exception as exc:  # noqa: BLE001 - layout must never crash a plot
            warnings.warn(
                f"SayonLab could not auto-optimize this figure's layout "
                f"({exc}). The figure will still be created, but you may "
                f"want to adjust spacing manually.",
                stacklevel=2,
            )


def close_figure(fig: Figure) -> None:
    """Close a figure safely, tolerating an already-closed figure.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The figure to close.

    Notes
    -----
    Matplotlib does not raise if you close an already-closed figure, but
    this wrapper exists as a single, explicit place to close figures so
    future cleanup logic (e.g. logging, figure-count tracking for tests)
    has one call site to hook into.
    """
    plt.close(fig)


@contextmanager
def figure_scope(
    style: PlotStyle = PUBLICATION_STYLE,
    figsize: Tuple[float, float] = (8.0, 5.0),
) -> Iterator[Tuple[Figure, Axes]]:
    """Create a styled figure/axes pair with guaranteed cleanup.

    This is the primary internal entry point every public plot function
    should use. It combines three concerns so callers in ``core.py``
    don't have to coordinate them manually:

    1. Applies ``style`` for the entire lifetime of the block (not just
       creation) — required because Matplotlib bakes in font/text
       properties at creation time, not at render time.
    2. Applies automatic layout optimization just before the figure is
       handed back to the caller for saving/showing.
    3. Guarantees the figure is closed on exit, even if an exception is
       raised while building the plot — preventing the "hundreds of
       open figures" memory issue common in notebook/batch loops.

    Parameters
    ----------
    style : PlotStyle, optional
        Style to apply for the duration of this figure. Defaults to
        :data:`sayonlab.plots.style.PUBLICATION_STYLE`.
    figsize : tuple of float, optional
        Figure size in inches as ``(width, height)``. Default ``(8, 5)``.

    Yields
    ------
    tuple of (matplotlib.figure.Figure, matplotlib.axes.Axes)
        The created figure and its primary axes, ready to be drawn on.

    Raises
    ------
    Exception
        Re-raises any exception from the caller's plotting code after
        ensuring the figure is closed — cleanup never swallows errors.

    Notes
    -----
    The figure is closed on exit from this context manager. If the
    caller needs the figure to remain open past the ``with`` block (for
    example, to call ``plt.show()`` interactively), that must happen
    *inside* the block, before exit.

    Examples
    --------
    >>> with figure_scope(figsize=(6, 4)) as (fig, ax):
    ...     ax.plot([1, 2, 3], [1, 4, 9])
    ...     ax.set_title("Example")
    ...     fig.savefig("example.png")
    """
    with styled_context(style):
        fig, ax = plt.subplots(figsize=figsize)
        try:
            yield fig, ax
            apply_auto_layout(fig)
        finally:
            close_figure(fig)