"""
Wind Rose Histogram for ESS airflow data.

Drop this function into your notebook to replace the existing
`wind_rosewind_histogram` in Cell 11.  It produces a publication-quality
matplotlib polar bar chart where:

  - Angular bins  → wind direction
  - Radial extent → frequency (% of total observations)
  - Stacked colors → wind-speed ranges

Usage
-----
    wind_rose(df_ess_airflow)                       # quick default
    wind_rose(df_ess_airflow, speed_bins=[0, 2, 4, 6, 8, 12, 20])
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors


def wind_rose(
    df: pd.DataFrame,
    speed_col: str = "speed",
    direction_col: str = "direction",
    n_dir_bins: int = 16,
    speed_bins: list | None = None,
    figsize: tuple = (9, 9),
    cmap: str = "viridis",
    title: str = "Wind Rose — ESS Weather Tower",
    edgecolor: str = "white",
    linewidth: float = 0.3,
):
    """Stacked‑bar wind rose histogram (matplotlib, polar projection).

    Parameters
    ----------
    df : pd.DataFrame
        Must contain ``speed_col`` (m/s) and ``direction_col`` (degrees, 0–360).
    n_dir_bins : int
        Number of angular slices (16 → 22.5° bins).
    speed_bins : list[float] | None
        Edges for the speed categories.  ``None`` → automatic quintile‑based bins.
    """
    data = df[[speed_col, direction_col]].dropna().copy()

    # ── speed bins ──────────────────────────────────────────────
    if speed_bins is None:
        quantiles = np.quantile(data[speed_col], [0, 0.2, 0.4, 0.6, 0.8, 1.0])
        speed_bins = np.unique(np.round(quantiles, 1))
        # Ensure at least two edges
        if len(speed_bins) < 3:
            speed_bins = np.linspace(
                data[speed_col].min(), data[speed_col].max(), 6
            )

    n_speed = len(speed_bins) - 1
    speed_labels = [
        f"{speed_bins[i]:.1f}–{speed_bins[i+1]:.1f} m/s"
        for i in range(n_speed)
    ]

    # ── direction bins (centered on N = 0°) ─────────────────────
    dir_bin_width = 360.0 / n_dir_bins
    half = dir_bin_width / 2
    dir_edges = np.linspace(-half, 360 - half, n_dir_bins + 1)

    # Shift directions so that the first bin straddles 0°
    shifted = (data[direction_col] + half) % 360 - half
    data["dir_bin"] = pd.cut(shifted, bins=dir_edges, labels=False, include_lowest=True)
    data["spd_bin"] = pd.cut(
        data[speed_col],
        bins=speed_bins,
        labels=False,
        include_lowest=True,
    )

    total = len(data)

    # ── count matrix (direction × speed) ────────────────────────
    counts = np.zeros((n_dir_bins, n_speed))
    for d in range(n_dir_bins):
        for s in range(n_speed):
            counts[d, s] = ((data["dir_bin"] == d) & (data["spd_bin"] == s)).sum()

    freq = 100.0 * counts / total  # percentage

    # ── angular coordinates ─────────────────────────────────────
    bin_centers_deg = np.arange(0, 360, dir_bin_width)
    theta = np.deg2rad(bin_centers_deg)  # meteorological → math handled by axis config
    bar_width = np.deg2rad(dir_bin_width) * 0.95  # tiny gap between bars

    # ── colormap ────────────────────────────────────────────────
    colormap = cm.get_cmap(cmap, n_speed)
    colors = [colormap(i / (n_speed - 1)) for i in range(n_speed)]

    # ── plot ─────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=figsize, subplot_kw={"projection": "polar"}, dpi=120)
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)  # clockwise

    bottoms = np.zeros(n_dir_bins)
    bars_per_speed = []
    for s in range(n_speed):
        bars = ax.bar(
            theta,
            freq[:, s],
            width=bar_width,
            bottom=bottoms,
            color=colors[s],
            edgecolor=edgecolor,
            linewidth=linewidth,
            label=speed_labels[s],
        )
        bars_per_speed.append(bars)
        bottoms += freq[:, s]

    # ── radial grid & labels ────────────────────────────────────
    max_pct = bottoms.max()
    tick_step = _nice_tick(max_pct / 4)
    r_ticks = np.arange(tick_step, max_pct + tick_step, tick_step)
    ax.set_yticks(r_ticks)
    ax.set_yticklabels([f"{v:.0f}%" for v in r_ticks], fontsize=8, color="0.4")
    ax.set_rlabel_position(67.5)

    # Cardinal labels
    ax.set_xticks(np.deg2rad([0, 45, 90, 135, 180, 225, 270, 315]))
    ax.set_xticklabels(["N", "NE", "E", "SE", "S", "SW", "W", "NW"], fontsize=10)

    # Legend & title
    ax.legend(
        loc="upper left",
        bbox_to_anchor=(1.05, 1.0),
        title="Wind Speed",
        fontsize=9,
        title_fontsize=10,
        frameon=True,
        fancybox=True,
    )
    ax.set_title(title, pad=24, fontsize=13, weight="bold")

    # ── summary annotation ──────────────────────────────────────
    dominant_dir_idx = bottoms.argmax()
    dominant_dir = bin_centers_deg[dominant_dir_idx]
    mean_speed = data[speed_col].mean()
    median_speed = data[speed_col].median()
    calm_pct = 100.0 * (data[speed_col] < speed_bins[1]).sum() / total

    stats_text = (
        f"N = {total:,}\n"
        f"Dominant dir ≈ {dominant_dir:.0f}°\n"
        f"Mean speed = {mean_speed:.1f} m/s\n"
        f"Median speed = {median_speed:.1f} m/s\n"
        f"Calm (< {speed_bins[1]:.1f} m/s) = {calm_pct:.1f}%"
    )
    fig.text(
        0.96, 0.2, stats_text,
        fontsize=8, family="monospace",
        ha="right", va="bottom",
        bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="0.7", alpha=0.85),
    )

    plt.tight_layout()
    return fig, ax


# ── helper ──────────────────────────────────────────────────────
def _nice_tick(rough):
    """Round *rough* to a 'nice' tick interval (1, 2, 5, 10, …)."""
    if rough <= 0:
        return 1
    mag = 10 ** np.floor(np.log10(rough))
    residual = rough / mag
    if residual <= 1.5:
        return mag
    elif residual <= 3.5:
        return 2 * mag
    elif residual <= 7.5:
        return 5 * mag
    else:
        return 10 * mag
