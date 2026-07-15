<div align="center">

<img width="160" alt="image" src="https://github.com/user-attachments/assets/9074b342-fb20-44c4-af32-fe885248a187" />


# SayonLab

**A Scientific Research Productivity Framework**

Reducing the engineering overhead of scientific research — one automated workflow at a time.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
![CI](https://img.shields.io/badge/CI-coming%20soon-lightgrey.svg)
[![PyPI](https://img.shields.io/pypi/v/sayonlab)](https://pypi.org/project/sayonlab/)
![Docs](https://img.shields.io/badge/docs-coming%20soon-lightgrey.svg)

</div>

---

## Introduction

Scientific research involves a large amount of repetitive engineering work
that has nothing to do with the actual research question: writing
boilerplate plotting code, manually formatting figures for publication,
re-implementing the same statistical checks across projects, and hand-
assembling reports. This work is necessary, but it consumes time that could
otherwise go toward the science itself.

SayonLab is an open-source framework aimed at reducing that overhead. It is
built as a collection of focused subsystems — plotting, statistics, dataset
handling, reporting, and others over time — unified behind a single,
consistent Python API.

**Current status:** SayonLab is in early, active development. As of v0.1.0,
one subsystem — `sayonlab.plots` — is implemented, tested, and usable. The
rest of the framework described below is roadmap, not shipped functionality,
and is labeled accordingly throughout this document.

## Why SayonLab?

SayonLab does not aim to replace NumPy, pandas, Matplotlib, SciPy, or
scikit-learn. Those libraries are stable, well-understood, and deeply
embedded in the scientific Python ecosystem for good reason.

What SayonLab aims to do is sit on top of them and automate the repetitive
decisions researchers make every time they use them — sensible defaults,
consistent styling, common validation, and output formats suited to
publication — so that using them well requires less repeated code.

A traditional plotting workflow might look like:

```
Load data → plt.subplots() → manually set fonts/DPI/grid → plot →
manually check for empty/mismatched data → fill_between for CI →
plt.tight_layout() → create output directory manually → savefig for
each format → remember to plt.close()
```

The equivalent SayonLab workflow:

```python
sl.plot.line(x, y, ci_lower=lo, ci_upper=hi, save_path="fig1", formats=["png", "pdf"])
```

Validation, styling, layout, directory creation, multi-format export, and
figure cleanup are handled internally. Matplotlib still does the actual
rendering — SayonLab automates the decisions around it.

## Key Features

### Available in v0.1

- Publication-ready line, scatter, and bar plots with a single function call
- Optional confidence-interval bands (`line`) and error bars (`bar`)
- Automatic plot-type inference via `sl.plot.auto()`
- Colorblind-safe default palette (Okabe-Ito)
- Scoped styling — never mutates global Matplotlib state
- Multi-format export (PNG, PDF, SVG) with automatic directory creation
- Per-format provenance metadata embedded in exported figures
- Memory-safe figure handling (no leaked figures, even on error)
- Informative, specific validation errors instead of raw Matplotlib tracebacks

### Planned for future versions

These are roadmap items, not implemented features. See [Roadmap](#roadmap)
for status.

- Statistical analysis utilities (`stats`)
- Dataset inspection and validation utilities (`datasets`)
- Automated report generation (`reports`)
- Experiment tracking and reproducibility metadata
- Additional plot types (histograms, box/violin plots, ML evaluation curves)
- Optional R-backend interoperability for bioinformatics-specific packages

## Current Modules

| Module | Status | Description |
|---|---|---|
| `sayonlab.plots` | ✅ Implemented | Publication-ready plotting: `line`, `scatter`, `bar`, `auto`. Fully tested (27 passing tests). |
| `sayonlab.stats` | 🔮 Planned | Statistical summaries and hypothesis testing utilities. Not yet implemented. |
| `sayonlab.datasets` | 🔮 Planned | Dataset loading, validation, and inspection utilities. Not yet implemented. |
| `sayonlab.reports` | 🔮 Planned | Automated report generation (Markdown/HTML/PDF). Not yet implemented. |

Only `sayonlab.plots` currently exists in the repository. The modules above
marked "Planned" are described here so the intended scope of the project is
visible, not because their files currently exist — see the
[Roadmap](#roadmap) for how these are sequenced.

## Installation

SayonLab is published to PyPI:

```bash
pip install sayonlab   
```

## Quick Start

```python
import sayonlab as sl

x = [1, 2, 3, 4, 5]
y = [2, 4, 5, 7, 8]

sl.plot.line(
    x, y,
    title="Example Trend",
    xlabel="Time",
    ylabel="Value",
    save_path="trend.png",
)
```

That's it — the figure is styled, laid out, and saved automatically. See
`examples/plotting_quickstart.py` for a complete walkthrough of `line`,
`scatter`, `bar`, and `auto`.

## Why Researchers May Like SayonLab

- **Publication-ready by default** — 300 DPI, colorblind-safe palette, and
  clean typography without configuring anything.
- **Sensible defaults, not rigid ones** — every default can be overridden
  via a `PlotStyle` object when a figure needs to differ.
- **Automation, not obscurity** — SayonLab automates repetitive steps
  (directory creation, multi-format export, layout) rather than hiding what
  Matplotlib is doing; the output is still a normal Matplotlib figure
  underneath.
- **Reproducibility-minded** — exported figures carry embedded provenance
  metadata (creator, creation date) by default.
- **A clean, small public API** — four functions (`line`, `scatter`, `bar`,
  `auto`) cover the v0.1 surface. Nothing to memorize beyond that.

## Architecture Overview

```
sayonlab/
├── __init__.py          # exposes sl.plot (stable public API)
└── plots/                # the only implemented subsystem in v0.1
    ├── __init__.py       # public surface: line, scatter, bar, auto, PlotStyle, ...
    ├── validation.py      # shared input validation
    ├── style.py            # scoped publication styling, colorblind-safe palette
    ├── base.py              # figure lifecycle: creation, layout, memory-safe cleanup
    ├── export.py            # multi-format save, metadata, directory creation
    └── core.py               # public functions: line(), scatter(), bar(), auto()
```

Each file in `plots/` has exactly one responsibility, and lower layers never
depend on higher ones — see `sayonlab/plots/ARCHITECTURE.md` (local
reference, not tracked in version control) for the full internal design
rationale.

## Roadmap

- ✅ **v0.1.0** — Plotting subsystem (`sayonlab.plots`): line, scatter, bar,
  auto-inference, publication styling, multi-format export, full test
  coverage.
- 🚧 **v0.2** — Statistics subsystem (`sayonlab.stats`): summary statistics,
  common hypothesis tests, effect sizes.
- 🔮 **v0.3** — Dataset utilities (`sayonlab.datasets`): validation,
  corruption/duplicate detection, class distribution reporting.
- 🔮 **v0.4** — Reporting (`sayonlab.reports`): automated Markdown/HTML
  report generation from plots and statistics.
- 🔮 **v0.5+** — Experiment tracking and reproducibility metadata; additional
  plot types (ML evaluation curves, statistical plots); exploration of
  optional R-backend interoperability for bioinformatics workflows.

Version numbers above are indicative of sequencing, not committed dates.

## Documentation

A dedicated documentation site is planned but does not yet exist. For now,
this README and the docstrings within each module (NumPy-style, complete
with parameters/returns/examples) are the primary reference. Every public
function in `sayonlab.plots` has a full docstring accessible via
`help(sl.plot.line)`.

## Examples

See [`examples/plotting_quickstart.py`](examples/plotting_quickstart.py) for
a runnable demonstration of all four plotting functions, including a
confidence-interval band, error bars, and automatic plot-type inference.

```bash
python examples/plotting_quickstart.py
```

## Testing

```bash
pip install pytest
pytest tests/ -v
```

The `sayonlab.plots` test suite currently includes 27 tests covering
validation, confidence intervals, error bars, plot-type inference, export
correctness, and memory-safe figure handling.

## Contributing

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for the current contribution policy and guidelines.

At this stage, feedback, bug reports, documentation improvements, and feature suggestions are especially welcome.

## License

SayonLab is licensed under the [Apache License 2.0](LICENSE).

## Citation

If you use SayonLab in academic research, please cite it using the metadata provided in [`CITATION.cff`](CITATION.cff).

A DOI will be added in a future stable release to provide versioned, permanent software citations.

## Acknowledgements

SayonLab is built on top of, and would not be possible without, the
scientific Python ecosystem — in particular NumPy, Matplotlib, and Pillow.

## Contact

Created and maintained by **Sayon Mitra**.
Email: [sayonmitracode@gmail.com](mailto:sayonmitracode@gmail.com)
For questions or discussion, please open a GitHub issue.

## Project Status

SayonLab is under active, early-stage development. The plotting subsystem
(`sayonlab.plots`) is stable and tested; all other functionality described
in this document is planned but not yet implemented. Expect the public API
to evolve as new subsystems are added.

---

<div align="center">

Built by **Sayon Mitra**

</div>
