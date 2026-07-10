"""
Tests for sayonlab.plots.core — the public plotting API.

Covers: happy paths for line/scatter/bar, validation error messages,
confidence-interval and error-bar handling, all three auto() inference
branches plus explicit override, export behavior, and the memory-safety
guarantee (no leaked Matplotlib figures across many calls).
"""

import matplotlib.pyplot as plt
import pytest

import sayonlab as sl
from sayonlab.plots.core import _infer_kind
from sayonlab.plots.validation import SayonLabValidationError


# ---------------------------------------------------------------------------
# line()
# ---------------------------------------------------------------------------
class TestLine:
    def test_happy_path_saves_expected_files(self, tmp_path):
        out = tmp_path / "line.png"
        saved = sl.plot.line([1, 2, 3], [1, 4, 9], title="Growth", save_path=out)

        assert saved == [out]
        assert out.exists()

    def test_multi_format_export(self, tmp_path):
        stem = tmp_path / "line"
        saved = sl.plot.line(
            [1, 2, 3], [1, 4, 9], save_path=stem, formats=["png", "pdf", "svg"]
        )

        assert len(saved) == 3
        assert all(p.exists() for p in saved)
        assert {p.suffix for p in saved} == {".png", ".pdf", ".svg"}

    def test_no_save_path_returns_none(self):
        assert sl.plot.line([1, 2, 3], [1, 4, 9]) is None

    def test_mismatched_length_raises_with_clear_message(self):
        with pytest.raises(SayonLabValidationError, match="same length"):
            sl.plot.line([1, 2, 3], [1, 2])

    def test_empty_input_raises(self):
        with pytest.raises(SayonLabValidationError, match="empty"):
            sl.plot.line([], [])

    def test_ci_bounds_must_be_given_together(self):
        with pytest.raises(SayonLabValidationError, match="together"):
            sl.plot.line([1, 2, 3], [1, 4, 9], ci_lower=[0, 3, 8])

    def test_ci_lower_exceeding_upper_raises(self):
        with pytest.raises(SayonLabValidationError, match="ci_lower"):
            sl.plot.line(
                [1, 2, 3], [1, 4, 9],
                ci_lower=[5, 5, 5], ci_upper=[1, 1, 1],
            )

    def test_ci_band_saves_successfully(self, tmp_path):
        out = tmp_path / "line_ci.png"
        saved = sl.plot.line(
            [1, 2, 3], [1, 4, 9],
            ci_lower=[0, 3, 8], ci_upper=[2, 5, 10],
            save_path=out,
        )
        assert saved == [out]
        assert out.exists()


# ---------------------------------------------------------------------------
# scatter()
# ---------------------------------------------------------------------------
class TestScatter:
    def test_happy_path_saves_expected_file(self, tmp_path):
        out = tmp_path / "scatter.png"
        saved = sl.plot.scatter([1, 2, 3], [3, 1, 2], label="A", save_path=out)

        assert saved == [out]
        assert out.exists()

    def test_mismatched_length_raises(self):
        with pytest.raises(SayonLabValidationError, match="same length"):
            sl.plot.scatter([1, 2, 3], [1, 2])


# ---------------------------------------------------------------------------
# bar()
# ---------------------------------------------------------------------------
class TestBar:
    def test_happy_path_with_error_bars(self, tmp_path):
        out = tmp_path / "bar.png"
        saved = sl.plot.bar(
            ["Control", "Treatment"], [12.5, 18.2],
            error=[1.1, 0.9], save_path=out,
        )
        assert saved == [out]
        assert out.exists()

    def test_category_value_length_mismatch_raises(self):
        with pytest.raises(SayonLabValidationError, match="same length"):
            sl.plot.bar(["A", "B"], [1, 2, 3])

    def test_empty_categories_raises(self):
        with pytest.raises(SayonLabValidationError, match="empty"):
            sl.plot.bar([], [])

    def test_negative_error_raises(self):
        with pytest.raises(SayonLabValidationError, match="non-negative"):
            sl.plot.bar(["A", "B"], [1, 2], error=[-1, 0.5])

    def test_error_length_mismatch_raises(self):
        with pytest.raises(SayonLabValidationError, match="length"):
            sl.plot.bar(["A", "B"], [1, 2], error=[0.1, 0.2, 0.3])


