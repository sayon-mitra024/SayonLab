# Changelog

All notable changes to SayonLab are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/) —
while it's pre-1.0, minor version bumps (`0.x.0`) may include breaking
changes as the API stabilizes.

## [Unreleased]

Nothing yet.

## [0.1.0] - 2026-07-10

### Added

- **`sayonlab.plots`** — the plotting subsystem. First fully implemented
  and tested module.
  - `sl.plot.line()` — line plot with optional confidence-interval band.
  - `sl.plot.scatter()` — scatter plot.
  - `sl.plot.bar()` — bar chart with optional error bars.
  - `sl.plot.auto()` — infers `line`/`scatter`/`bar` from the shape of the
    data, or dispatches an explicit `kind=`.
  - Publication-ready styling via `PlotStyle` / `PUBLICATION_STYLE`,
    scoped per-figure (never mutates global Matplotlib state).
  - Colorblind-safe default palette (Okabe-Ito).
  - Multi-format export (PNG, PDF, SVG) with automatic directory
    creation and per-format provenance metadata.
  - Memory-safe figure handling — figures are guaranteed to close, even
    if an exception occurs while plotting.
  - 27 passing unit tests covering validation, export, inference, and
    memory safety.
- `examples/plotting_quickstart.py` — runnable demo of the plotting API.
- Initial package structure: `sayonlab/plots/`, `sayonlab/stats.py`,
  `sayonlab/datasets.py`, `sayonlab/reports.py`, `sayonlab/themes.py`,
  `sayonlab/utils.py`.

### Scaffolded, not yet implemented

The following files exist as placeholders for future modules and
currently contain no functionality: `stats.py`, `datasets.py`,
`reports.py`, `themes.py`, `utils.py`. They are listed here so the
changelog accurately reflects what v0.1.0 actually does, rather than
implying these modules are functional.

[Unreleased]: https://github.com/sayonmitra/SayonLab/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/sayonmitra/SayonLab/releases/tag/v0.1.0