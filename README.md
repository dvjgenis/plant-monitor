# Dulf’s Plant Hydration Hub

**ESP32 soil sensors → Raspberry Pi → live home PWA · public portfolio on Streamlit Cloud**

A full-stack IoT project that measures soil moisture at the plant, stores readings on a Raspberry Pi, and surfaces them two ways: a **live Progressive Web App** on a home LAN, and a **portfolio snapshot** on Streamlit Cloud for GitHub visitors.

---

## Live PWA vs Streamlit portfolio

| | **Home PWA** (private, live) | **Streamlit Cloud** (public snapshot) |
|---|---|---|
| **URL** | `http://plant-pi.local:8000` (home Wi‑Fi) | Streamlit Cloud app URL |
| **Data** | Live from the Pi (SQLite + CSV) | Committed `readings.csv` in this repo |
| **Freshness** | Auto-refreshes ~every 30s | Updates when CSV is synced and pushed |
| **Audience** | Home monitoring on phone or laptop | Recruiters, classmates, GitHub visitors |
| **Secrets** | API key on the Pi for POST/DELETE | None — public CSV snapshot |
| **UI** | Custom botanical PWA (Chart.js, gauges) | Matching two-panel layout (Altair + HTML gauges) |

**In short:** the PWA is the real monitoring tool. Streamlit is a curated demo of the same design language, powered by a CSV periodically pulled from the Pi. If the CSV was wiped or not yet re-synced, Streamlit may show fewer (or older) points than the live dashboard.

```text
┌─────────────┐     Wi‑Fi POST      ┌──────────────────┐     home LAN           ┌─────────────┐
│  ESP32 +    │ ─────────────────► │  Raspberry Pi    │ ────────────────────► │  Home PWA   │
│  soil probe │    + API key       │  FastAPI · SQLite│  plant-pi.local:8000  │  (live)     │
└─────────────┘                    │  readings.csv    │                       └─────────────┘
                                   └────────┬─────────┘
                                            │  ./scripts/sync-readings.sh
                                            │  git commit + push
                                            ▼
                                   ┌──────────────────┐
                                   │  Streamlit Cloud │  ← portfolio snapshot
                                   │  streamlit_app.py│
                                   └──────────────────┘
```

---

## Skills & technologies

| Area | What this project covers |
|------|--------------------------|
| **Embedded / IoT** | ESP32 (Arduino), ADC soil sensing, calibration, Wi‑Fi reconnect, NTP-aligned sampling |
| **Raspberry Pi** | Headless Linux, `systemd` services, SSH deploy, LAN hosting |
| **Backend API** | FastAPI, REST ingest, API-key middleware, SQLite persistence, CSV export |
| **PWA frontend** | Installable home-screen web app (manifest), Chart.js day history, responsive botanical UI |
| **Data analytics** | Time-series moisture %, status bands (Dry → Soggy), 24‑hour military-time charts |
| **Portfolio / cloud** | Streamlit Cloud, pandas + Altair visualizations, git-synced datasets |
| **DevOps hygiene** | Secrets out of git (`.gitignore`), sync scripts, service restart workflows |

---

## Features

- **Present hydration** — latest % and Dry / Moist / Optimal / Soggy badge per plant  
- **Day history** — line chart on a fixed **00:00–24:00** axis with military-time labels  
- **Plant rename map** — display names (e.g. *Gynura Aurantiaca*) from `plant_id`, even if older CSV rows used another label  
- **Wipe + API key** — dashboard can clear readings when authenticated  
- **Portfolio parity** — Streamlit mirrors the same two-panel sage layout as the PWA  

---

## Quick start

### At home (live)

1. Pi service running — see [DEPLOY.md](DEPLOY.md)  
2. On phone (same Wi‑Fi): open **http://plant-pi.local:8000**  
3. Safari → Share → **Add to Home Screen**

### Portfolio (Streamlit)

1. Sync from Pi: `./scripts/sync-readings.sh`  
2. `git add readings.csv && git commit -m "Update readings snapshot" && git push`  
3. Streamlit Cloud redeploys from `streamlit_app.py` — **no secrets**

First-time Streamlit Cloud: [share.streamlit.io](https://share.streamlit.io) → create app → main file `streamlit_app.py`.

Local preview:

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

---

## Repository map

| Path | Role |
|------|------|
| [main.py](main.py) | FastAPI server, SQLite, CSV, plant name map |
| [requirements-pi.txt](requirements-pi.txt) | Pi / FastAPI dependencies |
| [requirements.txt](requirements.txt) | Streamlit Cloud dependencies |
| [static/index.html](static/index.html) | Live home PWA |
| [streamlit_app.py](streamlit_app.py) | Portfolio dashboard |
| [readings.csv](readings.csv) | Snapshot committed for Streamlit |
| [scripts/sync-readings.sh](scripts/sync-readings.sh) | Pull CSV from Pi → repo |
| [DEPLOY.md](DEPLOY.md) | Pi install, systemd, ESP32 endpoint, portfolio sync |
| `arduino.md` | Local-only firmware notes (**gitignored** — contains Wi‑Fi / API secrets) |

---

## API (on the Pi)

When `PLANT_API_KEY` is set in systemd:

- **GET** `/api/*` — open (home dashboard)  
- **POST / DELETE** — require `X-API-Key`

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/plants` | Latest reading per plant |
| GET | `/api/plants/{id}/history?day=YYYY-MM-DD` | Day history (+ available days) |
| POST | `/api/moisture` | ESP32 ingest |
| DELETE | `/api/readings` | Wipe all readings |
| GET | `/api/readings.csv` | Download CSV |

---

## Moisture categories

Evaluated in order (first match wins):

| Status | Moisture % |
|--------|------------|
| Dry | ≤ 20% |
| Moist | ≤ 50% |
| Optimal | ≤ 80% |
| Soggy | > 80% |

---

## Ops cheatsheet

```bash
# Pi health
ssh admin@plant-pi.local
sudo systemctl status plant-server.service

# Refresh portfolio data from Mac
./scripts/sync-readings.sh
git add readings.csv && git commit -m "Update readings snapshot" && git push
```

Full deploy, systemd unit, and ESP32 wiring: **[DEPLOY.md](DEPLOY.md)**.

---

## License / use

Built as a personal IoT + portfolio project by Dulf. Fork and adapt freely for other sensors and plants.
