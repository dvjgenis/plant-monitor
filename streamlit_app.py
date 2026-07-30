"""Portfolio plant dashboard — reads readings.csv committed to the repo."""

from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

CSV_PATH = Path(__file__).parent / "readings.csv"


def load_readings() -> pd.DataFrame:
    if not CSV_PATH.exists():
        st.error(f"`readings.csv` not found at `{CSV_PATH}`.")
        st.stop()

    df = pd.read_csv(CSV_PATH)
    if df.empty:
        st.info("No readings in the CSV yet.")
        st.stop()

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["moisture_percentage"] = pd.to_numeric(df["moisture_percentage"])
    df["plant_id"] = pd.to_numeric(df["plant_id"], downcast="integer")
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


def portfolio_dashboard(df: pd.DataFrame) -> None:
    latest = latest_per_plant(df)
    last_updated = df["timestamp"].max().strftime("%Y-%m-%d %H:%M")

    st.subheader("Present hydration")
    st.caption(f"Snapshot as of {last_updated} (from last git push)")

    cols = st.columns(min(len(latest), 3))
    for i, (_, row) in enumerate(latest.iterrows()):
        with cols[i % len(cols)]:
            pct = float(row["moisture_percentage"])
            st.metric(
                label=row["plant_name"],
                value=f"{pct:.1f}%",
                delta=row["status_category"],
            )
            st.progress(min(max(pct / 100.0, 0.0), 1.0))
            st.caption(f"Updated {row['time_of_day']}")

    chart_df = latest.set_index("plant_name")[["moisture_percentage"]]
    chart_df.columns = ["moisture_pct"]
    st.bar_chart(chart_df, height=220)

    st.divider()
    st.subheader("Day history")

    plant_options = dict(zip(latest["plant_name"], latest["plant_id"]))
    selected_name = st.selectbox("Plant", list(plant_options.keys()))
    plant_id = plant_options[selected_name]

    plant_df = df[df["plant_id"] == plant_id]
    min_day = plant_df["date"].min()
    max_day = plant_df["date"].max()
    picked = st.date_input(
        "Day",
        value=max_day,
        min_value=min_day,
        max_value=max_day,
    )

    day_df = plant_df[plant_df["date"] == picked].sort_values("timestamp")
    if day_df.empty:
        st.warning("No readings for this day in the CSV snapshot.")
        return

    st.line_chart(
        day_df.set_index("hour_fraction")["moisture_percentage"],
        height=280,
    )

    table = day_df[["time_of_day", "moisture_percentage", "status_category"]].copy()
    table.columns = ["Time", "Moisture %", "Status"]
    st.dataframe(table.iloc[::-1], use_container_width=True, hide_index=True)


def main() -> None:
    st.set_page_config(
        page_title="Plant Hydration Hub",
        page_icon="🪴",
        layout="wide",
    )
    st.title("Plant Hydration Hub")
    st.caption(
        "Portfolio snapshot from readings.csv · "
        "For live data at home, use the Pi PWA at plant-pi.local:8000"
    )

    df = load_readings()
    portfolio_dashboard(df)


if __name__ == "__main__":
    main()
