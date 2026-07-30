# Streamlit portfolio (readings.csv)

Streamlit Cloud shows a **snapshot** of plant data from [readings.csv](readings.csv) in this repo. It is not live — update the CSV and push when you want the portfolio to reflect new readings.

For **live** monitoring at home, use the Pi PWA at `http://plant-pi.local:8000` (see [README.md](README.md)).

## Architecture

```text
ESP32 → Pi (live PWA at home)
Pi readings.csv → scp → git push → Streamlit Cloud (portfolio)
```

No Cloudflare tunnel or Streamlit secrets needed.

## Deploy on Streamlit Cloud

1. Repo is on GitHub: `dvjgenis/plant-monitor`
2. [share.streamlit.io](https://share.streamlit.io) → **Create app**
3. Main file: `streamlit_app.py`
4. No secrets required
5. Deploy

## Update the portfolio data

From your Mac:

```bash
./scripts/sync-readings.sh
git add readings.csv
git commit -m "Update readings snapshot"
git push
```

Streamlit Cloud redeploys on push (or click **Reboot app** in the dashboard).

## Local preview

```bash
pip install streamlit pandas
streamlit run streamlit_app.py
```

Ensure `readings.csv` exists in the repo root.

## Pi CSV location

Live CSV grows on the Pi at `~/plant-monitor/readings.csv`. The sync script copies it into this repo before you push.

## Optional: stop Cloudflare tunnel

If you set up a tunnel for the old live Streamlit approach, you can stop it on the Pi:

```bash
pkill cloudflared
```

The Pi server and home PWA are unaffected.
