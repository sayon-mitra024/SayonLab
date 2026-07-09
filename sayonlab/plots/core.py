"""
Public plotting API for SayonLab.

This is the only module in ``sayonlab.plots`` researchers interact with
directly. Every function here follows the same shape:

    validate -> plot inside a styled, memory-safe figure -> save/show -> return

using the internal machinery built in ``validation.py``, ``style.py``,
``base.py``, and ``export.py``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Literal, Optional, Sequence, Union

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes

from .base import figure_scope
from .export import save_figure
from .style import PlotStyle, PUBLICATION_STYLE, get_color
from .validation import (
    ArrayLike,
    SayonLabValidationError,
    validate_confidence_bounds,
    validate_xy,
)

Kind = Literal["line", "scatter", "bar"]


# ---------------------------------------------------------------------------
# Shared helpers (used by every public function below)
# ---------------------------------------------------------------------------
def _apply_labels(
    ax: Axes,
    title: str,
    xlabel: str,
    ylabel: str,
    legend_needed: bool,
) -> None:
    """Apply title/axis labels/legend consistently across plot types."""
    if title:
        ax.set_title(title, fontweight="bold", pad=12)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    if legend_needed:
        ax.legend(loc="best", frameon=True)


def _save_and_show(
    fig,
    save_path: Optional[Union[str, Path]],
    formats: Optional[Sequence[str]],
    dpi: Optional[int],
    metadata: Optional[Dict[str, object]],
    show: bool,
) -> Optional[List[Path]]:
    """Save (if requested) and show (if requested) while the figure is still open.

    Must be called from *inside* the active ``figure_scope`` block, since
    the figure is closed on exit from that context manager.
    """
    saved: Optional[List[Path]] = None
    if save_path is not None:
        saved = save_figure(fig, save_path, formats=formats, dpi=dpi, metadata=metadata)
    if show:
        plt.show()
    return saved


def _validate_bar_data(
    categories: Sequence,
    values: ArrayLike,
) -> np.ndarray:
    """Validate a (categories, values) pair for :func:`bar`.

    Kept local to this file rather than added to ``validation.py``
    because it's specific to bar charts (categorical x-axis), not a
    cross-cutting concern shared by other plot types yet.
    """
    if len(categories) != len(values):
        raise SayonLabValidationError(
            f"'categories' and 'values' must have the same length. "
            f"Got len(categories)={len(categories)} and len(values)={len(values)}."
        )
    if len(categories) == 0:
        raise SayonLabValidationError("'categories' is empty. Provide at least one bar.")
    # Reuse validate_xy's numeric/NaN checks on `values` via a positional
    # index as the paired "x", since categories themselves aren't numeric.
    _, values_arr = validate_xy(
        list(range(len(values))), values, x_name="index", y_name="values"
    )
    return values_arr


def _validate_error_bars(error: Optional[ArrayLike], length: int) -> Optional[np.ndarray]:
    """Validate optional +/- error-bar magnitudes for :func:`bar`."""
    if error is None:
        return None
    arr = np.asarray(error, dtype=np.float64)
    if arr.ndim != 1 or arr.shape[0] != length:
        raise SayonLabValidationError(
            f"'error' must be a 1-D sequence of length {length} matching "
            f"'values'. Got shape {arr.shape}."
        )
    if np.any(arr < 0):
        raise SayonLabValidationError(
            "'error' values must be non-negative — they represent +/- "
            "magnitude around each bar, not absolute bounds."
        )
    return arr


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def line(
    x: ArrayLike,
    y: ArrayLike,
    *,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    label: Optional[str] = None,
    ci_lower: Optional[ArrayLike] = None,
    ci_upper: Optional[ArrayLike] = None,
    color: Optional[str] = None,
    style: PlotStyle = PUBLICATION_STYLE,
    figsize: tuple = (8.0, 5.0),
    save_path: Optional[Union[str, Path]] = None,
    formats: Optional[Sequence[str]] = None,
    dpi: Optional[int] = None,
    metadata: Optional[Dict[str, object]] = None,
    show: bool = False,
) -> Optional[List[Path]]:
    """Generate a publication-ready line plot, with optional confidence band.

    Parameters
    ----------
    x, y : array-like
        Data to plot. Must be equal length, numeric, and not entirely NaN.
    title, xlabel, ylabel : str, optional
        Text labels. Omitted labels are simply not drawn.
    label : str, optional
        Legend label for this line. If omitted and no confidence
        interval is given, no legend is drawn.
    ci_lower, ci_upper : array-like, optional
        Confidence band bounds, same length as ``x``. Must be given
        together or not at all.
    color : str, optional
        Line/band color. Defaults to the first color in ``style``'s palette.
    style : PlotStyle, optional
        Visual style. Defaults to :data:`sayonlab.plots.style.PUBLICATION_STYLE`.
    figsize : tuple of float, optional
        Figure size in inches. Default ``(8, 5)``.
    save_path : str or Path, optional
        If given, the figure is saved here. Parent directories are
        created automatically.
    formats : sequence of str, optional
        Export formats (``"png"``, ``"pdf"``, ``"svg"``). Inferred from
        ``save_path``'s extension if omitted.
    dpi : int, optional
        Export resolution. Defaults to ``style.dpi``.
    metadata : dict, optional
        Extra metadata to embed in the saved file(s).
    show : bool, default False
        Whether to display the figure interactively. Kept ``False`` by
        default so this function is safe to call in headless/batch
        pipelines without blocking.

    Returns
    -------
    list of Path, or None
        Paths written, if ``save_path`` was given; otherwise ``None``.

    Raises
    ------
    sayonlab.plots.validation.SayonLabValidationError
        If ``x``/``y``/confidence bounds fail validation.

    Examples
    --------
    >>> line([1, 2, 3], [1, 4, 9], title="Growth", save_path="growth.png")
    """
    x_arr, y_arr = validate_xy(x, y)
    ci_lo, ci_hi = validate_confidence_bounds(x_arr, ci_lower, ci_upper)

    with figure_scope(style=style, figsize=figsize) as (fig, ax):
        line_color = color or get_color(style, 0)
        ax.plot(x_arr, y_arr, label=label, color=line_color, linewidth=2)

        if ci_lo is not None:
            band_label = "Confidence interval" if label is None else None
            ax.fill_between(x_arr, ci_lo, ci_hi, color=line_color, alpha=0.2, label=band_label)

        _apply_labels(
            ax, title, xlabel, ylabel,
            legend_needed=bool(label) or ci_lo is not None,
        )
        saved = _save_and_show(fig, save_path, formats, dpi, metadata, show)

    return saved


def scatter(
    x: ArrayLike,
    y: ArrayLike,
    *,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    label: Optional[str] = None,
    color: Optional[str] = None,
    size: float = 30.0,
    alpha: float = 0.8,
    style: PlotStyle = PUBLICATION_STYLE,
    figsize: tuple = (8.0, 5.0),
    save_path: Optional[Union[str, Path]] = None,
    formats: Optional[Sequence[str]] = None,
    dpi: Optional[int] = None,
    metadata: Optional[Dict[str, object]] = None,
    show: bool = False,
) -> Optional[List[Path]]:
    """Generate a publication-ready scatter plot.

    Parameters
    ----------
    x, y : array-like
        Data to plot. Must be equal length, numeric, and not entirely NaN.
    title, xlabel, ylabel : str, optional
        Text labels. Omitted labels are simply not drawn.
    label : str, optional
        Legend label for this series. If omitted, no legend is drawn.
    color : str, optional
        Marker color. Defaults to the first color in ``style``'s palette.
    size : float, default 30.0
        Marker area (Matplotlib's ``s`` parameter).
    alpha : float, default 0.8
        Marker transparency, 0 (invisible) to 1 (opaque).
    style, figsize, save_path, formats, dpi, metadata, show
        See :func:`line` for these shared parameters.

    Returns
    -------
    list of Path, or None
        Paths written, if ``save_path`` was given; otherwise ``None``.

    Raises
    ------
    sayonlab.plots.validation.SayonLabValidationError
        If ``x``/``y`` fail validation.

    Examples
    --------
    >>> scatter([1, 2, 3], [3, 1, 2], title="Measurements")
    """
    x_arr, y_arr = validate_xy(x, y)

    with figure_scope(style=style, figsize=figsize) as (fig, ax):
        point_color = color or get_color(style, 0)
        ax.scatter(
            x_arr, y_arr, label=label, color=point_color,
            s=size, alpha=alpha, edgecolors="white", linewidths=0.5,
        )
        _apply_labels(ax, title, xlabel, ylabel, legend_needed=bool(label))
        saved = _save_and_show(fig, save_path, formats, dpi, metadata, show)

    return saved


def bar(
    categories: Sequence,
    values: ArrayLike,
    *,
    error: Optional[ArrayLike] = None,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    color: Optional[str] = None,
    style: PlotStyle = PUBLICATION_STYLE,
    figsize: tuple = (8.0, 5.0),
    save_path: Optional[Union[str, Path]] = None,
    formats: Optional[Sequence[str]] = None,
    dpi: Optional[int] = None,
    metadata: Optional[Dict[str, object]] = None,
    show: bool = False,
) -> Optional[List[Path]]:
    """Generate a publication-ready bar chart, with optional error bars.

    Parameters
    ----------
    categories : sequence
        Category labels, one per bar (need not be numeric).
    values : array-like
        Bar heights, same length as ``categories``.
    error : array-like, optional
        Symmetric +/- error magnitude per bar (e.g. standard error).
        Must be non-negative and the same length as ``values``.
    title, xlabel, ylabel : str, optional
        Text labels. Omitted labels are simply not drawn.
    color : str, optional
        Bar color. Defaults to the first color in ``style``'s palette.
    style, figsize, save_path, formats, dpi, metadata, show
        See :func:`line` for these shared parameters.

    Returns
    -------
    list of Path, or None
        Paths written, if ``save_path`` was given; otherwise ``None``.

    Raises
    ------
    sayonlab.plots.validation.SayonLabValidationError
        If ``categories``/``values``/``error`` fail validation.

    Examples
    --------
    >>> bar(["Control", "Treatment"], [12.5, 18.2], error=[1.1, 0.9])
    """
    values_arr = _validate_bar_data(categories, values)
    error_arr = _validate_error_bars(error, len(values_arr))

    with figure_scope(style=style, figsize=figsize) as (fig, ax):
        bar_color = color or get_color(style, 0)
        x_pos = np.arange(len(categories))

        ax.bar(
            x_pos, values_arr, yerr=error_arr, color=bar_color,
            capsize=4 if error_arr is not None else 0,
            edgecolor="white", linewidth=0.5,
        )
        ax.set_xticks(x_pos)
        long_labels = any(len(str(c)) > 8 for c in categories)
        ax.set_xticklabels(
            categories,
            rotation=30 if long_labels else 0,
            ha="right" if long_labels else "center",
        )
        _apply_labels(ax, title, xlabel, ylabel, legend_needed=False)
        saved = _save_and_show(fig, save_path, formats, dpi, metadata, show)

    return saved


# ---------------------------------------------------------------------------
# auto() — infers a plot kind from the data, or dispatches an explicit kind
# ---------------------------------------------------------------------------
_DISPATCH = {"line": line, "scatter": scatter, "bar": bar}


def _infer_kind(x: ArrayLike) -> Kind:
    """Infer a plot kind from ``x`` using a simple, documented heuristic.

    Rules (checked in order)
    -------------------------
    1. ``x`` is not numeric (e.g. strings) -> ``"bar"``.
    2. ``x`` is numeric and strictly increasing -> ``"line"``.
    3. ``x`` is numeric but not monotonic -> ``"scatter"``.

    This is intentionally simple for v0.1 rather than a black-box
    guess — a researcher can always override it with ``kind=``.

    Raises
    ------
    SayonLabValidationError
        If there are too few points to infer confidently.
    """
    try:
        numeric = np.asarray(x, dtype=np.float64)
        is_numeric = numeric.ndim == 1
    except (TypeError, ValueError):
        is_numeric = False

    if not is_numeric:
        return "bar"

    if numeric.size < 2:
        raise SayonLabValidationError(
            "sl.plot.auto() could not infer a plot kind from fewer than 2 "
            "numeric x-values. Pass kind='line', 'scatter', or 'bar' explicitly."
        )

    is_strictly_increasing = bool(np.all(np.diff(numeric) > 0))
    return "line" if is_strictly_increasing else "scatter"


def auto(
    x: ArrayLike,
    y: ArrayLike,
    *,
    kind: Optional[Kind] = None,
    **kwargs,
) -> Optional[List[Path]]:
    """Plot ``x``/``y`` using an automatically inferred or explicit kind.

    Parameters
    ----------
    x, y : array-like
        Data to plot.
    kind : {"line", "scatter", "bar"}, optional
        Force a specific plot type, bypassing inference. Use this
        whenever you know what you want or the automatic guess isn't
        right for your data.
    **kwargs
        Forwarded to the underlying plot function (:func:`line`,
        :func:`scatter`, or :func:`bar`) — e.g. ``title=``, ``save_path=``.

    Returns
    -------
    list of Path, or None
        Paths written, if ``save_path`` was given; otherwise ``None``.

    Raises
    ------
    sayonlab.plots.validation.SayonLabValidationError
        If ``kind`` is invalid, or the data doesn't provide enough
        information to infer a kind confidently.

    See Also
    --------
    sayonlab.plots.core._infer_kind : the inference heuristic used.

    Examples
    --------
    >>> auto([1, 2, 3], [1, 4, 9])                  # -> line (increasing x)
    >>> auto([3, 1, 2], [5, 2, 8])                  # -> scatter (non-monotonic x)
    >>> auto(["A", "B", "C"], [4, 7, 2])            # -> bar (non-numeric x)
    >>> auto([1, 2, 3], [1, 4, 9], kind="scatter")  # explicit override
    """
    if kind is not None:
        if kind not in _DISPATCH:
            raise SayonLabValidationError(
                f"Unknown kind={kind!r}. Supported: {sorted(_DISPATCH)}."
            )
        return _DISPATCH[kind](x, y, **kwargs)

    inferred = _infer_kind(x)
    return _DISPATCH[inferred](x, y, **kwargs)