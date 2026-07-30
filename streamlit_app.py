"""Portfolio plant dashboard — reads readings.csv committed to the repo."""

from datetime import date
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

CSV_PATH = Path(__file__).parent / "readings.csv"

PLANT_NAMES = {
    1: "Gynura Aurantiaca",
    2: "Plant #2",
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
  margin-bottom: 0.65rem;
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

.snapshot-note {
  font-size: 0.82rem;
  color: #5a7262;
  margin-bottom: 1rem;
}
</style>
"""


def inject_styles() -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def display_name(row: pd.Series) -> str:
    pid = int(row["plant_id"])
    return PLANT_NAMES.get(pid, row.get("plant_name") or f"Plant #{pid}")


def load_readings() -> pd.DataFrame:
    if not CSV_PATH.exists():
        st.error("`readings.csv` not found in the repo.")
        st.stop()

    df = pd.read_csv(CSV_PATH)
    if df.empty:
        st.info("No readings in the CSV yet. Run `./scripts/sync-readings.sh` after the Pi collects data.")
        st.stop()

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["moisture_percentage"] = pd.to_numeric(df["moisture_percentage"])
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
    fg, bg = BADGE_STYLES.get(category, BADGE_STYLES["Unknown"])
    return f'<span class="badge" style="color:{fg};background:{bg}">{category}</span>'


def bar_gradient(category: str) -> str:
    colors = {
        "Dry": "linear-gradient(90deg, #d97858, #c45c3e)",
        "Moist": "linear-gradient(90deg, #e0b34d, #c4922a)",
        "Optimal": "linear-gradient(90deg, #5cbc7d, #2d8a55)",
        "Soggy": "linear-gradient(90deg, #4ea8b8, #2a7a8a)",
    }
    return colors.get(category, colors["Dry"])


def render_gauge_card(row: pd.Series) -> None:
    pct = float(row["moisture_percentage"])
    category = row.get("status_category", "Unknown")
    width = min(max(pct, 0), 100)
    st.markdown(
        f"""
        <div class="gauge-card">
          <div class="gauge-top">
            <span class="gauge-name">{row['plant_name']}</span>
            <span class="gauge-pct">{pct:.1f}%</span>
          </div>
          <div class="gauge-bar">
            <div class="gauge-fill" style="width:{width}%;background:{bar_gradient(category)}"></div>
          </div>
          <div style="display:flex;justify-content:space-between;align-items:center;">
            {badge_html(category)}
            <span style="font-size:0.72rem;color:#5a7262;">Updated {row['time_of_day']}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def day_chart(day_df: pd.DataFrame) -> alt.Chart:
    chart = (
        alt.Chart(day_df)
        .mark_line(point=True, color="#2d5a3d", strokeWidth=2.5)
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
            tooltip=[
                alt.Tooltip("time_of_day:N", title="Time"),
                alt.Tooltip("moisture_percentage:Q", title="Moisture %", format=".1f"),
                alt.Tooltip("status_category:N", title="Status"),
            ],
        )
        .properties(height=260)
        .configure_view(strokeWidth=0)
        .configure_axis(gridColor="rgba(45, 90, 61, 0.1)", labelColor="#5a7262", titleColor="#5a7262")
    )
    return chart


def portfolio_dashboard(df: pd.DataFrame) -> None:
    latest = latest_per_plant(df)
    last_updated = df["timestamp"].max().strftime("%Y-%m-%d %H:%M")

    st.markdown(
        f'<p class="snapshot-note">Portfolio snapshot as of <strong>{last_updated}</strong> '
        f"(from last git push). For live data at home, use the Pi PWA at "
        f"<code>plant-pi.local:8000</code>.</p>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="legend">
          <span>Dry ≤20%</span>
          <span>Moist 21–50%</span>
          <span>Optimal 51–80%</span>
          <span>Soggy &gt;80%</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.55, 0.85], gap="medium")

    plant_options = dict(zip(latest["plant_name"], latest["plant_id"]))

    with right:
        st.markdown(
            '<div class="panel"><h3>Present hydration</h3>'
            '<div class="sub">Latest reading per plant</div>',
            unsafe_allow_html=True,
        )
        for _, row in latest.iterrows():
            render_gauge_card(row)
        st.markdown("</div>", unsafe_allow_html=True)

    with left:
        st.markdown(
            '<div class="panel"><h3>Day history</h3>'
            '<div class="sub">Hourly moisture for selected day</div>',
            unsafe_allow_html=True,
        )

        selected_name = st.selectbox(
            "Plant",
            list(plant_options.keys()),
            label_visibility="collapsed",
        )
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
            st.caption(f"{selected_name} · {len(day_df)} reading(s)")
            st.altair_chart(day_chart(day_df), use_container_width=True)
            table = day_df[["time_of_day", "moisture_percentage", "status_category"]].copy()
            table.columns = ["Time", "Moisture %", "Status"]
            st.dataframe(table.iloc[::-1], use_container_width=True, hide_index=True)

        st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(
        page_title="Plant Hydration Hub",
        page_icon="🪴",
        layout="centered",
    )
    inject_styles()
    st.title("Plant Hydration Hub")
    st.caption("Portfolio view · ESP32 soil moisture project")

    df = load_readings()
    portfolio_dashboard(df)


if __name__ == "__main__":
    main()
