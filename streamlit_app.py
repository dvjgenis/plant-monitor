"""Portfolio plant dashboard — reads readings.csv committed to the repo."""

import html
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
    2: "Plant #2",
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

html, body, [class*="css"] {
  font-family: 'Manrope', sans-serif;
  color: #1a2e22;
}

.block-container {
  max-width: 920px;
  padding-top: 1.5rem;
  padding-bottom: 2.5rem;
}

h1 {
  font-family: 'Fraunces', Georgia, serif !important;
  color: #2d5a3d !important;
  font-weight: 700 !important;
  letter-spacing: -0.02em;
}

.panel {
  background: rgba(255, 252, 247, 0.82);
  border: 1px solid rgba(45, 90, 61, 0.14);
  border-radius: 22px;
  padding: 1.1rem 1.2rem 1.25rem;
  box-shadow: 0 18px 40px rgba(26, 46, 34, 0.08);
  margin-bottom: 0.5rem;
}

.panel h3 {
  font-family: 'Fraunces', Georgia, serif;
  font-size: 1.1rem;
  margin: 0 0 0.15rem;
  color: #1a2e22;
}

.panel .sub {
  font-size: 0.78rem;
  color: #5a7262;
  margin-bottom: 0.85rem;
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
  box-shadow: 0 0 0 2px rgba(196, 224, 122, 0.55);
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
  font-size: 0.72rem;
  font-weight: 600;
  color: #5a7262;
  padding: 0.3rem 0.6rem;
  border-radius: 999px;
  border: 1px solid rgba(45, 90, 61, 0.14);
  background: rgba(255, 252, 247, 0.55);
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

.snapshot-note {
  font-size: 0.78rem;
  color: #5a7262;
  margin: 0 0 1rem;
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


def bar_gradient(category: str) -> str:
    colors = {
        "Dry": "linear-gradient(90deg, #d97858, #c45c3e)",
        "Moist": "linear-gradient(90deg, #e0b34d, #c4922a)",
        "Optimal": "linear-gradient(90deg, #5cbc7d, #2d8a55)",
        "Soggy": "linear-gradient(90deg, #4ea8b8, #2a7a8a)",
    }
    return colors.get(category, colors["Dry"])


def render_gauge_card(row: pd.Series, selected: bool = False) -> None:
    pct = float(row["moisture_percentage"])
    category = row.get("status_category", "Unknown")
    width = min(max(pct, 0), 100)
    selected_cls = " selected" if selected else ""
    name = html.escape(str(row["plant_name"]))
    time_label = html.escape(str(row["time_of_day"]))
    st.markdown(
        f"""
        <div class="gauge-card{selected_cls}">
          <div class="gauge-top">
            <span class="gauge-name">{name}</span>
            <span class="gauge-pct">{pct:.1f}%</span>
          </div>
          <div class="gauge-bar">
            <div class="gauge-fill" style="width:{width}%;background:{bar_gradient(category)}"></div>
          </div>
          <div style="display:flex;justify-content:space-between;align-items:center;">
            {badge_html(category)}
            <span style="font-size:0.72rem;color:#5a7262;">Updated {time_label}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def day_chart(day_df: pd.DataFrame) -> alt.Chart:
    """Layered Altair chart: band guides, area, line, status-colored points, hover + zoom."""
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

    band_rules = (
        alt.Chart(pd.DataFrame({"y": [20, 50, 80]}))
        .mark_rule(strokeDash=[4, 4], strokeWidth=1, color="rgba(45, 90, 61, 0.28)")
        .encode(y="y:Q")
    )

    area = base.mark_area(opacity=0.14, color="#2d8a55", line=False)
    line = base.mark_line(color="#2d5a3d", strokeWidth=2.5)

    points = (
        base.mark_circle(size=70)
        .encode(
            color=alt.Color(
                "status_category:N",
                scale=alt.Scale(
                    domain=list(STATUS_COLORS.keys()),
                    range=list(STATUS_COLORS.values()),
                ),
                legend=alt.Legend(title="Status", orient="bottom"),
            ),
            size=alt.condition(nearest, alt.value(140), alt.value(70)),
            tooltip=[
                alt.Tooltip("time_of_day:N", title="Time"),
                alt.Tooltip("moisture_percentage:Q", title="Moisture %", format=".1f"),
                alt.Tooltip("status_category:N", title="Status"),
            ],
        )
        .add_params(nearest)
    )

    mean_y = float(day_df["moisture_percentage"].mean())
    mean_rule = (
        alt.Chart(pd.DataFrame({"y": [mean_y]}))
        .mark_rule(color="#2d5a3d", strokeWidth=1.5, strokeDash=[6, 4], opacity=0.55)
        .encode(y="y:Q")
    )

    hover_rule = (
        base.transform_filter(nearest)
        .mark_rule(color="#5a7262", strokeWidth=1, opacity=0.45)
        .encode(x="hour_fraction:Q")
    )

    return (
        alt.layer(band_rules, area, line, mean_rule, hover_rule, points)
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


def portfolio_dashboard(df: pd.DataFrame) -> None:
    latest = latest_per_plant(df)
    last_updated = df["timestamp"].max().strftime("%Y-%m-%d %H:%M")
    plant_options = dict(zip(latest["plant_name"], latest["plant_id"]))
    names = list(plant_options.keys())

    if "selected_plant" not in st.session_state:
        st.session_state.selected_plant = names[0]
    if st.session_state.selected_plant not in names:
        st.session_state.selected_plant = names[0]

    st.markdown(
        f"""
        <div class="intro">
          <p class="byline">Dulf’s Plant Hydration Hub</p>
          <p>
            A personal IoT build: ESP32 soil probes post moisture to a Raspberry Pi,
            which powers a live home PWA. This page is the <strong>public portfolio view</strong> —
            a curated CSV snapshot of real readings (last synced
            <strong>{last_updated}</strong>), not a live feed.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="legend">
          <span>Dry ≤20%</span>
          <span>Moist ≤50%</span>
          <span>Optimal ≤80%</span>
          <span>Soggy &gt;80%</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.55, 0.85], gap="medium")

    with right:
        st.markdown(
            '<div class="panel"><h3>Present hydration</h3>'
            '<div class="sub">Select a plant to drive the day chart</div>',
            unsafe_allow_html=True,
        )
        picked_plant = st.radio(
            "Plant",
            names,
            index=names.index(st.session_state.selected_plant),
            label_visibility="collapsed",
            key="plant_radio",
        )
        st.session_state.selected_plant = picked_plant
        for _, row in latest.iterrows():
            render_gauge_card(row, selected=(row["plant_name"] == picked_plant))
        st.markdown("</div>", unsafe_allow_html=True)

    with left:
        st.markdown(
            '<div class="panel"><h3>Day history</h3>'
            '<div class="sub">Hover points · drag horizontally to zoom hours</div>',
            unsafe_allow_html=True,
        )

        selected_name = st.session_state.selected_plant
        plant_id = plant_options[selected_name]
        plant_df = df[df["plant_id"] == plant_id]

        min_day = plant_df["date"].min()
        max_day = plant_df["date"].max()
        picked = st.date_input(
            "Day",
            value=max_day,
            min_value=min_day,
            max_value=max_day,
            label_visibility="collapsed",
        )

        day_df = plant_df[plant_df["date"] == picked].sort_values("timestamp")
        if day_df.empty:
            st.warning("No readings for this day in the CSV snapshot.")
        else:
            st.caption(f"{selected_name} · {picked}")
            st.markdown(day_stats_html(day_df), unsafe_allow_html=True)
            st.altair_chart(day_chart(day_df), use_container_width=True)

            table = day_df[
                ["time_of_day", "moisture_percentage", "status_category"]
            ].copy()
            table.columns = ["Time", "Moisture %", "Status"]
            st.dataframe(
                table.iloc[::-1],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Moisture %": st.column_config.ProgressColumn(
                        "Moisture %",
                        format="%.1f%%",
                        min_value=0,
                        max_value=100,
                    ),
                    "Status": st.column_config.TextColumn("Status"),
                },
            )

        st.markdown("</div>", unsafe_allow_html=True)


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
