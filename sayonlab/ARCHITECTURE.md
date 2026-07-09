# SayonLab — `plots/` Architecture

Scope: this document explains **only the `sayonlab/plots/` folder** — what
each file does, why it exists, and how they depend on each other. It is a
map for future-you (or any AI assisting future-you) so nobody has to
re-read every file to remember the design.

---

## Purpose of this folder

`plots/` is the plotting subsystem of SayonLab. Its job is to let a
researcher write one line of code (`sl.plot.line(...)`) and get a
publication-ready figure — styled, validated, auto-laid-out, exported to
PNG/PDF/SVG, and memory-safe — instead of hand-writing Matplotlib
boilerplate every time.

**Design principle:** organize by *responsibility*, not by *chart type*.
There is no `line_chart.py` + `bar_chart.py` + `scatter_chart.py`. Instead,
cross-cutting concerns (validation, styling, figure lifecycle, export)
each get one file, and all chart types share them.

---

## File-by-file

### `validation.py` — *is the data safe to plot?*
- **Purpose:** the single place every plot function checks its inputs, so
  every function gives the same quality of error message instead of a
  raw Matplotlib traceback.
- **Public-ish exports:** `SayonLabValidationError`, `validate_xy`,
  `validate_confidence_bounds`, `validate_positive_int`.
- **Knows nothing about:** what kind of plot is being made. Pure input
  checking.
- **Used by:** `core.py`, `export.py` (DPI check).

### `style.py` — *what should the figure look like?*
- **Purpose:** publication styling (fonts, DPI, grid, colorblind-safe
  Okabe-Ito palette), applied **per figure** via a scoped
  `matplotlib.rc_context()` — never a global `rcParams.update()`. This
  means importing SayonLab never silently changes a researcher's other,
  unrelated Matplotlib figures.
- **Public exports:** `PlotStyle` (frozen dataclass), `PUBLICATION_STYLE`
  (default instance), `styled_context()`, `get_color()`.
- **Used by:** `base.py` (applies the style), `core.py` (lets users pass
  a custom style).

### `base.py` — *figure lifecycle: create, layout, close safely*
- **Purpose:** internal plotting engine. Nobody outside this folder
  should ever import from here directly.
- **Key export:** `figure_scope(style, figsize)` — a context manager
  that creates a styled figure/axes pair and **guarantees** the figure
  is closed on exit, even if the plotting code inside raises an
  exception. This is what prevents the "hundreds of open figures crash
  a notebook loop" problem.
- **Important constraint:** because Matplotlib bakes in font/text
  properties at *creation* time (not render time), everything that
  builds a plot — title, labels, legend — must happen **inside** the
  `with figure_scope(...) as (fig, ax):` block, not after it.
- **Also exports:** `apply_auto_layout()`, `close_figure()`.
- **Used by:** `core.py`.

### `export.py` — *saving a figure to disk correctly*
- **Purpose:** one save function that: auto-creates missing directories,
  supports multiple export formats in one call, and embeds provenance
  metadata (creator, creation date) — adapted correctly per format,
  since PNG/PDF/SVG each expect different metadata keys and types (e.g.
  PDF requires `CreationDate` as an actual `datetime` object; SVG
  rejects that key name and wants `Date` as a string instead).
- **Key export:** `save_figure(fig, path, formats=, dpi=, metadata=)`.
- **Also exports:** `SayonLabExportError`, `SUPPORTED_FORMATS` (currently
  `("png", "pdf", "svg")` — extending this list later is non-breaking).
- **Used by:** `core.py`.

### `core.py` — *the actual public API*
- **Purpose:** this is what a researcher calls. Every function follows
  the same shape: **validate → plot inside `figure_scope` → save/show →
  return.**
- **Public functions:**
  - `line(x, y, ..., ci_lower=, ci_upper=, ...)` — line plot with
    optional confidence band.
  - `scatter(x, y, ...)` — scatter plot.
  - `bar(categories, values, ..., error=, ...)` — bar chart with
    optional symmetric error bars.
  - `auto(x, y, kind=None, ...)` — infers `line`/`scatter`/`bar` from the
    data (non-numeric x → bar; increasing numeric x → line; non-monotonic
    numeric x → scatter), or dispatches an explicit `kind=`.
- **Returns:** `list[Path] | None` — saved file paths if `save_path` was
  given, else `None`.
- **Local-only validation:** `_validate_bar_data()` and
  `_validate_error_bars()` live here, not in `validation.py`, because
  they're specific to bar charts, not a cross-cutting concern (yet).

### `__init__.py` — *what's actually public*
- **Purpose:** the only file that decides what `sl.plot.<name>` exposes.
  Everything internal (`figure_scope`, `get_color`,
  `_metadata_for_format`, etc.) is deliberately **not** re-exported here.
- **Exposes:** `line`, `scatter`, `bar`, `auto`, `PlotStyle`,
  `PUBLICATION_STYLE`, `SayonLabValidationError`, `SayonLabExportError`.

---

## Dependency chain

```
validation.py  (no internal deps)
     ↓
style.py       (no internal deps)
     ↓
base.py        (depends on: style.py)
     ↓
export.py      (depends on: validation.py)
     ↓
core.py        (depends on: validation.py, style.py, base.py, export.py)
     ↓
__init__.py    (re-exports selected names from core.py, style.py,
                 validation.py, export.py)
```

Each layer only depends on layers above it. Nothing lower ever imports
from `core.py` or `__init__.py` — that would create a circular
dependency.

---

## Adding a new chart type later (e.g. `histogram`, `boxplot`)

1. If it fits an existing file's scope, add it to `core.py`.
2. If a *new category* of plots emerges (statistical, ML evaluation,
   image/medical), create a new file (`statistical.py`, `ml.py`,
   `image.py`) — but only when there's a real function to put in it, not
   as an empty placeholder.
3. New chart-type files should still route through `validation.py`,
   `style.py`, and `base.py.figure_scope()` — never duplicate that logic.
4. Update this document's "File-by-file" section and the dependency
   diagram when a new file is added.

---

## What NOT to do here

- Don't call `plt.rcParams.update()` anywhere — always go through
  `styled_context()`.
- Don't create a figure without `figure_scope()` — you lose the
  guaranteed-cleanup behavior.
- Don't add a new file "because it sounds impressive" — every file here
  exists because at least one real function needed it.

*Last updated: alongside `core.py` and `__init__.py` (v0.1.0).*
