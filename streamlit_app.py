"""Portfolio plant dashboard — reads readings.csv committed to the repo."""

import html
from datetime import date
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st
from pandas.errors import EmptyDataError

CSV_PATH = Path(__file__).parent / "readings.csv"
REQUIRED_COLUMNS = {
    "timestamp",
    "plant_id",
    "moisture_percentage",
    "status_category",
}

PLANT_NAMES = {
    1: "Gynura Aurantiaca",
    2: "Tradescantia Zebrina",
    3: "Monstera Deliciosa",
}

PLANT_COLORS = {
    1: "#1f7a45",  # Gynura — green
    2: "#7a4fb0",  # Tradescantia — purple
    3: "#e07a2a",  # Monstera — orange
    4: "#1f6fbf",  # spare
}

PLANT_BLURBS = {
    1: {
        "about": "Soft velvet purple foliage—better known as purple passion.",
        "fact": "Fun Fact: tiny leaf hairs catch light and shimmer like fabric.",
    },
    2: {
        "about": "A trailing houseplant with bold silver zebra stripes.",
        "fact": "Fun Fact: stem cuttings often root in water overnight.",
    },
    3: {
        "about": "A tropical climber famous for holey Swiss-cheese leaves.",
        "fact": "Fun Fact: ripe fruit can taste like pineapple and banana.",
    },
}

STATUS_COLORS = {
    "Dry": "#c45c3e",
    "Moist": "#c4922a",
    "Optimal": "#2d8a55",
    "Soggy": "#2a7a8a",
    "Unknown": "#5a7262",
}

BADGE_STYLES = {
    "Dry": ("#c45c3e", "rgba(196, 92, 62, 0.12)"),
    "Moist": ("#8a6418", "rgba(196, 146, 42, 0.14)"),
    "Optimal": ("#2d8a55", "rgba(45, 138, 85, 0.12)"),
    "Soggy": ("#2a7a8a", "rgba(42, 122, 138, 0.12)"),
    "Unknown": ("#5a7262", "rgba(90, 114, 98, 0.12)"),
}

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=Manrope:wght@400;500;600;700&display=swap');

