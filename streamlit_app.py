"""Portfolio plant dashboard — reads readings.csv committed to the repo."""

import html
import textwrap
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
.stApp {
  background:
    radial-gradient(ellipse 90% 60% at 10% -10%, #f4f9e8 0%, transparent 55%),
    radial-gradient(ellipse 70% 50% at 100% 0%, #cfe0c8 0%, transparent 50%),
    linear-gradient(165deg, #e8f0e6 0%, #d5e4d2 100%);
  background-attachment: fixed;
  font-family: 'Manrope', sans-serif;
  color: #1a2e22;
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

.block-container {
  max-width: 1100px;
  padding-top: 2.25rem !important;
  padding-bottom: 2.5rem;
  padding-left: 1.5rem !important;
  padding-right: 1.5rem !important;
  overflow: visible !important;
}

h1 {
  font-family: 'Fraunces', Georgia, serif !important;
  color: #2d5a3d !important;
  font-weight: 700 !important;
  letter-spacing: -0.02em;
  line-height: 1.2 !important;
  margin-top: 0.35rem !important;
  overflow: visible !important;
}

/* st.html iframes can clip wide content; keep HTML blocks fully visible */
div[data-testid="stHtml"],
div[data-testid="stMarkdown"] {
  width: 100% !important;
  max-width: 100% !important;
  overflow: visible !important;
}

div[data-testid="stHtml"] iframe {
  width: 100% !important;
  max-width: 100% !important;
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

p.gauge-blurb {
  margin: 0 0 0.4rem !important;
  font-size: 0.7rem !important;
  line-height: 1.35 !important;
  color: #5a7262 !important;
}

p.gauge-blurb .fact {
  display: block;
  margin-top: 0.15rem;
  font-size: inherit;
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
  margin: 0.75rem 0 0.85rem;
}

div[data-testid="stSegmentedControl"] {
  margin: 0.25rem 0 1rem;
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
  margin: 0.25rem 0 0.85rem;
  padding: 0.7rem 0.95rem;
  border-radius: 14px;
  border: 1px solid rgba(45, 90, 61, 0.14);
  background: rgba(255, 252, 247, 0.72);
  box-sizing: border-box;
  width: 100%;
  max-width: 100%;
  overflow: visible;
}

.intro p {
  margin: 0;
  font-size: 0.8rem;
  line-height: 1.45;
  color: #5a7262;
  white-space: normal;
  overflow-wrap: anywhere;
  word-wrap: break-word;
  max-width: 100%;
}

.day-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(5.5rem, 1fr));
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
  display: block;
  font-family: 'Fraunces', Georgia, serif;
  font-size: 1.15rem;
  font-weight: 700;
  color: #1a2e22;
}

.day-stat .sub {
  display: block;
  font-size: 0.62rem;
  color: #5a7262;
  margin-top: 0.1rem;
}

.trend-up { color: #2d8a55; }
.trend-down { color: #c45c3e; }
.trend-flat { color: #5a7262; }

.status-mix-block {
  margin-top: 0.85rem;
}

.status-mix-block h4 {
  margin: 0 0 0.55rem;
  font-family: 'Fraunces', Georgia, serif;
  font-size: 0.95rem;
  font-weight: 600;
  color: #1a2e22;
}

.status-bar {
  display: flex;
  height: 10px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(45, 90, 61, 0.08);
  margin-bottom: 0.35rem;
}

.status-bar span {
  display: block;
  height: 100%;
  min-width: 2px;
}

.status-bar-legend {
  font-size: 0.68rem;
  color: #5a7262;
  margin-bottom: 0.65rem;
}

.watering-note {
  margin: 0.65rem 0 0;
  font-size: 0.78rem;
  color: #5a7262;
  padding: 0.55rem 0.7rem;
  border-radius: 10px;
  background: rgba(196, 224, 122, 0.18);
  border: 1px solid rgba(45, 90, 61, 0.12);
}

.plant-swatch {
  display: inline-block;
  width: 0.55rem;
  height: 0.55rem;
  border-radius: 50%;
  margin-right: 0.35rem;
  vertical-align: middle;
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
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 0.35rem;
  padding: 0.4rem 0.45rem;
  border-radius: 10px;
  background: rgba(255, 252, 247, 0.65);
  border: 1px solid rgba(45, 90, 61, 0.12);
  font-size: 0.78rem;
  min-width: 0;
}

.hour-list .time {
  font-weight: 700;
  color: #2d5a3d;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.hour-list .badge {
  justify-self: start;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hour-list .pct {
  font-family: 'Fraunces', Georgia, serif;
  font-weight: 700;
  font-size: 0.88rem;
  white-space: nowrap;
}

div[data-testid="stHorizontalBlock"] div[data-testid="column"] button {
  border-radius: 999px !important;
  font-weight: 600;
  font-size: 0.78rem !important;
  white-space: nowrap !important;
}

div[data-testid="stHorizontalBlock"] div[data-testid="column"] button p {
  white-space: nowrap !important;
  overflow: hidden;
  text-overflow: ellipsis;
}

div[data-testid="stHorizontalBlock"] div[data-testid="column"] button[kind="secondary"] {
  border-radius: 999px;
  font-weight: 600;
  font-size: 0.78rem;
}

div[data-testid="stCaptionContainer"] p {
  font-size: 0.76rem !important;
  line-height: 1.4 !important;
  margin-top: 0.15rem !important;
}

@media (max-width: 700px) {
  .block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
  }

  h1 {
    font-size: 1.65rem !important;
    margin-bottom: 0.15rem !important;
  }

  .legend {
    gap: 0.35rem;
    margin: 0.55rem 0 0.75rem;
  }

  .legend span {
    font-size: 0.68rem;
    padding: 0.26rem 0.5rem;
  }

  .panel-sub {
    margin-bottom: 0.55rem;
  }

  div[data-testid="stHorizontalBlock"]:has([data-testid="stVerticalBlockBorderWrapper"]) {
    flex-direction: column !important;
    gap: 0.85rem !important;
  }

  div[data-testid="stHorizontalBlock"]:has([data-testid="stVerticalBlockBorderWrapper"])
    > div[data-testid="column"] {
    width: 100% !important;
    flex: 1 1 100% !important;
    min-width: 0 !important;
  }

  div[data-testid="stHorizontalBlock"]:has([data-testid="stVerticalBlockBorderWrapper"])
    > div[data-testid="column"]:nth-child(2) {
    order: -1;
  }

  div:has(> .day-chips-anchor) + div {
    display: none !important;
  }
}
</style>
"""


def render_html(body: str) -> None:
    """Render HTML in the main doc so app CSS applies (avoids st.html clip/iframe)."""
    cleaned = textwrap.dedent(body).strip()
    # Collapse leading indentation so Markdown won't treat tags as code fences.
    compact = "\n".join(line.lstrip() for line in cleaned.splitlines())
    st.markdown(compact, unsafe_allow_html=True)


def inject_styles() -> None:
    # Non-blocking font load (avoids @import inside CSS delaying first paint).
    st.markdown(
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700'
        '&family=Manrope:wght@400;500;600;700&display=swap" rel="stylesheet">',
        unsafe_allow_html=True,
    )
    render_html(CUSTOM_CSS)


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
    render_html(
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
        """
    )


def render_status_legend() -> None:
    render_html(
        """
        <div class="legend">
          <span><i style="background:#c45c3e"></i> Dry ≤20%</span>
          <span><i style="background:#c4922a"></i> Moist ≤50%</span>
          <span><i style="background:#2d8a55"></i> Optimal ≤80%</span>
          <span><i style="background:#2a7a8a"></i> Soggy &gt;80%</span>
        </div>
        """
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
                    labelExpr="slice('0' + datum.value, -2) + ':00'",
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
                    labelExpr="slice('0' + datum.value, -2) + ':00'",
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
                legend=None,
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
        .properties(height=260)
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


def build_daily_summary(plant_df: pd.DataFrame) -> pd.DataFrame:
    """One row per plant per calendar day with avg/min/max."""
    daily = (
        plant_df.groupby(["plant_id", "plant_name", "date"], as_index=False)
        .agg(
            avg_moisture=("moisture_percentage", "mean"),
            min_moisture=("moisture_percentage", "min"),
            max_moisture=("moisture_percentage", "max"),
            reading_count=("moisture_percentage", "count"),
        )
        .sort_values(["plant_id", "date"])
    )
    daily["avg_moisture"] = daily["avg_moisture"].round(1)
    daily["min_moisture"] = daily["min_moisture"].round(1)
    daily["max_moisture"] = daily["max_moisture"].round(1)
    return daily


def filter_daily_range(daily_df: pd.DataFrame, range_key: str) -> pd.DataFrame:
    if daily_df.empty:
        return daily_df
    dates = sorted(daily_df["date"].unique())
    if range_key == "7":
        keep = set(dates[-7:])
    elif range_key == "14":
        keep = set(dates[-14:])
    else:
        keep = set(dates)
    return daily_df[daily_df["date"].isin(keep)].copy()


def _trends_day_axis(daily_df: pd.DataFrame) -> alt.X:
    """One tick label per calendar day (avoids Altair's half-day duplicate labels)."""
    dates = sorted(pd.to_datetime(daily_df["date"]).dt.normalize().unique())
    if len(dates) > 14:
        step = max(1, (len(dates) - 1) // 10)
        tick_values = list(dates[::step])
        if tick_values[-1] != dates[-1]:
            tick_values.append(dates[-1])
    else:
        tick_values = list(dates)

    return alt.X(
        "yearmonthdate(date):T",
        title="Day",
        axis=alt.Axis(
            format="%b %d",
            labelAngle=-35,
            values=tick_values,
            labelOverlap=True,
            tickCount=len(tick_values),
        ),
    )


def _trends_y_axis() -> alt.Y:
    return alt.Y(
        "avg_moisture:Q",
        title="Moisture %",
        scale=alt.Scale(domain=[0, 100]),
    )


def daily_trends_chart(daily_df: pd.DataFrame) -> alt.Chart:
    if daily_df.empty:
        return alt.Chart(pd.DataFrame()).mark_point()

    daily_df = daily_df.copy()
    daily_df["date"] = pd.to_datetime(daily_df["date"]).dt.normalize()
    x_enc = _trends_day_axis(daily_df)
    y_enc = _trends_y_axis()

    if daily_df["plant_id"].nunique() > 1:
        names = list(daily_df.sort_values("plant_id")["plant_name"].unique())
        ids = [
            int(daily_df.loc[daily_df["plant_name"] == name, "plant_id"].iloc[0])
            for name in names
        ]
        colors = [plant_color(pid) for pid in ids]
        base = alt.Chart(daily_df).encode(
            x=x_enc,
            y=y_enc,
            color=alt.Color(
                "plant_name:N",
                scale=alt.Scale(domain=names, range=colors),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("plant_name:N", title="Plant"),
                alt.Tooltip("date:T", title="Day", format="%b %d, %Y"),
                alt.Tooltip("avg_moisture:Q", title="Avg %", format=".1f"),
                alt.Tooltip("min_moisture:Q", title="Low %", format=".1f"),
                alt.Tooltip("max_moisture:Q", title="High %", format=".1f"),
                alt.Tooltip("reading_count:Q", title="Reads"),
            ],
        )
        line = base.mark_line(strokeWidth=2.5)
        points = base.mark_circle(size=60)
        return (
            alt.layer(_band_rules(), line, points)
            .properties(height=280)
            .configure_view(strokeWidth=0)
            .configure_axis(
                gridColor="rgba(45, 90, 61, 0.1)",
                labelColor="#5a7262",
                titleColor="#5a7262",
            )
        )

    plant_id = int(daily_df["plant_id"].iloc[0])
    line_color = plant_color(plant_id)
    base = alt.Chart(daily_df).encode(x=x_enc, y=y_enc)
    band = (
        alt.Chart(daily_df)
        .mark_area(opacity=0.14, color=line_color)
        .encode(
            x=x_enc,
            y="min_moisture:Q",
            y2="max_moisture:Q",
        )
    )
    line = base.mark_line(color=line_color, strokeWidth=2.5)
    points = base.mark_circle(color=line_color, size=60).encode(
        tooltip=[
            alt.Tooltip("date:T", title="Day", format="%b %d, %Y"),
            alt.Tooltip("avg_moisture:Q", title="Avg %", format=".1f"),
            alt.Tooltip("min_moisture:Q", title="Low %", format=".1f"),
            alt.Tooltip("max_moisture:Q", title="High %", format=".1f"),
            alt.Tooltip("reading_count:Q", title="Reads"),
        ],
    )
    return (
        alt.layer(_band_rules(), band, line, points)
        .properties(height=280)
        .configure_view(strokeWidth=0)
        .configure_axis(
            gridColor="rgba(45, 90, 61, 0.1)",
            labelColor="#5a7262",
            titleColor="#5a7262",
        )
    )


def compute_trends_insights(
    daily_df: pd.DataFrame, plant_df: pd.DataFrame
) -> dict | None:
    if daily_df.empty:
        return None

    dates = sorted(daily_df["date"].unique())
    subset = plant_df[plant_df["date"].isin(dates)]
    total_count = len(subset)
    if total_count == 0:
        return None

    overall_avg = float(daily_df["avg_moisture"].mean())
    status_totals = subset["status_category"].value_counts().to_dict()
    optimal_pct = round(
        (status_totals.get("Optimal", 0) / total_count) * 100
    )

    driest_avg = float(daily_df["avg_moisture"].min())
    driest_date = pd.Timestamp(
        daily_df.loc[daily_df["avg_moisture"].idxmin(), "date"]
    )

    trend_text = "—"
    trend_class = "trend-flat"
    if len(dates) >= 4:
        half = len(dates) // 2
        first_dates = set(dates[:half])
        second_dates = set(dates[half:])
        first_mean = float(
            daily_df[daily_df["date"].isin(first_dates)]["avg_moisture"].mean()
        )
        second_mean = float(
            daily_df[daily_df["date"].isin(second_dates)]["avg_moisture"].mean()
        )
        delta = second_mean - first_mean
        if abs(delta) < 2:
            trend_text = "Flat"
        elif delta > 0:
            trend_text = f"↑ {delta:.1f}%"
            trend_class = "trend-up"
        else:
            trend_text = f"↓ {abs(delta):.1f}%"
            trend_class = "trend-down"

    return {
        "overall_avg": overall_avg,
        "optimal_pct": optimal_pct,
        "driest_date": driest_date,
        "driest_avg": driest_avg,
        "trend_text": trend_text,
        "trend_class": trend_class,
        "status_totals": status_totals,
        "total_count": total_count,
    }


def trends_insights_html(insights: dict | None) -> str:
    if not insights:
        return ""
    driest_label = insights["driest_date"].strftime("%b %d")
    return (
        '<div class="day-stats">'
        f'<div class="day-stat"><span class="label">Range avg</span>'
        f'<span class="value">{insights["overall_avg"]:.1f}%</span></div>'
        f'<div class="day-stat"><span class="label">Trend</span>'
        f'<span class="value {insights["trend_class"]}">{insights["trend_text"]}</span>'
        f'<span class="sub">vs prior half</span></div>'
        f'<div class="day-stat"><span class="label">Optimal</span>'
        f'<span class="value">{insights["optimal_pct"]}%</span>'
        f'<span class="sub">of readings</span></div>'
        f'<div class="day-stat"><span class="label">Driest day</span>'
        f'<span class="value">{insights["driest_avg"]:.1f}%</span>'
        f'<span class="sub">{driest_label}</span></div>'
        "</div>"
    )


def status_mix_html(
    daily_df: pd.DataFrame, plant_df: pd.DataFrame, insights: dict | None
) -> str:
    if not insights or not insights["total_count"]:
        return ""

    dates = sorted(daily_df["date"].unique())
    status_colors = STATUS_COLORS
    rows = []

    if daily_df["plant_id"].nunique() > 1:
        for plant_id, group in daily_df.groupby("plant_id", sort=True):
            name = html.escape(str(group["plant_name"].iloc[0]))
            swatch = plant_color(int(plant_id))
            subset = plant_df[
                (plant_df["plant_id"] == plant_id) & (plant_df["date"].isin(dates))
            ]
            totals = subset["status_category"].value_counts().to_dict()
            count = len(subset)
            if not count:
                continue
            rows.append(
                _one_status_bar_html(name, swatch, totals, count, status_colors)
            )
    else:
        rows.append(
            _one_status_bar_html(
                "Status mix",
                None,
                insights["status_totals"],
                insights["total_count"],
                status_colors,
            )
        )

    return (
        '<div class="status-mix-block"><h4>Status mix</h4>'
        f'{"".join(rows)}</div>'
    )


def _one_status_bar_html(
    label: str,
    swatch: str | None,
    totals: dict,
    count: int,
    status_colors: dict,
) -> str:
    segments = []
    legend_parts = []
    for cat in ["Dry", "Moist", "Optimal", "Soggy"]:
        n = totals.get(cat, 0)
        if n <= 0:
            continue
        pct = (n / count) * 100
        segments.append(
            f'<span style="width:{pct:.1f}%;background:{status_colors[cat]}"></span>'
        )
        legend_parts.append(f"{cat} {round(pct)}%")
    swatch_html = (
        f'<span class="plant-swatch" style="background:{swatch}"></span>'
        if swatch
        else ""
    )
    return (
        '<div class="status-mix-row">'
        f'<div class="hour-col-head">{swatch_html}{label}</div>'
        f'<div class="status-bar">{"".join(segments)}</div>'
        f'<div class="status-bar-legend">{" · ".join(legend_parts)}</div>'
        "</div>"
    )


def detect_watering_notes(daily_df: pd.DataFrame) -> str:
    notes = []
    for plant_id, group in daily_df.groupby("plant_id", sort=True):
        group = group.sort_values("date")
        name = str(group["plant_name"].iloc[0])
        avgs = group["avg_moisture"].tolist()
        dates = group["date"].tolist()
        for i in range(1, len(avgs)):
            jump = avgs[i] - avgs[i - 1]
            if jump >= 15:
                d = pd.Timestamp(dates[i]).strftime("%b %d")
                notes.append(f"{name}: {d} (+{jump:.0f}%)")
    if not notes:
        return ""
    return (
        f'<p class="watering-note">Likely watered: {html.escape(" · ".join(notes))}</p>'
    )


def render_today_panel(
    plant_df: pd.DataFrame,
    picked_plants: list[str],
    plant_options: dict[str, int],
    today: date,
) -> None:
    render_html('<p class="panel-title">Day history</p>')
    render_html(
        '<p class="panel-sub">Multi-plant overlay · hover · drag to zoom</p>'
    )

    if not picked_plants:
        st.info("Select a plant to view its day chart.")
        return

    selected_ids = [plant_options[n] for n in picked_plants]
    scoped_df = plant_df[plant_df["plant_id"].isin(selected_ids)]

    available_days = sorted(
        {pd.Timestamp(d).date() for d in scoped_df["date"].dropna().unique()}
    )
    if not available_days:
        st.warning("No dated readings for the selected plants in the CSV snapshot.")
        return

    day_key = "day_select_multi"
    if day_key not in st.session_state or st.session_state[day_key] not in available_days:
        st.session_state[day_key] = available_days[-1]
    st.session_state["_nav_days"] = available_days

    day_counts = scoped_df.groupby("date").size().to_dict()
    picked = st.session_state[day_key]
    render_day_chips(available_days, picked, day_counts, today, day_key)

    day_idx = available_days.index(st.session_state[day_key])
    prev_col, mid_col, next_col = st.columns([1, 4, 1], gap="small")
    with prev_col:
        st.button(
            "←",
            disabled=day_idx <= 0,
            use_container_width=True,
            key="prev_day_multi",
            help="Previous day with readings",
            on_click=_nudge_day,
            args=(day_key, -1),
        )
    with mid_col:
        st.selectbox(
            "Day",
            available_days,
            format_func=lambda d: day_label(d, today),
            label_visibility="collapsed",
            key=day_key,
        )
    with next_col:
        st.button(
            "→",
            disabled=day_idx >= len(available_days) - 1,
            use_container_width=True,
            key="next_day_multi",
            help="Next day with readings",
            on_click=_nudge_day,
            args=(day_key, 1),
        )

    picked = st.session_state[day_key]
    if len(available_days) == 1:
        st.caption(
            "Only one day in this CSV snapshot — sync more history from the Pi to browse other days."
        )
    else:
        st.caption(
            f"Day {day_idx + 1} of {len(available_days)} with readings · use ← → or the menu"
        )

    day_df = scoped_df[scoped_df["date"] == picked].sort_values("timestamp")
    if day_df.empty:
        st.warning("No readings for this day in the CSV snapshot.")
        return

    if len(selected_ids) == 1:
        st.caption(f"{picked_plants[0]} · {day_label(picked, today)}")
        render_html(day_stats_html(day_df))
    else:
        st.caption(
            f"{len(selected_ids)} plants · {day_label(picked, today)} · {len(day_df)} readings"
        )
        render_html(multi_day_stats_html(day_df))

    st.altair_chart(day_chart(day_df), use_container_width=True)
    render_html(render_hour_lists_html(day_df, multi=len(selected_ids) > 1))


def render_trends_panel(
    plant_df: pd.DataFrame,
    picked_plants: list[str],
    plant_options: dict[str, int],
) -> None:
    render_html('<p class="panel-title">Daily trends</p>')
    render_html(
        '<p class="panel-sub">Daily average moisture · range band for one plant</p>'
    )

    if not picked_plants:
        st.info("Select a plant to view daily trends.")
        return

    selected_ids = [plant_options[n] for n in picked_plants]
    scoped_df = plant_df[plant_df["plant_id"].isin(selected_ids)]
    daily_all = build_daily_summary(scoped_df)
    if daily_all.empty:
        st.warning("Not enough history for trends yet.")
        return

    range_key = st.segmented_control(
        "Range",
        options=["7", "14", "all"],
        format_func=lambda x: {"7": "7 days", "14": "14 days", "all": "All"}[x],
        default="all",
        label_visibility="collapsed",
        key="trends_range",
    )
    daily_df = filter_daily_range(daily_all, range_key or "all")
    if daily_df.empty:
        st.warning("No readings in the selected range.")
        return

    n_days = daily_df["date"].nunique()
    if len(selected_ids) == 1:
        st.caption(f"{picked_plants[0]} · {n_days} day{'s' if n_days != 1 else ''}")
    else:
        st.caption(
            f"{len(selected_ids)} plants · {n_days} day{'s' if n_days != 1 else ''}"
        )

    insights = compute_trends_insights(daily_df, scoped_df)
    render_html(trends_insights_html(insights))
    st.altair_chart(daily_trends_chart(daily_df), use_container_width=True)
    render_html(status_mix_html(daily_df, scoped_df, insights))
    watering = detect_watering_notes(daily_df)
    if watering:
        render_html(watering)


def day_stats_html(day_df: pd.DataFrame) -> str:
    avg = day_df["moisture_percentage"].mean()
    lo = day_df["moisture_percentage"].min()
    hi = day_df["moisture_percentage"].max()
    n = len(day_df)
    return (
        '<div class="day-stats">'
        f'<div class="day-stat"><span class="label">Avg</span><span class="value">{avg:.1f}%</span></div>'
        f'<div class="day-stat"><span class="label">Low</span><span class="value">{lo:.1f}%</span></div>'
        f'<div class="day-stat"><span class="label">High</span><span class="value">{hi:.1f}%</span></div>'
        f'<div class="day-stat"><span class="label">Reads</span><span class="value">{n}</span></div>'
        "</div>"
    )


def multi_day_stats_html(day_df: pd.DataFrame) -> str:
    cards = []
    for plant_id, group in day_df.groupby("plant_id", sort=True):
        name = html.escape(str(group["plant_name"].iloc[0]))
        swatch = plant_color(int(plant_id))
        avg = group["moisture_percentage"].mean()
        cards.append(
            '<div class="day-stat">'
            f'<span class="label"><span class="plant-swatch" style="background:{swatch}"></span>{name}</span>'
            f'<span class="value">{avg:.1f}%</span>'
            "</div>"
        )
    return (
        '<div class="day-stats" style="grid-template-columns:repeat(auto-fit,minmax(120px,1fr));">'
        f'{"".join(cards)}'
        "</div>"
    )


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


def _set_day(day_key: str, day: date) -> None:
    """Callback: set selected day before widgets instantiate on the next run."""
    st.session_state[day_key] = day


def _nudge_day(day_key: str, delta: int) -> None:
    """Callback: step ←/→ across days stored for navigation."""
    days = st.session_state.get("_nav_days")
    current = st.session_state.get(day_key)
    if not days or current not in days:
        return
    idx = days.index(current)
    new_idx = idx + delta
    if 0 <= new_idx < len(days):
        st.session_state[day_key] = days[new_idx]


def render_day_chips(available_days: list, picked, counts: dict, today: date, day_key: str) -> None:
    recent = list(reversed(available_days[-7:]))
    # With only one day, the chip duplicates the selectbox and reads like "Yesterday · 3".
    if not recent or len(available_days) <= 1:
        return
    render_html('<div class="day-chips-anchor" aria-hidden="true"></div>')
    cols = st.columns(len(recent))
    for col, d in zip(cols, recent):
        with col:
            label = f"{short_day_label(d, today)} · {counts.get(d, 0)}"
            st.button(
                label,
                key=f"day_chip_{d}",
                use_container_width=True,
                type="primary" if d == picked else "secondary",
                on_click=_set_day,
                args=(day_key, d),
            )


def render_hour_lists_html(day_df: pd.DataFrame, multi: bool) -> str:
    if not multi:
        rows = day_df.sort_values("timestamp", ascending=False)
        items = []
        for _, row in rows.iterrows():
            items.append(
                "<li>"
                f'<span class="time">{html.escape(str(row["time_of_day"]))}</span>'
                f'{badge_html(str(row["status_category"]))}'
                f'<span class="pct">{float(row["moisture_percentage"]):.1f}%</span>'
                "</li>"
            )
        return f'<ul class="hour-list">{"".join(items)}</ul>'

    columns = []
    for plant_id, group in day_df.groupby("plant_id", sort=True):
        name = html.escape(str(group["plant_name"].iloc[0]))
        swatch = plant_color(int(plant_id))
        items = []
        for _, row in group.sort_values("timestamp", ascending=False).iterrows():
            items.append(
                "<li>"
                f'<span class="time">{html.escape(str(row["time_of_day"]))}</span>'
                f'{badge_html(str(row["status_category"]))}'
                f'<span class="pct">{float(row["moisture_percentage"]):.1f}%</span>'
                "</li>"
            )
        columns.append(
            '<div class="hour-col">'
            '<div class="hour-col-head">'
            f'<span class="plant-swatch" style="background:{swatch}"></span>'
            f'<span title="{name}">{name}</span>'
            "</div>"
            f'<ul class="hour-list">{"".join(items)}</ul>'
            "</div>"
        )
    return f'<div class="hour-columns">{"".join(columns)}</div>'


def plant_toggle_label(name: str) -> str:
    """Short label that fits narrow Streamlit columns without mid-word wrap."""
    parts = name.split()
    if not parts:
        return name
    # Prefer species epithet when genus is long (Tradescantia → Zebrina).
    if len(parts[0]) > 8 and len(parts) > 1:
        return parts[1]
    return parts[0]


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

    shorts = [plant_toggle_label(name) for name in names]

    cols = st.columns(3)
    for idx, name in enumerate(names):
        with cols[idx % 3]:
            active = name in selected
            if st.button(
                shorts[idx],
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

    all_label = "One" if all_selected else "All"
    if st.button(
        all_label,
        key="toggle_all_plants",
        use_container_width=True,
        type="secondary",
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

    intro_html = (
        '<div class="intro"><p>'
        "Built to bring three threads together: a love of working with data, "
        "a growing interest in hardware and IoT, and expertise in visualization "
        "and web development — into one honest project: taking better care of "
        "the plants at home. ESP32 soil probes post to a Raspberry Pi that powers "
        "a live home PWA; this page is the <strong>public portfolio view</strong> — "
        "a curated CSV snapshot of real readings (last synced "
        f"<strong>{last_updated}</strong>), not a live feed."
        "</p></div>"
    )
    render_html(intro_html)

    render_status_legend()

    init_plant_selection(names)

    view = st.segmented_control(
        "View",
        options=["Today", "Trends"],
        default="Today",
        label_visibility="collapsed",
        key="dashboard_view",
    )

    left, right = st.columns([1.55, 0.85], gap="medium")
    today = pd.Timestamp.now().date()

    with right:
        with st.container(border=True):
            render_html('<p class="panel-title">Present hydration</p>')
            render_html(
                '<p class="panel-sub">Use buttons to multi-select · compare on charts</p>'
            )
            picked_plants = render_plant_toggles(names)
            selected_set = set(picked_plants)
            for _, row in latest.iterrows():
                render_gauge_card(row, selected=(row["plant_name"] in selected_set))

    with left:
        with st.container(border=True):
            if view == "Trends":
                render_trends_panel(df, picked_plants, plant_options)
            else:
                render_today_panel(df, picked_plants, plant_options, today)


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
