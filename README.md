# Plant Hydration Hub

ESP32 soil sensors → Raspberry Pi FastAPI server → dashboard at home or anywhere via Streamlit Cloud.

## Views

| Where | URL | Use case |
|-------|-----|----------|
| Home (LAN) | `http://plant-pi.local:8000` | Full dashboard, PWA, low latency |
| Anywhere | Streamlit Cloud app | Check plants from phone/laptop off Wi-Fi |

## Stack

- **Backend:** [main.py](main.py) — FastAPI, SQLite, CSV export
- **Home UI:** [static/index.html](static/index.html)
- **Remote UI:** [streamlit_app.py](streamlit_app.py)
- **Hardware:** ESP32 + capacitive moisture sensor ([arduino.md](arduino.md), gitignored)

## Quick start (Pi)

See [DEPLOY.md](DEPLOY.md) for full Pi setup.

```bash
ssh admin@plant-pi.local
sudo systemctl status plant-server.service
```

## Remote access

See [STREAMLIT.md](STREAMLIT.md) for Cloudflare Tunnel + Streamlit Cloud + API key setup.

## API

All `/api/*` **write** routes (POST, DELETE) require header `X-API-Key` when `PLANT_API_KEY` is set on the server. **GET** routes stay open so the home dashboard works.

- `GET /api/plants` — latest reading per plant
- `GET /api/plants/{id}/history?day=YYYY-MM-DD` — day history
- `POST /api/moisture` — ESP32 ingest
- `DELETE /api/readings` — wipe all data