.stApp {
  background:
    radial-gradient(ellipse 90% 60% at 10% -10%, #f4f9e8 0%, transparent 55%),
    radial-gradient(ellipse 70% 50% at 100% 0%, #cfe0c8 0%, transparent 50%),
    linear-gradient(165deg, #e8f0e6 0%, #d5e4d2 100%);
  background-attachment: fixed;
}

.stApp::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  opacity: 0.35;
  background-image: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%232d5a3d' fill-opacity='0.06'%3E%3Cpath d='M30 5c2 8 8 14 16 16-8 2-14 8-16 16-2-8-8-14-16-16 8-2 14-8 16-16z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
  z-index: 0;
}

html, body, [class*="css"] {
  font-family: 'Manrope', sans-serif;
  color: #1a2e22;
}

.block-container {
  max-width: 1100px;
  padding-top: 1.5rem;
  padding-bottom: 2.5rem;
}

h1 {
  font-family: 'Fraunces', Georgia, serif !important;
  color: #2d5a3d !important;
  font-weight: 700 !important;
  letter-spacing: -0.02em;
}

[data-testid="stVerticalBlockBorderWrapper"] {
  background: rgba(255, 252, 247, 0.82) !important;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(45, 90, 61, 0.14) !important;
  border-radius: 22px !important;
  box-shadow: 0 18px 40px rgba(26, 46, 34, 0.08);
  padding: 0.35rem 0.15rem;
}

.panel-title {
  font-family: 'Fraunces', Georgia, serif;
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 0.1rem;
  color: #1a2e22;
}

.panel-sub {
  font-size: 0.78rem;
  color: #5a7262;
  margin: 0 0 0.75rem;
}

.gauge-card {
  border: 1px solid rgba(45, 90, 61, 0.14);
  border-radius: 14px;
  padding: 0.75rem 0.85rem;
  background: rgba(255, 252, 247, 0.65);
  margin-bottom: 0.35rem;
}

.gauge-card.selected {
  border-color: #2d5a3d;
  box-shadow: 0 0 0 2px rgba(196, 224, 122, 0.7);
}

.gauge-top {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 0.5rem;
}

.gauge-name {
  font-weight: 600;
  font-size: 0.88rem;
}

.gauge-pct {
  font-family: 'Fraunces', Georgia, serif;
  font-size: 1.35rem;
  font-weight: 700;
}

.gauge-bar {
  height: 10px;
  border-radius: 999px;
  background: rgba(45, 90, 61, 0.1);
  overflow: hidden;
  margin: 0.55rem 0 0.45rem;
}

.gauge-fill {
  height: 100%;
  border-radius: inherit;
}

.gauge-blurb {
  margin: 0 0 0.4rem;
  font-size: 0.68rem;
  line-height: 1.35;
  color: #5a7262;
}

.gauge-blurb .fact {
  display: block;
  margin-top: 0.15rem;
  color: rgba(90, 114, 98, 0.85);
}

.badge {
  display: inline-block;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  padding: 0.28rem 0.5rem;
  border-radius: 8px;
}

.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  margin: 0.75rem 0 1rem;
}

.legend span {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.72rem;
  font-weight: 600;
  color: #5a7262;
  padding: 0.3rem 0.6rem;
  border-radius: 999px;
  border: 1px solid rgba(45, 90, 61, 0.14);
  background: rgba(255, 252, 247, 0.55);
}

.legend i {
  width: 0.55rem;
  height: 0.55rem;
  border-radius: 50%;
  display: inline-block;
}

.intro {
  margin: 0.35rem 0 1.1rem;
  padding: 0.85rem 1rem;
  border-radius: 14px;
  border: 1px solid rgba(45, 90, 61, 0.14);
  background: rgba(255, 252, 247, 0.72);
}

.intro .byline {
  font-family: 'Fraunces', Georgia, serif;
  font-size: 0.95rem;
  font-weight: 700;
  color: #2d5a3d;
  margin: 0 0 0.35rem;
}

.intro p {
  margin: 0;
  font-size: 0.84rem;
  line-height: 1.45;
  color: #5a7262;
}

.day-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.5rem;
  margin: 0.35rem 0 0.85rem;
}

.day-stat {
  background: rgba(255, 252, 247, 0.65);
  border: 1px solid rgba(45, 90, 61, 0.12);
  border-radius: 12px;
  padding: 0.55rem 0.6rem;
  text-align: center;
}

.day-stat .label {
  display: block;
  font-size: 0.65rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #5a7262;
  margin-bottom: 0.15rem;
}

.day-stat .value {
  font-family: 'Fraunces', Georgia, serif;
  font-size: 1.05rem;
  font-weight: 700;
  color: #1a2e22;
}

.plant-swatch {
  display: inline-block;
  width: 0.55rem;
  height: 0.55rem;
  border-radius: 50%;
  margin-right: 0.35rem;
  vertical-align: middle;
}

.day-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin: 0.35rem 0 0.65rem;
}

.day-chip {
  display: inline-block;
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.35rem 0.65rem;
  border-radius: 999px;
  border: 1px solid rgba(45, 90, 61, 0.14);
  background: rgba(255, 252, 247, 0.7);
  color: #5a7262;
}

.day-chip.active {
  background: #2d5a3d;
  color: #f5f8f0;
  border-color: #2d5a3d;
}

.hour-columns {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(168px, 1fr));
  gap: 0.65rem;
  margin-top: 0.75rem;
}

.hour-col-head {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.72rem;
  font-weight: 700;
  color: #1a2e22;
  margin-bottom: 0.35rem;
}

.hour-col-head span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hour-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 0.3rem;
  max-height: 220px;
  overflow-y: auto;
}