# ---------------------------------------------------------------------------
# auto() — inference logic (unit-level, via _infer_kind directly)
# ---------------------------------------------------------------------------
class TestInferKind:
    def test_increasing_numeric_x_infers_line(self):
        assert _infer_kind([1, 2, 3, 4]) == "line"

    def test_nonmonotonic_numeric_x_infers_scatter(self):
        assert _infer_kind([3, 1, 2]) == "scatter"

    def test_nonnumeric_x_infers_bar(self):
        assert _infer_kind(["A", "B", "C"]) == "bar"

    def test_too_few_points_raises(self):
        with pytest.raises(SayonLabValidationError, match="fewer than 2"):
            _infer_kind([1])


# ---------------------------------------------------------------------------
# auto() — end-to-end dispatch
# ---------------------------------------------------------------------------
class TestAutoDispatch:
    def test_infers_and_saves_line(self, tmp_path):
        out = tmp_path / "auto_line.png"
        saved = sl.plot.auto([1, 2, 3, 4], [1, 4, 9, 16], save_path=out)
        assert saved == [out]
        assert out.exists()

    def test_infers_and_saves_scatter(self, tmp_path):
        out = tmp_path / "auto_scatter.png"
        saved = sl.plot.auto([3, 1, 2], [5, 2, 8], save_path=out)
        assert saved == [out]
        assert out.exists()

    def test_infers_and_saves_bar(self, tmp_path):
        out = tmp_path / "auto_bar.png"
        saved = sl.plot.auto(["A", "B", "C"], [4, 7, 2], save_path=out)
        assert saved == [out]
        assert out.exists()

    def test_explicit_kind_overrides_inference(self, tmp_path):
        # x is increasing (would infer "line"), force "scatter" instead.
        out = tmp_path / "auto_override.png"
        saved = sl.plot.auto([1, 2, 3], [1, 4, 9], kind="scatter", save_path=out)
        assert saved == [out]
        assert out.exists()

    def test_invalid_kind_raises(self):
        with pytest.raises(SayonLabValidationError, match="Unknown kind"):
            sl.plot.auto([1, 2, 3], [1, 4, 9], kind="pie")


# ---------------------------------------------------------------------------
# Memory safety — the guarantee figure_scope() provides
# ---------------------------------------------------------------------------
class TestMemorySafety:
    def test_no_figures_leak_across_many_calls(self, tmp_path):
        baseline = len(plt.get_fignums())

        for i in range(20):
            sl.plot.line([1, 2, 3], [1, 4, 9], save_path=tmp_path / f"fig_{i}.png")

        assert len(plt.get_fignums()) == baseline

    def test_figure_closed_even_when_show_is_true(self, tmp_path):
        # show=True still must not leak, since plt.show() with the Agg
        # backend used in tests is a no-op (no GUI event loop).
        baseline = len(plt.get_fignums())
        sl.plot.scatter([1, 2, 3], [1, 2, 3], show=True)
        assert len(plt.get_fignums()) == baseline


# ---------------------------------------------------------------------------
# Custom style is actually applied
# ---------------------------------------------------------------------------
class TestCustomStyle:
    def test_custom_dpi_is_honored(self, tmp_path):
        from PIL import Image

        custom_style = sl.plot.PlotStyle(dpi=150)
        out = tmp_path / "custom_dpi.png"
        sl.plot.line([1, 2, 3], [1, 4, 9], style=custom_style, save_path=out)

        with Image.open(out) as img:
            dpi_x, _ = img.info.get("dpi", (None, None))
        assert dpi_x == pytest.approx(150, abs=1)