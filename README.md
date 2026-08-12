<p align="center">
  <img src="static/icon-animated.svg" alt="Plant Hydration Hub" width="96" height="96">
</p>

<h1 align="center">Dulf’s Plant Hydration Hub</h1>

<p align="center">
  <strong>TL;DR — One sentence:</strong> An always-on IoT system that reads soil moisture from an ESP32, stores it on a Raspberry Pi, and shows it live at home (installable PWA) plus a public Streamlit portfolio anyone can open.
</p>

<p align="center">
  <em>ESP32 → Raspberry Pi → live home PWA · public Streamlit portfolio</em>
</p>

<p align="center">
  <a href="https://plant-monitor.streamlit.app/"><img alt="Live demo" src="https://img.shields.io/badge/Live_demo-plant--monitor.streamlit.app-c45c3e?style=for-the-badge"></a>
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-2d5a3d?style=flat-square"></a>
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white">
  <img alt="ESP32" src="https://img.shields.io/badge/ESP32-Arduino-00979D?style=flat-square&logo=arduino&logoColor=white">
  <img alt="Raspberry Pi" src="https://img.shields.io/badge/Raspberry%20Pi-A22846?style=flat-square&logo=raspberrypi&logoColor=white">
</p>

<p align="center">
  <a href="https://plant-monitor.streamlit.app/"><strong>Try the public portfolio →</strong></a>
</p>

---

## What this is (in plain English)

Most “plant apps” stop at a demo sketch. This one runs **24/7**:

1. An **ESP32** with a soil probe measures moisture and POSTs on the clock (`:00` / `:30`)  
2. A **Raspberry Pi** FastAPI server stores readings in SQLite + CSV  
3. A **home PWA** on the local network shows live status and day charts  
4. A **Streamlit Cloud** app mirrors a synced CSV snapshot for recruiters / visitors  

Built to care for real plants at home — and to prove one person can design, ship, and maintain a small IoT product end to end.

---

## Why it's interesting / significant

| | |
|---|---|
| **Full hardware → cloud path** | Calibrated probe → Wi‑Fi → Pi API → storage → two UIs |
| **Real ops** | `systemd`, API keys on mutating routes, sync script, deploy docs — not a laptop-only toy |
| **Skills in one repo** | Embedded IoT, Linux hosting, FastAPI, PWA, time-series viz, Streamlit analytics |
| **Honest portfolio** | Public demo anyone can open; live system is what actually runs at home |

It's a concrete answer to: *can you design, ship, and maintain a small IoT product?*

---

## Two views — live vs portfolio

| | Home PWA | Streamlit Cloud |
|---|---|---|
| Who | Me, on home Wi‑Fi | Visitors / recruiters |
| Where | `http://plant-pi.local:8000` | **[plant-monitor.streamlit.app](https://plant-monitor.streamlit.app/)** |
| Data | Live Pi SQLite + CSV | Committed `readings.csv` |
| Refresh | ~every 30s while open | After sync + `git push` |
| Secrets | API key for POST/DELETE | None |

The PWA is the monitoring tool. Streamlit is the curated public demo of the same botanical UI.

---

## How it works

```text
  ESP32 + soil probe          Raspberry Pi                 Views
  ─────────────────          ─────────────                 ─────
        │                         │
        │  Wi‑Fi POST (:00/:30)   │  plant-pi.local:8000
        │  + API key              ├──────────────────────►  Home PWA (live)
        └────────────────────────►│  FastAPI · SQLite
                                  │  readings.csv
                                  │
                                  │  sync-readings.sh
                                  │  git push
                                  └──────────────────────►  Streamlit (snapshot)
```

---

## Features

- Latest hydration % with Dry / Moist / Optimal / Soggy badges  
- Day history chart (00:00–24:00), list ↔ point highlight  
- Plant labels from `plant_id` (e.g. *Gynura Aurantiaca*)  
- Authenticated wipe from the dashboard  
- Matching Streamlit layout (Altair + gauges) for the public portfolio  

---

## Stack

| Layer | Tech |
|------|------|
| Embedded | ESP32 (Arduino), ADC sensing, calibration, NTP-aligned 30‑min posts |
| Host | Raspberry Pi, `systemd`, SSH deploy |
| API | FastAPI, SQLite, CSV export, API-key middleware |
| Home UI | Installable PWA, Chart.js |
| Portfolio | Streamlit, pandas, Altair |

---

## Quick start

**Live at home**

1. Bring the Pi service up — see [DEPLOY.md](DEPLOY.md)  
2. Open **http://plant-pi.local:8000** on the same Wi‑Fi  
3. Safari → Share → **Add to Home Screen**  

**Portfolio snapshot** — [https://plant-monitor.streamlit.app/](https://plant-monitor.streamlit.app/)

Refresh portfolio data from the Pi:

```bash
./scripts/sync-readings.sh
git add readings.csv && git commit -m "Update readings snapshot" && git push
```

Local Streamlit preview:

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

---

## Repo map

| Path | Role |
|------|------|
| [main.py](main.py) | FastAPI server |
| [requirements-pi.txt](requirements-pi.txt) | Pi / FastAPI deps |
| [requirements.txt](requirements.txt) | Streamlit Cloud deps |
| [static/index.html](static/index.html) | Live home PWA |
| [streamlit_app.py](streamlit_app.py) | Portfolio dashboard |
| [readings.csv](readings.csv) | Portfolio CSV snapshot |
| [scripts/sync-readings.sh](scripts/sync-readings.sh) | Pi → repo sync |
| [DEPLOY.md](DEPLOY.md) | Full install & ops |

---

## API (on the Pi)

With `PLANT_API_KEY` set: **GET** stays open for the dashboard; **POST / DELETE** need `X-API-Key`.

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/plants` | Latest reading per plant |
| GET | `/api/plants/{id}/history?day=YYYY-MM-DD` | Day history |
| POST | `/api/moisture` | ESP32 ingest |
| DELETE | `/api/readings` | Wipe |
| GET | `/api/readings.csv` | Download CSV |

---

## Moisture bands

First match wins:

| Status | Moisture |
|--------|----------|
| Dry | ≤ 20% |
| Moist | ≤ 50% |
| Optimal | ≤ 80% |
| Soggy | > 80% |

---

## Ops

```bash
ssh admin@plant-pi.local
sudo systemctl status plant-server.service

./scripts/sync-readings.sh
git add readings.csv && git commit -m "Update readings snapshot" && git push
```

Full systemd + ESP32 wiring: **[DEPLOY.md](DEPLOY.md)**.

---

## Appendix: Tech vocabulary

| Term | Meaning here |
|------|----------------|
| **IoT** | Everyday devices with sensors + network — here, a soil probe talking to a home server |
| **ESP32** | Low-cost Wi‑Fi microcontroller that reads the probe and POSTs moisture |
| **Raspberry Pi** | Always-on Linux host for the API, database, and home dashboard |
| **FastAPI** | Python web framework implementing the Pi API |
| **SQLite / CSV** | Storage on the Pi; CSV also synced to GitHub for Streamlit |
| **PWA** | Installable web app for the live home dashboard |
| **Streamlit** | Public portfolio view at [plant-monitor.streamlit.app](https://plant-monitor.streamlit.app/) |
| **systemd** | Keeps the Pi server running after reboot |
| **API key** | Secret required for POST/DELETE so random clients can't spam or wipe data |

---

<p align="center">
  <sub>Built by Dulf · personal IoT + portfolio project · MIT License</sub>
</p>
