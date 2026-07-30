"""Remote plant dashboard — reads live data from the Pi via Cloudflare Tunnel."""

from datetime import date, datetime, timedelta
import os

import pandas as pd
import requests
import streamlit as st

REFRESH_SECONDS = 30

CATEGORY_COLORS = {
    "Dry": "#c45c3e",
    "Moist": "#c4922a",
    "Optimal": "#2d8a55",
    "Soggy": "#2a7a8a",
    "Unknown": "#5a7262",
}


def get_config() -> tuple[str, str]:
    api_url = os.environ.get("PI_API_URL", "").strip()
    api_key = os.environ.get("PLANT_API_KEY", "").strip()
    try:
        if not api_url:
            api_url = st.secrets["PI_API_URL"].strip()
        if not api_key:
            api_key = st.secrets["PLANT_API_KEY"].strip()
    except (KeyError, FileNotFoundError, AttributeError):
        pass
    if not api_url or not api_key:
        st.error(
            "Missing `PI_API_URL` or `PLANT_API_KEY`. "
            "Add them in Streamlit Cloud → Settings → Secrets."
        )
        st.stop()
    return api_url.rstrip("/"), api_key


def api_get(base_url: str, api_key: str, path: str, **params) -> dict | list:
    response = requests.get(
        f"{base_url}{path}",
        headers={"X-API-Key": api_key},
        params=params or None,
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


@st.fragment(run_every=timedelta(seconds=REFRESH_SECONDS))
def live_dashboard(base_url: str, api_key: str) -> None:
    try:
        plants_payload = api_get(base_url, api_key, "/api/plants")
    except requests.RequestException as exc:
        st.error(f"Could not reach the Pi API: {exc}")
        st.caption("Check that the Pi service and Cloudflare tunnel are running.")
        return

    plants = plants_payload.get("plants", [])
    if not plants:
        st.info("No readings yet. Waiting for the ESP32 to post to the Pi.")
        return

    st.subheader("Present hydration")
    cols = st.columns(min(len(plants), 3))
    for idx, plant in enumerate(plants):
        with cols[idx % len(cols)]:
            pct = float(plant["moisture_percentage"])
            category = plant.get("status_category", "Unknown")
            st.metric(
                label=plant["name"],
                value=f"{pct:.1f}%",
                delta=category,
            )
            st.progress(min(max(pct / 100.0, 0.0), 1.0))
            st.caption(f"Updated {plant.get('time_of_day', '—')}")

    chart_df = pd.DataFrame(
        {
            "plant": [p["name"] for p in plants],
            "moisture_pct": [float(p["moisture_percentage"]) for p in plants],
        }
    ).set_index("plant")
    st.bar_chart(chart_df, height=220)

    st.divider()
    st.subheader("Day history")

    plant_options = {p["name"]: p["plant_id"] for p in plants}
    selected_name = st.selectbox("Plant", list(plant_options.keys()))
    plant_id = plant_options[selected_name]

    today = date.today()
    picked = st.date_input("Day", value=today, max_value=today)
    selected_day = picked.isoformat()

    try:
        history_payload = api_get(
            base_url,
            api_key,
            f"/api/plants/{plant_id}/history",
            day=selected_day,
        )
    except requests.RequestException as exc:
        st.error(f"Could not load history: {exc}")
        return

    history = history_payload.get("history", [])
    if not history:
        st.warning("No readings for this day.")
        return

    df = pd.DataFrame(history)
    df["hour"] = df["hour_fraction"]
    df = df.sort_values("hour")
    st.line_chart(df.set_index("hour")["moisture_percentage"], height=280)

    table = df[["time_of_day", "moisture_percentage", "status_category"]].copy()
    table.columns = ["Time", "Moisture %", "Status"]
    table = table.iloc[::-1]
    st.dataframe(table, use_container_width=True, hide_index=True)


def main() -> None:
    st.set_page_config(
        page_title="Plant Hydration Hub",
        page_icon="🪴",
        layout="wide",
    )
    st.title("Plant Hydration Hub")
    st.caption("Live view from home · auto-refreshes every 30 seconds")

    base_url, api_key = get_config()
    live_dashboard(base_url, api_key)


if __name__ == "__main__":
    main()
