"""
Figure export for the SayonLab plotting subsystem.

Every public plot function in ``core.py`` that accepts a ``save_path``
routes through :func:`save_figure` here, so directory creation, DPI
handling, multi-format export, and metadata embedding are implemented
and tested exactly once.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Sequence, Union

from matplotlib.figure import Figure

from .validation import validate_positive_int

#: Formats supported in v0.1. Extending this tuple later (e.g. adding
#: "eps", "tiff") is a non-breaking change — no need to redesign this
#: module for that, so we don't build for it prematurely.
SUPPORTED_FORMATS: tuple[str, ...] = ("png", "pdf", "svg")


class SayonLabExportError(ValueError):
    """Raised when a figure cannot be exported as requested.

    Subclasses ``ValueError`` for consistency with
    :class:`~sayonlab.plots.validation.SayonLabValidationError`.
    """


#: Metadata keys accepted by Matplotlib's PDF backend. Passing an
#: unrecognized key raises there, so we filter down to this set.
_PDF_METADATA_KEYS = {
    "Title", "Author", "Subject", "Keywords", "Creator", "Producer", "CreationDate",
}
#: Metadata keys accepted by Matplotlib's SVG backend. Note it uses
#: "Date", not "CreationDate" — handled by the rename in
#: :func:`_metadata_for_format`.
_SVG_METADATA_KEYS = {
    "Title", "Author", "Description", "Copyright", "Date", "Format", "Creator",
}


def _default_metadata() -> Dict[str, object]:
    """Build the baseline provenance metadata embedded in every export.

    ``CreationDate`` is kept as a real ``datetime`` object here (not a
    string) because Matplotlib's PDF backend requires that exact type;
    :func:`_metadata_for_format` converts it to a string for PNG/SVG,
    which expect text.
    """
    try:
        from importlib.metadata import PackageNotFoundError, version

        try:
            pkg_version = version("sayonlab")
        except PackageNotFoundError:
            pkg_version = "0.1.0"
    except ImportError:  # pragma: no cover - importlib.metadata always present on 3.8+
        pkg_version = "0.1.0"

    return {
        "Creator": f"SayonLab {pkg_version}",
        "CreationDate": datetime.now(),
    }


def _metadata_for_format(fmt: str, metadata: Dict[str, object]) -> Dict[str, str]:
    """Adapt generic metadata into the schema a specific backend accepts.

    PNG (via Pillow) accepts arbitrary string keys/values. PDF requires
    ``CreationDate`` to be a ``datetime`` object and only recognizes a
    fixed key set. SVG has its own fixed key set and calls the same
    concept ``Date`` instead of ``CreationDate``. This function is what
    lets a researcher pass one metadata dict to :func:`save_figure` and
    have it "just work" across all three formats, instead of needing to
    know each backend's quirks.

    Parameters
    ----------
    fmt : str
        One of ``"png"``, ``"pdf"``, ``"svg"``.
    metadata : dict
        Generic metadata, as produced by merging
        :func:`_default_metadata` with any user-supplied metadata.

    Returns
    -------
    dict
        A metadata dict safe to pass to that format's ``savefig(metadata=...)``.
    """
    if fmt == "png":
        return {
            k: (v.isoformat() if isinstance(v, datetime) else str(v))
            for k, v in metadata.items()
        }

    if fmt == "pdf":
        out: Dict[str, object] = {}
        for k, v in metadata.items():
            if k == "CreationDate":
                out[k] = v if isinstance(v, datetime) else datetime.now()
            elif k in _PDF_METADATA_KEYS:
                out[k] = str(v)
        return out

    if fmt == "svg":
        out = {}
        for k, v in metadata.items():
            key = "Date" if k == "CreationDate" else k
            if key in _SVG_METADATA_KEYS:
                out[key] = v.isoformat() if isinstance(v, datetime) else str(v)
        return out

    return {}  # pragma: no cover - unreachable, formats validated earlier


def _resolve_targets(
    path: Union[str, Path],
    formats: Optional[Sequence[str]],
) -> tuple[Path, tuple[str, ...]]:
    """Determine the output stem path and the set of formats to write.

    Parameters
    ----------
    path : str or Path
        Either a full filename with extension (``"fig.png"``) or a stem
        (``"fig"``) to be combined with ``formats``.
    formats : sequence of str, optional
        Explicit formats to export. If omitted, inferred from ``path``'s
        extension.

    Returns
    -------
    tuple of (Path, tuple of str)
        The path stem (no extension) and the validated, lowercased
        formats to write.

    Raises
    ------
    SayonLabExportError
        If no format can be determined, or an unsupported format is
        requested.
    """
    path = Path(path)

    if formats is None:
        ext = path.suffix.lstrip(".").lower()
        if not ext:
            raise SayonLabExportError(
                f"Could not determine an export format from path '{path}'. "
                f"Either give it an extension (e.g. 'fig.png') or pass "
                f"formats=[...] explicitly. Supported formats: "
                f"{SUPPORTED_FORMATS}."
            )
        resolved_formats: tuple[str, ...] = (ext,)
        stem = path.with_suffix("")
    else:
        if len(formats) == 0:
            raise SayonLabExportError(
                "'formats' was given as an empty sequence. Provide at "
                f"least one of {SUPPORTED_FORMATS}, or omit 'formats' and "
                "give 'path' an extension instead."
            )
        resolved_formats = tuple(f.lower() for f in formats)
        stem = path.with_suffix("") if path.suffix else path

    unsupported = [f for f in resolved_formats if f not in SUPPORTED_FORMATS]
    if unsupported:
        raise SayonLabExportError(
            f"Unsupported export format(s) {unsupported}. SayonLab v0.1 "
            f"supports {SUPPORTED_FORMATS}."
        )

    return stem, resolved_formats


def save_figure(
    fig: Figure,
    path: Union[str, Path],
    *,
    formats: Optional[Sequence[str]] = None,
    dpi: Optional[int] = None,
    metadata: Optional[Dict[str, object]] = None,
) -> list[Path]:
    """Save a figure to one or more formats, creating directories as needed.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The figure to save.
    path : str or Path
        A full filename with extension (e.g. ``"results/fig1.png"``), or
        a path stem (e.g. ``"results/fig1"``) when ``formats`` is given.
    formats : sequence of str, optional
        Formats to export, e.g. ``["png", "pdf"]``. If omitted, the
        single format is inferred from ``path``'s extension. Supported:
        ``"png"``, ``"pdf"``, ``"svg"``.
    dpi : int, optional
        Resolution for raster output. If omitted, the figure's own DPI
        (typically set by the active :class:`~sayonlab.plots.style.PlotStyle`)
        is used.
    metadata : dict of str to str, optional
        Additional metadata to embed (e.g. ``{"Title": "Figure 1"}``).
        Merged with SayonLab's default provenance metadata
        (creator, creation date); explicit keys here take precedence.

    Returns
    -------
    list of Path
        The paths actually written, one per requested format.

    Raises
    ------
    SayonLabExportError
        If no format can be determined, an unsupported format is
        requested, or the figure cannot be written to disk (e.g.
        permission error).

    Examples
    --------
    >>> saved = save_figure(fig, "results/fig1.png")
    >>> saved = save_figure(fig, "results/fig1", formats=["png", "pdf", "svg"])
    """
    stem, resolved_formats = _resolve_targets(path, formats)

    resolved_dpi = validate_positive_int(dpi, "dpi") if dpi is not None else None

    stem.parent.mkdir(parents=True, exist_ok=True)

    merged_metadata = {**_default_metadata(), **(metadata or {})}

    saved_paths: list[Path] = []
    for fmt in resolved_formats:
        out_path = stem.with_suffix(f".{fmt}")
        save_kwargs: Dict[str, object] = {
            "format": fmt,
            "metadata": _metadata_for_format(fmt, merged_metadata),
            "bbox_inches": "tight",
        }
        if resolved_dpi is not None:
            save_kwargs["dpi"] = resolved_dpi

        try:
            fig.savefig(out_path, **save_kwargs)
        except OSError as exc:
            raise SayonLabExportError(
                f"Failed to write figure to '{out_path}': {exc}"
            ) from exc

        saved_paths.append(out_path)

    return saved_paths