"""
Every public function in ``sayonlab.plots`` (line, scatter, bar, auto, and
future statistical/ml/image plots) routes its inputs through this module
before touching Matplotlib. Centralizing validation here guarantees a
consistent, informative error message for every plot function instead of
duplicated checks or a raw Matplotlib traceback reaching the researcher.

This module has no knowledge of *which* plot is being made — only whether
the data handed to it is well-formed. Plot-specific logic belongs in
``core.py``.
"""

from __future__ import annotations

from typing import Optional, Sequence, Union

import numpy as np

ArrayLike = Union[Sequence[float], np.ndarray]


class SayonLabValidationError(ValueError):
    """Raised when data passed to a SayonLab plotting function is invalid.

    Subclasses ``ValueError`` so existing ``except ValueError`` handlers
    still work, while allowing callers/tests to catch SayonLab-specific
    validation failures distinctly from generic Python errors.
    """


def _coerce_array(data: ArrayLike, name: str) -> np.ndarray:
    """Convert array-like input to a 1-D ``float64`` NumPy array.

    Parameters
    ----------
    data : array-like
        Input data — list, tuple, NumPy array, or pandas Series.
    name : str
        The parameter name as the caller knows it (e.g. ``"x"``), used
        to build informative error messages.

    Returns
    -------
    numpy.ndarray
        A 1-D array of dtype ``float64``.

    Raises
    ------
    SayonLabValidationError
        If ``data`` cannot be converted to a numeric 1-D array.
    """
    try:
        arr = np.asarray(data, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise SayonLabValidationError(
            f"'{name}' must be array-like and numeric (list, tuple, NumPy "
            f"array, or pandas Series). Got type {type(data).__name__!r} "
            f"which could not be converted: {exc}"
        ) from exc

    if arr.ndim == 0:
        raise SayonLabValidationError(
            f"'{name}' must be a 1-D sequence of values, got a single "
            f"scalar ({data!r})."
        )
    if arr.ndim > 1:
        raise SayonLabValidationError(
            f"'{name}' must be 1-D, got an array with shape {arr.shape}. "
            f"If you're passing a DataFrame column, use df['col'].values "
            f"or select a single column."
        )
    return arr


def _check_non_empty(arr: np.ndarray, name: str) -> None:
    """Raise if ``arr`` has zero elements."""
    if arr.size == 0:
        raise SayonLabValidationError(
            f"'{name}' is empty. Provide at least one data point."
        )


def _check_not_all_nan(arr: np.ndarray, name: str) -> None:
    """Raise if every value in ``arr`` is NaN (nothing plottable)."""
    if np.all(np.isnan(arr)):
        raise SayonLabValidationError(
            f"'{name}' contains only NaN values — there is nothing to plot."
        )


def validate_xy(
    x: ArrayLike,
    y: ArrayLike,
    *,
    x_name: str = "x",
    y_name: str = "y",
) -> tuple[np.ndarray, np.ndarray]:
    """Validate and coerce an ``(x, y)`` pair for plotting.

    Checks performed
    -----------------
    - Both inputs convert cleanly to 1-D numeric arrays.
    - Neither is empty.
    - Lengths match.
    - Neither is entirely NaN.

    Parameters
    ----------
    x : array-like
        Values for the x-axis.
    y : array-like
        Values for the y-axis.
    x_name, y_name : str, optional
        Names used in error messages, useful when wrapping this function
        for parameters that aren't literally called ``x``/``y``.

    Returns
    -------
    tuple of numpy.ndarray
        ``(x_arr, y_arr)``, both validated ``float64`` 1-D arrays.

    Raises
    ------
    SayonLabValidationError
        If any of the checks above fail. The message states exactly
        which check failed and what the researcher should do about it.

    Examples
    --------
    >>> x_arr, y_arr = validate_xy([1, 2, 3], [4, 5, 6])
    >>> x_arr
    array([1., 2., 3.])
    """
    x_arr = _coerce_array(x, x_name)
    y_arr = _coerce_array(y, y_name)

    _check_non_empty(x_arr, x_name)
    _check_non_empty(y_arr, y_name)

    if x_arr.shape[0] != y_arr.shape[0]:
        raise SayonLabValidationError(
            f"'{x_name}' and '{y_name}' must have the same length. "
            f"Got len({x_name})={x_arr.shape[0]} and "
            f"len({y_name})={y_arr.shape[0]}."
        )

    _check_not_all_nan(x_arr, x_name)
    _check_not_all_nan(y_arr, y_name)

    return x_arr, y_arr


def validate_confidence_bounds(
    x: np.ndarray,
    ci_lower: Optional[ArrayLike],
    ci_upper: Optional[ArrayLike],
) -> tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """Validate optional confidence-interval bounds against an x-axis.

    Either both ``ci_lower`` and ``ci_upper`` must be provided, or
    neither. This prevents a silently one-sided or missing confidence
    band, which is easy to do by accident and hard to notice visually.

    Parameters
    ----------
    x : numpy.ndarray
        The already-validated x-axis array the bounds must align with.
    ci_lower : array-like, optional
        Lower confidence bound for each point in ``x``.
    ci_upper : array-like, optional
        Upper confidence bound for each point in ``x``.

    Returns
    -------
    tuple of (numpy.ndarray or None, numpy.ndarray or None)
        Validated bounds, or ``(None, None)`` if neither was supplied.

    Raises
    ------
    SayonLabValidationError
        If exactly one of ``ci_lower``/``ci_upper`` is given, if their
        lengths don't match ``x``, or if any lower bound exceeds its
        corresponding upper bound.
    """
    if ci_lower is None and ci_upper is None:
        return None, None

    if (ci_lower is None) != (ci_upper is None):
        raise SayonLabValidationError(
            "'ci_lower' and 'ci_upper' must be provided together. "
            "Got only one of the two — pass both, or neither."
        )

    lower_arr = _coerce_array(ci_lower, "ci_lower")
    upper_arr = _coerce_array(ci_upper, "ci_upper")

    if lower_arr.shape[0] != x.shape[0] or upper_arr.shape[0] != x.shape[0]:
        raise SayonLabValidationError(
            f"'ci_lower' and 'ci_upper' must have the same length as 'x' "
            f"({x.shape[0]}). Got len(ci_lower)={lower_arr.shape[0]}, "
            f"len(ci_upper)={upper_arr.shape[0]}."
        )

    if np.any(lower_arr > upper_arr):
        bad_idx = int(np.argmax(lower_arr > upper_arr))
        raise SayonLabValidationError(
            f"'ci_lower' must not exceed 'ci_upper' at any point. "
            f"At index {bad_idx}: ci_lower={lower_arr[bad_idx]} > "
            f"ci_upper={upper_arr[bad_idx]}."
        )

    return lower_arr, upper_arr


def validate_positive_int(value: int, name: str) -> int:
    """Validate that ``value`` is a positive integer (e.g. DPI, figure counts).

    Parameters
    ----------
    value : int
        The value to check.
    name : str
        Parameter name, used in the error message.

    Returns
    -------
    int
        ``value``, unchanged, if valid.

    Raises
    ------
    SayonLabValidationError
        If ``value`` is not an integer or is not positive.
    """
    if not isinstance(value, (int, np.integer)) or isinstance(value, bool):
        raise SayonLabValidationError(
            f"'{name}' must be an integer, got {type(value).__name__} ({value!r})."
        )
    if value <= 0:
        raise SayonLabValidationError(f"'{name}' must be positive, got {value}.")
    return int(value)