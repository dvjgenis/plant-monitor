# Plant Hydration Hub

ESP32 soil sensors → Raspberry Pi FastAPI server → live PWA at home, portfolio dashboard on Streamlit Cloud.

## Two ways to view

| View | Where | Live? |
|------|-------|-------|
| **Home PWA** | `http://plant-pi.local:8000` on home Wi-Fi | Yes — auto-refreshes |
| **Portfolio** | Streamlit Cloud app | Snapshot from `readings.csv` in this repo |

## Live at home (PWA)

1. Pi must be running (`plant-server.service` — see [DEPLOY.md](DEPLOY.md))
2. On your phone (same Wi-Fi), open **http://plant-pi.local:8000**
3. **Add to Home Screen** (Safari → Share → Add to Home Screen)

No Mac or Cursor needed for daily checks.

## Portfolio (Streamlit Cloud)

Streamlit reads [readings.csv](readings.csv) from GitHub — not live, but good for a portfolio demo.

1. Sync CSV from Pi: `./scripts/sync-readings.sh`
2. Commit and push: `git add readings.csv && git commit -m "Update readings snapshot" && git push`
3. Streamlit Cloud redeploys automatically — **no secrets required**

See [STREAMLIT.md](STREAMLIT.md) for Streamlit Cloud setup.

## Stack

- **Backend:** [main.py](main.py) — FastAPI, SQLite, CSV export
- **Home UI:** [static/index.html](static/index.html) + [static/manifest.json](static/manifest.json)
- **Portfolio UI:** [streamlit_app.py](streamlit_app.py)
- **Hardware:** ESP32 ([arduino.md](arduino.md), gitignored)

## Pi ops

```bash
ssh admin@plant-pi.local
sudo systemctl status plant-server.service
```

## API (Pi)

POST/DELETE require `X-API-Key` when `PLANT_API_KEY` is set. GET stays open for the home dashboard.

- `GET /api/plants` — latest reading per plant
- `GET /api/plants/{id}/history?day=YYYY-MM-DD` — day history
- `POST /api/moisture` — ESP32 ingest
- `DELETE /api/readings` — wipe all data
