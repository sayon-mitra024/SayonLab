"""
SayonLab — Plotting Quickstart
================================
Run this script to see SayonLab's plotting API in action:

    python examples/plotting_quickstart.py

It generates four publication-ready figures into ./output/, demonstrating:
  1. line()   — with a confidence interval band
  2. scatter()
  3. bar()    — with error bars
  4. auto()   — automatic plot-type inference

No explanation needed beyond this file — that's the point.
"""

import sayonlab as sl

OUTPUT_DIR = "output"


def main() -> None:
    print("SayonLab Plotting Quickstart")
    print("=" * 40)

    # 1. Line plot with a confidence interval band.
    #    Useful for showing a trend (e.g. training loss, dose-response)
    #    alongside its uncertainty, with zero manual fill_between() code.
    days = [1, 2, 3, 4, 5, 6, 7]
    accuracy = [0.61, 0.68, 0.74, 0.79, 0.83, 0.85, 0.87]
    ci_lower = [0.55, 0.63, 0.70, 0.75, 0.80, 0.82, 0.84]
    ci_upper = [0.67, 0.73, 0.78, 0.83, 0.86, 0.88, 0.90]

    saved = sl.plot.line(
        days, accuracy,
        title="Model Accuracy Over Training",
        xlabel="Epoch",
        ylabel="Validation Accuracy",
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        save_path=f"{OUTPUT_DIR}/1_line_with_ci.png",
        formats=["png", "pdf"],
    )
    print(f"1. line()    -> {saved}")

    # 2. Scatter plot.
    #    Two measurements per sample — no monotonic relationship expected.
    dose_mg = [5, 10, 15, 20, 25, 30, 12, 22, 8, 27]
    response = [12, 25, 31, 40, 38, 45, 22, 41, 15, 43]

    saved = sl.plot.scatter(
        dose_mg, response,
        title="Dose–Response Relationship",
        xlabel="Dose (mg)",
        ylabel="Response (%)",
        label="Sample",
        save_path=f"{OUTPUT_DIR}/2_scatter.png",
    )
    print(f"2. scatter() -> {saved}")

    # 3. Bar chart with error bars.
    #    Classic group-comparison figure with standard error shown.
    groups = ["Control", "Treatment A", "Treatment B"]
    means = [12.5, 18.2, 15.7]
    std_error = [1.1, 0.9, 1.4]

    saved = sl.plot.bar(
        groups, means,
        error=std_error,
        title="Group Comparison",
        ylabel="Effect Size",
        save_path=f"{OUTPUT_DIR}/3_bar_with_error.png",
    )
    print(f"3. bar()     -> {saved}")

    # 4. auto() — SayonLab inspects the data and picks the right plot type.
    #    Non-numeric x (category names) -> automatically renders as a bar chart.
    #    No need to remember which function to call.
    cell_types = ["A", "B", "AB", "O"]
    counts = [320, 280, 90, 410]

    saved = sl.plot.auto(
        cell_types, counts,
        title="Sample Distribution by Blood Group",
        ylabel="Count",
        save_path=f"{OUTPUT_DIR}/4_auto_inferred.png",
    )
    print(f"4. auto()    -> {saved}  (inferred as 'bar' since x is non-numeric)")

    print("=" * 40)
    print(f"Done. Open the '{OUTPUT_DIR}/' folder to view the figures.")


if __name__ == "__main__":
    main()