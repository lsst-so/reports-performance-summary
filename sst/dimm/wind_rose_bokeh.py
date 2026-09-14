"""
Wind Rose Histogram (Bokeh) for ESS airflow data.

Drop this function into your notebook to replace the existing
`wind_rosewind_histogram` in Cell 11.  It produces an interactive Bokeh
polar bar chart where:

  - Angular bins  → wind direction
  - Radial extent → frequency (% of total observations)
  - Stacked colors → wind-speed ranges
  - Hover tool → direction, speed range (min/max), frequency

Usage
-----
    wind_rose_bokeh(df_ess_airflow)
    wind_rose_bokeh(df_ess_airflow, speed_bins=[0, 2, 4, 6, 8, 12, 20])
"""

import numpy as np
import pandas as pd

from bokeh.plotting import figure, show
from bokeh.models import (
    AnnularWedge,
    ColumnDataSource,
    HoverTool,
    Label,
    Legend,
    LegendItem,
    Range1d,
)
from bokeh.palettes import Viridis256, Cividis256


def wind_rose_bokeh(
    df: pd.DataFrame,
    speed_col: str = "speed",
    direction_col: str = "direction",
    n_dir_bins: int = 16,
    speed_bins: list | None = None,
    size: int = 650,
    palette: str = "viridis",
    title: str = "Wind Rose — ESS Weather Tower",
):
    """Stacked annular-wedge wind rose histogram (Bokeh).

    Parameters
    ----------
    df : pd.DataFrame
        Must contain ``speed_col`` (m/s) and ``direction_col`` (degrees, 0–360).
    n_dir_bins : int
        Number of angular slices (16 → 22.5° bins).
    speed_bins : list[float] | None
        Edges for the speed categories.  ``None`` → automatic quintile-based bins.
    palette : str
        'viridis' or 'cividis'.
    """
    data = df[[speed_col, direction_col]].dropna().copy()
    total = len(data)

    # ── speed bins ──────────────────────────────────────────────
    if speed_bins is None:
        quantiles = np.quantile(data[speed_col], [0, 0.2, 0.4, 0.6, 0.8, 1.0])
        speed_bins = np.unique(np.round(quantiles, 1)).tolist()
        if len(speed_bins) < 3:
            speed_bins = np.linspace(
                data[speed_col].min(), data[speed_col].max(), 6
            ).tolist()

    n_speed = len(speed_bins) - 1
    speed_labels = [
        f"{speed_bins[i]:.1f}–{speed_bins[i+1]:.1f} m/s"
        for i in range(n_speed)
    ]

    # ── direction bins (centered on N = 0°) ─────────────────────
    dir_bin_width = 360.0 / n_dir_bins
    half = dir_bin_width / 2
    dir_edges = np.linspace(-half, 360 - half, n_dir_bins + 1)

    shifted = (data[direction_col] + half) % 360 - half
    data["dir_bin"] = pd.cut(shifted, bins=dir_edges, labels=False, include_lowest=True)
    data["spd_bin"] = pd.cut(
        data[speed_col], bins=speed_bins, labels=False, include_lowest=True,
    )

    # ── count matrix (direction × speed) and per-cell stats ─────
    bin_centers_deg = np.arange(0, 360, dir_bin_width)

    # Pick palette
    pal = Viridis256 if palette == "viridis" else Cividis256
    color_indices = np.linspace(40, 240, n_speed).astype(int)
    colors = [pal[i] for i in color_indices]

    # Cardinal label helper
    _cardinals = {
        0: "N", 1: "NNE", 2: "NE", 3: "ENE",
        4: "E", 5: "ESE", 6: "SE", 7: "SSE",
        8: "S", 9: "SSW", 10: "SW", 11: "WSW",
        12: "W", 13: "WNW", 14: "NW", 15: "NNW",
    }

    def _cardinal(deg):
        idx = int(round(deg / (360 / 16))) % 16
        return _cardinals.get(idx, f"{deg:.0f}°")

    # Build per-wedge data
    all_inner = []
    all_outer = []
    all_start = []
    all_end = []
    all_color = []
    all_dir_label = []
    all_dir_center = []
    all_spd_label = []
    all_spd_min = []
    all_spd_max = []
    all_freq = []
    all_count = []

    # Track cumulative bottoms per direction bin
    bottoms = np.zeros(n_dir_bins)

    # Bokeh angles: 0 = right (East), counter-clockwise positive
    # Meteorological: 0 = North, clockwise
    # Convert: bokeh_angle = pi/2 - met_angle_rad
    wedge_width = np.deg2rad(dir_bin_width) * 0.95

    for s in range(n_speed):
        for d in range(n_dir_bins):
            mask = (data["dir_bin"] == d) & (data["spd_bin"] == s)
            count = mask.sum()
            freq_pct = 100.0 * count / total

            # Actual min/max speed in this cell
            if count > 0:
                cell_speeds = data.loc[mask, speed_col]
                spd_min = cell_speeds.min()
                spd_max = cell_speeds.max()
            else:
                spd_min = speed_bins[s]
                spd_max = speed_bins[s + 1]

            center_deg = bin_centers_deg[d]
            center_rad = np.deg2rad(90 - center_deg)  # bokeh polar convention

            inner = bottoms[d]
            outer = bottoms[d] + freq_pct

            all_start.append(center_rad - wedge_width / 2)
            all_end.append(center_rad + wedge_width / 2)
            all_inner.append(inner)
            all_outer.append(outer)
            all_color.append(colors[s])
            all_dir_label.append(f"{_cardinal(center_deg)} ({center_deg:.0f}°)")
            all_dir_center.append(center_deg)
            all_spd_label.append(speed_labels[s])
            all_spd_min.append(round(spd_min, 2))
            all_spd_max.append(round(spd_max, 2))
            all_freq.append(round(freq_pct, 2))
            all_count.append(count)

        # Update bottoms after this speed layer
        for d in range(n_dir_bins):
            mask = (data["dir_bin"] == d) & (data["spd_bin"] == s)
            bottoms[d] += 100.0 * mask.sum() / total

    source = ColumnDataSource(data=dict(
        inner_radius=all_inner,
        outer_radius=all_outer,
        start_angle=all_start,
        end_angle=all_end,
        color=all_color,
        dir_label=all_dir_label,
        dir_center=all_dir_center,
        spd_label=all_spd_label,
        spd_min=all_spd_min,
        spd_max=all_spd_max,
        freq=all_freq,
        count=all_count,
    ))

    # ── figure ──────────────────────────────────────────────────
    max_r = bottoms.max() * 1.15
    p = figure(
        width=size,
        height=size,
        x_range=Range1d(-max_r, max_r),
        y_range=Range1d(-max_r, max_r),
        match_aspect=True,
        tools="pan,wheel_zoom,reset,save",
        title=title,
    )
    p.title.text_font_size = "14pt"
    p.axis.visible = False
    p.grid.visible = False
    p.outline_line_color = None
    p.background_fill_color = None

    # ── radial grid rings ───────────────────────────────────────
    tick_step = _nice_tick(max_r / 4)
    for r_val in np.arange(tick_step, max_r, tick_step):
        angles = np.linspace(0, 2 * np.pi, 100)
        p.line(
            r_val * np.cos(angles), r_val * np.sin(angles),
            line_color="#cccccc", line_width=0.5, line_dash="dotted",
        )
        p.add_layout(Label(
            x=0, y=r_val,
            text=f"{r_val:.0f}%",
            text_font_size="8pt", text_color="#888888",
            x_offset=3, y_offset=-2,
        ))

    # ── cardinal direction labels ───────────────────────────────
    label_r = max_r * 1.05
    for deg, txt in [(0, "N"), (90, "E"), (180, "S"), (270, "W")]:
        rad = np.deg2rad(90 - deg)
        p.add_layout(Label(
            x=label_r * np.cos(rad),
            y=label_r * np.sin(rad),
            text=txt,
            text_font_size="12pt",
            text_font_style="bold",
            text_align="center",
            text_baseline="middle",
        ))
    for deg, txt in [(45, "NE"), (135, "SE"), (225, "SW"), (315, "NW")]:
        rad = np.deg2rad(90 - deg)
        p.add_layout(Label(
            x=label_r * np.cos(rad),
            y=label_r * np.sin(rad),
            text=txt,
            text_font_size="9pt",
            text_color="#666666",
            text_align="center",
            text_baseline="middle",
        ))

    # ── wedges ──────────────────────────────────────────────────
    wedge_renderer = p.annular_wedge(
        x=0, y=0,
        inner_radius="inner_radius",
        outer_radius="outer_radius",
        start_angle="start_angle",
        end_angle="end_angle",
        fill_color="color",
        line_color="white",
        line_width=0.4,
        fill_alpha=0.85,
        source=source,
    )

    # ── hover tool ──────────────────────────────────────────────
    hover = HoverTool(
        renderers=[wedge_renderer],
        tooltips=[
            ("Direction", "@dir_label"),
            ("Speed bin", "@spd_label"),
            ("Speed min", "@spd_min{0.1f} m/s"),
            ("Speed max", "@spd_max{0.1f} m/s"),
            ("Frequency", "@freq{0.1f}%"),
            ("Count", "@count"),
        ],
    )
    p.add_tools(hover)

    # ── legend (manual, outside plot) ───────────────────────────
    legend_items = []
    for s in range(n_speed):
        # Create a tiny invisible glyph per speed bin for the legend
        src = ColumnDataSource(data=dict(x=[0], y=[0]))
        r = p.scatter("x", "y", size=0, source=src, fill_color=colors[s], line_color=colors[s])
        legend_items.append(LegendItem(label=speed_labels[s], renderers=[r]))

    legend = Legend(items=legend_items, title="Wind Speed", location="top_left")
    legend.label_text_font_size = "9pt"
    legend.title_text_font_size = "10pt"
    p.add_layout(legend, "right")

    # ── summary stats label ─────────────────────────────────────
    dominant_idx = bottoms.argmax()
    dominant_deg = bin_centers_deg[dominant_idx]
    mean_spd = data[speed_col].mean()
    median_spd = data[speed_col].median()
    calm_pct = 100.0 * (data[speed_col] < speed_bins[1]).sum() / total

    stats = (
        f"N = {total:,}  |  "
        f"Dominant ≈ {_cardinal(dominant_deg)} ({dominant_deg:.0f}°)  |  "
        f"Mean = {mean_spd:.1f} m/s  |  "
        f"Median = {median_spd:.1f} m/s  |  "
        f"Calm (< {speed_bins[1]:.1f} m/s) = {calm_pct:.1f}%"
    )
    p.add_layout(Label(
        x=0, y=0,
        text=stats,
        text_font_size="8pt",
        text_color="#555555",
        x_units="screen", y_units="screen",
        x_offset=10, y_offset=10,
    ))

    show(p)
    return p


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