.hour-list li {
  display: grid;
  grid-template-columns: 3.6rem 1fr auto;
  align-items: center;
  gap: 0.35rem;
  padding: 0.4rem 0.45rem;
  border-radius: 10px;
  background: rgba(255, 252, 247, 0.65);
  border: 1px solid rgba(45, 90, 61, 0.12);
  font-size: 0.78rem;
}

.hour-list .time {
  font-weight: 700;
  color: #2d5a3d;
  font-variant-numeric: tabular-nums;
}

.hour-list .pct {
  font-family: 'Fraunces', Georgia, serif;
  font-weight: 700;
  font-size: 0.88rem;
}

div[data-testid="stHorizontalBlock"] div[data-testid="column"] button[kind="secondary"] {
  border-radius: 999px;
  font-weight: 600;
  font-size: 0.78rem;
}
</style>
"""


def inject_styles() -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def display_name(row: pd.Series) -> str:
    raw_pid = row.get("plant_id")
    if pd.isna(raw_pid):
        return "Unknown plant"
    pid = int(raw_pid)
    return PLANT_NAMES.get(pid, row.get("plant_name") or f"Plant #{pid}")


def load_readings() -> pd.DataFrame:
    if not CSV_PATH.exists():
        st.error("`readings.csv` not found in the repo.")
        st.stop()

    if CSV_PATH.stat().st_size == 0:
        st.info(
            "The CSV file is empty. Run `./scripts/sync-readings.sh` after the Pi collects data."
        )
        st.stop()

    try:
        df = pd.read_csv(CSV_PATH)
    except EmptyDataError:
        st.info(
            "The CSV has no readable rows yet. Run `./scripts/sync-readings.sh` after the Pi collects data."
        )
        st.stop()

    if df.empty:
        st.info(
            "No readings in the CSV yet. Run `./scripts/sync-readings.sh` after the Pi collects data."
        )
        st.stop()

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        st.error(f"`readings.csv` is missing columns: {', '.join(sorted(missing))}")
        st.stop()

    df = df.dropna(subset=["plant_id", "timestamp", "moisture_percentage"])
    if df.empty:
        st.warning("No valid rows in the CSV after filtering bad data.")
        st.stop()

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])
    if df.empty:
        st.warning("All timestamps in the CSV were invalid.")
        st.stop()

    df["moisture_percentage"] = pd.to_numeric(df["moisture_percentage"], errors="coerce")
    df = df.dropna(subset=["moisture_percentage"])
    if "raw_value" in df.columns:
        df["raw_value"] = pd.to_numeric(df["raw_value"], errors="coerce")
    df["plant_id"] = pd.to_numeric(df["plant_id"], downcast="integer")
    df["plant_name"] = df.apply(display_name, axis=1)
    df["date"] = df["timestamp"].dt.date
    df["time_of_day"] = df["timestamp"].dt.strftime("%H:%M")
    df["hour_fraction"] = (
        df["timestamp"].dt.hour
        + df["timestamp"].dt.minute / 60
        + df["timestamp"].dt.second / 3600
    )
    return df.sort_values("timestamp")


def latest_per_plant(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.sort_values("timestamp")
        .groupby("plant_id", as_index=False)
        .last()
        .sort_values("plant_id")
    )


def badge_html(category: str) -> str:
    safe = html.escape(str(category))
    fg, bg = BADGE_STYLES.get(category, BADGE_STYLES["Unknown"])
    return f'<span class="badge" style="color:{fg};background:{bg}">{safe}</span>'


def plant_color(plant_id: int) -> str:
    return PLANT_COLORS.get(int(plant_id), PLANT_COLORS[((int(plant_id) - 1) % 4) + 1])


def plant_bar_gradient(plant_id: int) -> str:
    """Gauge fill matches plant identity color (green / purple / orange)."""
    base = plant_color(plant_id)
    lighter = {
        1: "#4caa6e",
        2: "#9b74c9",
        3: "#f0a05a",
        4: "#4a8fd4",
    }.get(int(plant_id), base)
    return f"linear-gradient(90deg, {lighter}, {base})"


def relative_time(ts: pd.Timestamp) -> str:
    diff_sec = int((pd.Timestamp.now() - ts).total_seconds())
    if diff_sec < 45:
        return "just now"
    if diff_sec < 3600:
        return f"{diff_sec // 60}m ago"
    if diff_sec < 86400:
        return f"{diff_sec // 3600}h ago"
    return f"{diff_sec // 86400}d ago"


def render_gauge_card(row: pd.Series, selected: bool = False) -> None:
    pct = float(row["moisture_percentage"])
    category = row.get("status_category", "Unknown")
    width = min(max(pct, 0), 100)
    selected_cls = " selected" if selected else ""
    name = html.escape(str(row["plant_name"]))
    when = html.escape(relative_time(row["timestamp"]))
    pid = int(row["plant_id"])
    swatch = plant_color(pid)
    blurb = PLANT_BLURBS.get(pid)
    blurb_html = ""
    if blurb:
        blurb_html = (
            f'<p class="gauge-blurb">{html.escape(blurb["about"])}'
            f'<span class="fact">{html.escape(blurb["fact"])}</span></p>'
        )
    st.markdown(
        f"""
        <div class="gauge-card{selected_cls}">
          <div class="gauge-top">
            <span class="gauge-name"><span class="plant-swatch" style="background:{swatch}"></span>{name}</span>
            <span class="gauge-pct">{pct:.1f}%</span>
          </div>
          <div class="gauge-bar">
            <div class="gauge-fill" style="width:{width}%;background:{plant_bar_gradient(pid)}"></div>
          </div>
          {blurb_html}
          <div style="display:flex;justify-content:space-between;align-items:center;">
            {badge_html(category)}
            <span style="font-size:0.72rem;color:#5a7262;">{when}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_legend() -> None:
    st.markdown(
        """
        <div class="legend">
          <span><i style="background:#c45c3e"></i> Dry ≤20%</span>
          <span><i style="background:#c4922a"></i> Moist ≤50%</span>
          <span><i style="background:#2d8a55"></i> Optimal ≤80%</span>
          <span><i style="background:#2a7a8a"></i> Soggy &gt;80%</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _band_rules() -> alt.Chart:
    return (
        alt.Chart(pd.DataFrame({"y": [20, 50, 80]}))
        .mark_rule(strokeDash=[4, 4], strokeWidth=1, color="rgba(45, 90, 61, 0.28)")
        .encode(y="y:Q")
    )


def day_chart(day_df: pd.DataFrame) -> alt.Chart:
    if day_df["plant_id"].nunique() > 1:
        return day_chart_multi(day_df)

    plant_id = int(day_df["plant_id"].iloc[0])
    line_color = plant_color(plant_id)

    nearest = alt.selection_point(
        nearest=True,
        on="pointerover",
        fields=["hour_fraction"],
        empty=False,
    )
    zoom = alt.selection_interval(bind="scales", encodings=["x"])

    base = (
        alt.Chart(day_df)
        .add_params(zoom)
        .encode(
            x=alt.X(
                "hour_fraction:Q",
                title="Hour (24h)",
                scale=alt.Scale(domain=[0, 24]),
                axis=alt.Axis(
                    values=list(range(0, 25, 3)),
                    labelExpr="pad(datum.value, 2, '0') + ':00'",
                ),
            ),
            y=alt.Y(
                "moisture_percentage:Q",
                title="Moisture %",
                scale=alt.Scale(domain=[0, 100]),
            ),
        )
    )

    area = base.mark_area(opacity=0.14, color=line_color, line=False)
    line = base.mark_line(color=line_color, strokeWidth=2.5)

    hover_points = (
        base.mark_circle(size=80, opacity=0)
        .encode(
            tooltip=[
                alt.Tooltip("time_of_day:N", title="Time"),
                alt.Tooltip("moisture_percentage:Q", title="Moisture %", format=".1f"),
                alt.Tooltip("raw_value:Q", title="Raw (ADC)", format="d"),
                alt.Tooltip("status_category:N", title="Status"),
            ],
        )
        .add_params(nearest)
    )

    latest_df = day_df.iloc[[-1]]
    latest_point = (
        alt.Chart(latest_df)
        .mark_circle(size=110, stroke="#fffbf5", strokeWidth=2)
        .encode(
            x="hour_fraction:Q",
            y="moisture_percentage:Q",
            color=alt.Color(
                "status_category:N",
                scale=alt.Scale(
                    domain=list(STATUS_COLORS.keys()),
                    range=list(STATUS_COLORS.values()),
                ),
                legend=alt.Legend(title="Status", orient="bottom"),
            ),
            tooltip=[
                alt.Tooltip("time_of_day:N", title="Time"),
                alt.Tooltip("moisture_percentage:Q", title="Moisture %", format=".1f"),
                alt.Tooltip("raw_value:Q", title="Raw (ADC)", format="d"),
                alt.Tooltip("status_category:N", title="Status"),
            ],
        )
    )

    mean_y = float(day_df["moisture_percentage"].mean())
    mean_rule = (
        alt.Chart(pd.DataFrame({"y": [mean_y]}))
        .mark_rule(color=line_color, strokeWidth=1.5, strokeDash=[6, 4], opacity=0.55)
        .encode(y="y:Q")
    )

    hover_rule = (
        base.transform_filter(nearest)
        .mark_rule(color="#5a7262", strokeWidth=1, opacity=0.45)
        .encode(x="hour_fraction:Q")
    )

    return (
        alt.layer(
            _band_rules(), area, line, mean_rule, hover_rule, hover_points, latest_point
        )
        .properties(height=280)
        .configure_view(strokeWidth=0)
        .configure_axis(
            gridColor="rgba(45, 90, 61, 0.1)",
            labelColor="#5a7262",
            titleColor="#5a7262",
        )
        .configure_legend(
            labelFont="Manrope",
            titleFont="Manrope",
            labelColor="#5a7262",
            titleColor="#5a7262",
        )
    )


def day_chart_multi(day_df: pd.DataFrame) -> alt.Chart:
    zoom = alt.selection_interval(bind="scales", encodings=["x"])
    names = list(day_df.sort_values("plant_id")["plant_name"].unique())
    ids = [
        int(day_df.loc[day_df["plant_name"] == name, "plant_id"].iloc[0]) for name in names
    ]
    colors = [plant_color(pid) for pid in ids]

    base = (
        alt.Chart(day_df)
        .add_params(zoom)
        .encode(
            x=alt.X(
                "hour_fraction:Q",
                title="Hour (24h)",
                scale=alt.Scale(domain=[0, 24]),
                axis=alt.Axis(
                    values=list(range(0, 25, 3)),
                    labelExpr="pad(datum.value, 2, '0') + ':00'",
                ),
            ),
            y=alt.Y(
                "moisture_percentage:Q",
                title="Moisture %",
                scale=alt.Scale(domain=[0, 100]),
            ),
            color=alt.Color(
                "plant_name:N",
                scale=alt.Scale(domain=names, range=colors),
                legend=alt.Legend(title="Plant", orient="bottom"),
            ),
        )
    )

    line = base.mark_line(strokeWidth=2.5)
    point_tooltip = [
        alt.Tooltip("plant_name:N", title="Plant"),
        alt.Tooltip("time_of_day:N", title="Time"),
        alt.Tooltip("moisture_percentage:Q", title="Moisture %", format=".1f"),
        alt.Tooltip("status_category:N", title="Status"),
        alt.Tooltip("raw_value:Q", title="Raw (ADC)", format="d"),
    ]
    points = base.mark_circle(size=55, opacity=0).encode(tooltip=point_tooltip)

    latest_rows = (
        day_df.sort_values("timestamp").groupby("plant_id", as_index=False).last()
    )
    latest_point = (
        alt.Chart(latest_rows)
        .mark_circle(size=100, stroke="#fffbf5", strokeWidth=2)
        .encode(
            x="hour_fraction:Q",
            y="moisture_percentage:Q",
            color=alt.Color(
                "plant_name:N",
                scale=alt.Scale(domain=names, range=colors),
                legend=None,
            ),
            tooltip=point_tooltip,
        )
    )

    return (
        alt.layer(_band_rules(), line, points, latest_point)
        .properties(height=300)
        .configure_view(strokeWidth=0)
        .configure_axis(
            gridColor="rgba(45, 90, 61, 0.1)",
            labelColor="#5a7262",
            titleColor="#5a7262",
        )
        .configure_legend(
            labelFont="Manrope",
            titleFont="Manrope",
            labelColor="#5a7262",
            titleColor="#5a7262",
            columns=2,
        )
    )


def day_stats_html(day_df: pd.DataFrame) -> str:
    avg = day_df["moisture_percentage"].mean()
    lo = day_df["moisture_percentage"].min()
    hi = day_df["moisture_percentage"].max()
    n = len(day_df)
    return f"""
    <div class="day-stats">
      <div class="day-stat"><span class="label">Avg</span><span class="value">{avg:.1f}%</span></div>
      <div class="day-stat"><span class="label">Low</span><span class="value">{lo:.1f}%</span></div>
      <div class="day-stat"><span class="label">High</span><span class="value">{hi:.1f}%</span></div>
      <div class="day-stat"><span class="label">Reads</span><span class="value">{n}</span></div>
    </div>
    """


def multi_day_stats_html(day_df: pd.DataFrame) -> str:
    cards = []
    for plant_id, group in day_df.groupby("plant_id", sort=True):
        name = html.escape(str(group["plant_name"].iloc[0]))
        swatch = plant_color(int(plant_id))
        avg = group["moisture_percentage"].mean()
        n = len(group)
        cards.append(
            f"""
            <div class="day-stat">
              <span class="label"><span class="plant-swatch" style="background:{swatch}"></span>{name}</span>
              <span class="value">{avg:.1f}%</span>
              <span style="font-size:0.65rem;color:#5a7262;">{n} reads</span>
            </div>
            """
        )
    return f'<div class="day-stats" style="grid-template-columns:repeat(auto-fit,minmax(120px,1fr));">{"".join(cards)}</div>'


def day_label(day, today=None) -> str:
    if today is None:
        today = pd.Timestamp.now().date()
    day = pd.Timestamp(day).date()
    ts = pd.Timestamp(day)
    pretty = ts.strftime("%b ") + str(ts.day) + ts.strftime(", %Y")
    if day == today:
        return f"Today · {pretty}"
    if day == today - pd.Timedelta(days=1):
        return f"Yesterday · {pretty}"
    return f"{ts.strftime('%a')} · {pretty}"


def short_day_label(day, today: date) -> str:
    day = pd.Timestamp(day).date()
    if day == today:
        return "Today"
    if day == today - pd.Timedelta(days=1):
        return "Yesterday"
    return pd.Timestamp(day).strftime("%a %b %d")


def render_day_chips(available_days: list, picked, counts: dict, today: date, day_key: str) -> None:
    recent = list(reversed(available_days[-7:]))
    if not recent:
        return
    cols = st.columns(len(recent))
    for col, d in zip(cols, recent):
        with col:
            label = f"{short_day_label(d, today)} · {counts.get(d, 0)}"
            if st.button(
                label,
                key=f"day_chip_{d}",
                use_container_width=True,
                type="primary" if d == picked else "secondary",
            ):
                st.session_state[day_key] = d
                st.rerun()


def render_hour_lists_html(day_df: pd.DataFrame, multi: bool) -> str:
    if not multi:
        rows = day_df.sort_values("timestamp", ascending=False)
        items = []
        for _, row in rows.iterrows():
            items.append(
                f"""
                <li>
                  <span class="time">{html.escape(str(row['time_of_day']))}</span>
                  {badge_html(str(row['status_category']))}
                  <span class="pct">{float(row['moisture_percentage']):.1f}%</span>
                </li>
                """
            )
        return f'<ul class="hour-list">{"".join(items)}</ul>'

    columns = []
    for plant_id, group in day_df.groupby("plant_id", sort=True):
        name = html.escape(str(group["plant_name"].iloc[0]))
        swatch = plant_color(int(plant_id))
        items = []
        for _, row in group.sort_values("timestamp", ascending=False).iterrows():
            items.append(
                f"""
                <li>
                  <span class="time">{html.escape(str(row['time_of_day']))}</span>
                  {badge_html(str(row['status_category']))}
                  <span class="pct">{float(row['moisture_percentage']):.1f}%</span>
                </li>
                """
            )
        columns.append(
            f"""
            <div class="hour-col">
              <div class="hour-col-head">
                <span class="plant-swatch" style="background:{swatch}"></span>
                <span title="{name}">{name}</span>
              </div>
              <ul class="hour-list">{"".join(items)}</ul>
            </div>
            """
        )
    return f'<div class="hour-columns">{"".join(columns)}</div>'


def init_plant_selection(names: list[str]) -> None:
    if "selected_plants" not in st.session_state:
        st.session_state.selected_plants = set(names)
        return
    st.session_state.selected_plants = {
        n for n in st.session_state.selected_plants if n in names
    }


def render_plant_toggles(names: list[str]) -> list[str]:
    init_plant_selection(names)
    selected = set(st.session_state.selected_plants)
    all_selected = bool(names) and selected.issuperset(names)

    cols = st.columns(len(names) + 1)
    for idx, name in enumerate(names):
        with cols[idx]:
            active = name in selected
            short = name.split()[0]
            if st.button(
                short,
                key=f"plant_toggle_{name}",
                use_container_width=True,
                type="primary" if active else "secondary",
            ):
                if active:
                    selected.discard(name)
                else:
                    selected.add(name)
                st.session_state.selected_plants = selected
                st.rerun()

    with cols[-1]:
        if st.button(
            "One" if all_selected else "All",
            key="toggle_all_plants",
            use_container_width=True,
        ):
            st.session_state.selected_plants = (
                {names[0]} if all_selected and names else set(names)
            )
            st.rerun()

    return [n for n in names if n in st.session_state.selected_plants]


def portfolio_dashboard(df: pd.DataFrame) -> None:
    latest = latest_per_plant(df)
    last_updated = df["timestamp"].max().strftime("%Y-%m-%d %H:%M")
    plant_options = dict(zip(latest["plant_name"], latest["plant_id"]))
    names = list(plant_options.keys())

    st.markdown(
        f"""
        <div class="intro">
          <p class="byline">Dulf’s Plant Hydration Hub</p>
          <p>
            Built to bring three threads together: a love of working with data,
            a growing interest in hardware and IoT, and expertise in visualization
            and web development — into one honest project: taking better care of
            the plants at home. ESP32 soil probes post to a Raspberry Pi that powers
            a live home PWA; this page is the <strong>public portfolio view</strong> —
            a curated CSV snapshot of real readings (last synced
            <strong>{last_updated}</strong>), not a live feed.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_status_legend()

    left, right = st.columns([1.55, 0.85], gap="medium")

    with right:
        with st.container(border=True):
            st.markdown('<p class="panel-title">Present hydration</p>', unsafe_allow_html=True)
            st.markdown(
                '<p class="panel-sub">Tap to multi-select · compare on the day chart</p>',
                unsafe_allow_html=True,
            )
            picked_plants = render_plant_toggles(names)
            selected_set = set(picked_plants)
            for _, row in latest.iterrows():
                render_gauge_card(row, selected=(row["plant_name"] in selected_set))

    with left:
        with st.container(border=True):
            st.markdown('<p class="panel-title">Day history</p>', unsafe_allow_html=True)
            st.markdown(
                '<p class="panel-sub">Multi-plant overlay · hover · drag to zoom</p>',
                unsafe_allow_html=True,
            )

            if not picked_plants:
                st.info("Select a plant to view its day chart.")
                return

            selected_ids = [plant_options[n] for n in picked_plants]
            plant_df = df[df["plant_id"].isin(selected_ids)]

            available_days = sorted(
                {pd.Timestamp(d).date() for d in plant_df["date"].dropna().unique()}
            )
            if not available_days:
                st.warning("No dated readings for the selected plants in the CSV snapshot.")
                return

            today = pd.Timestamp.now().date()
            day_key = "day_select_multi"
            if day_key not in st.session_state or st.session_state[day_key] not in available_days:
                st.session_state[day_key] = available_days[-1]

            day_counts = (
                plant_df.groupby("date").size().to_dict()
            )

            picked = st.session_state[day_key]
            render_day_chips(available_days, picked, day_counts, today, day_key)

            day_idx = available_days.index(st.session_state[day_key])
            prev_col, mid_col, next_col = st.columns([1, 4, 1], gap="small")
            with prev_col:
                if st.button(
                    "←",
                    disabled=day_idx <= 0,
                    use_container_width=True,
                    key="prev_day_multi",
                    help="Previous day with readings",
                ):
                    st.session_state[day_key] = available_days[day_idx - 1]
                    st.rerun()
            with mid_col:
                st.selectbox(
                    "Day",
                    available_days,
                    format_func=lambda d: day_label(d, today),
                    label_visibility="collapsed",
                    key=day_key,
                )
            with next_col:
                if st.button(
                    "→",
                    disabled=day_idx >= len(available_days) - 1,
                    use_container_width=True,
                    key="next_day_multi",
                    help="Next day with readings",
                ):
                    st.session_state[day_key] = available_days[day_idx + 1]
                    st.rerun()

            picked = st.session_state[day_key]
            if len(available_days) == 1:
                st.caption(
                    "Only one day in this CSV snapshot — sync more history from the Pi to browse other days."
                )
            else:
                st.caption(
                    f"Day {day_idx + 1} of {len(available_days)} with readings · use ← → or the menu"
                )

            day_df = plant_df[plant_df["date"] == picked].sort_values("timestamp")
            if day_df.empty:
                st.warning("No readings for this day in the CSV snapshot.")
            else:
                if len(selected_ids) == 1:
                    st.caption(f"{picked_plants[0]} · {day_label(picked, today)}")
                    st.markdown(day_stats_html(day_df), unsafe_allow_html=True)
                else:
                    st.caption(
                        f"{len(selected_ids)} plants · {day_label(picked, today)} · {len(day_df)} readings"
                    )
                    st.markdown(multi_day_stats_html(day_df), unsafe_allow_html=True)

                st.altair_chart(day_chart(day_df), use_container_width=True)
                st.markdown(
                    render_hour_lists_html(day_df, multi=len(selected_ids) > 1),
                    unsafe_allow_html=True,
                )


def main() -> None:
    st.set_page_config(
        page_title="Dulf’s Plant Hydration Hub",
        page_icon="🪴",
        layout="centered",
    )
    inject_styles()
    st.title("Plant Hydration Hub")
    st.caption("Built by Dulf · ESP32 · Raspberry Pi · Streamlit portfolio")

    df = load_readings()
    portfolio_dashboard(df)


if __name__ == "__main__":
    main()
