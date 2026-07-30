<p align="center">
  <img src="static/icon-animated.svg" alt="Plant Hydration Hub" width="96" height="96">
</p>

<h1 align="center">Dulf’s Plant Hydration Hub</h1>

<p align="center">
  <em>ESP32 → Raspberry Pi → live home PWA · public Streamlit portfolio</em>
</p>

<p align="center">
  <a href="https://plant-monitor.streamlit.app/"><img alt="Live demo" src="https://img.shields.io/badge/🌱_Live_demo-plant--monitor.streamlit.app-c45c3e?style=for-the-badge"></a>
</p>

<p align="center">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-2d5a3d?style=flat-square&logo=opensourceinitiative&logoColor=white"></a>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.x-3776AB?style=flat-square&logo=python&logoColor=white">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white">
  <img alt="Streamlit" src="https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white">
  <img alt="ESP32" src="https://img.shields.io/badge/ESP32-Arduino-00979D?style=flat-square&logo=arduino&logoColor=white">
  <img alt="Raspberry Pi" src="https://img.shields.io/badge/Raspberry%20Pi-A22846?style=flat-square&logo=raspberrypi&logoColor=white">
</p>

<p align="center">
  <a href="https://plant-monitor.streamlit.app/"><strong>Try the public portfolio →</strong></a>
</p>

A full-stack IoT build that measures soil moisture at the plant, stores it on a Raspberry Pi, and shows it two ways: a **live dashboard at home**, and a **portfolio snapshot** anyone can open on Streamlit Cloud.

I built this to bring three threads together: a **love of working with data**, a growing **interest in hardware and IoT**, and **expertise in visualization and web development** — into one honest project: taking better care of the plants at home. Not a toy demo, not a tutorial clone — a system I actually use.

---

## 🌱 Why this matters

Most “plant apps” stop at a demo sketch or a laptop script. This one is an end-to-end system that actually runs 24/7:

| | |
|---|---|
| Hardware → cloud path | Calibrated ESP32 probe → Wi‑Fi POST → Pi API → SQLite/CSV → installable PWA *and* a public Streamlit view |
| Real ops, not a toy | `systemd` service, API keys on mutating routes, sync script for portfolio data, deploy docs |
| Skills in one repo | Embedded IoT, Linux hosting, FastAPI, PWA UI, time-series charts, Streamlit analytics |

It’s a concrete answer to: *can you design, ship, and maintain a small IoT product?*

---

## Contents

- [Why this matters](#-why-this-matters)
- [Two views](#-two-views--live-vs-portfolio)
- [How it works](#-how-it-works)
- [Features](#-features)
- [Stack](#-stack)
- [Quick start](#-quick-start)
- [Repo map](#-repo-map)
- [API](#-api-on-the-pi)
- [Moisture bands](#-moisture-bands)
- [Ops](#-ops)
- [Full deploy guide](DEPLOY.md)
- [Appendix: Tech vocabulary](#-appendix-tech-vocabulary)

---

## 🏠 Two views — live vs portfolio

| | 🏡 Home PWA | ☁️ Streamlit Cloud |
|---|---|---|
| Who | Dulf, on home Wi‑Fi | Visitors / recruiters |
| Where | `http://plant-pi.local:8000` | **[plant-monitor.streamlit.app](https://plant-monitor.streamlit.app/)** |
| Data | Live Pi SQLite + CSV | Committed `readings.csv` |
| Updates | ~every 30s | After sync + `git push` |
| Secrets | API key for POST/DELETE | None |

**Open the public demo:** [https://plant-monitor.streamlit.app/](https://plant-monitor.streamlit.app/)

The PWA is the monitoring tool. Streamlit is the curated demo of the same botanical UI — if the CSV isn’t re-synced after a wipe, the portfolio can look older than the live dashboard.

---

## 🔄 How it works

```text
  ESP32 + soil probe          Raspberry Pi                 Views
  ─────────────────          ─────────────                 ─────
        │                         │
        │  Wi‑Fi POST             │  plant-pi.local:8000
        │  + API key              ├──────────────────────►  Home PWA (live)
        └────────────────────────►│  FastAPI · SQLite
                                  │  readings.csv
                                  │
                                  │  sync-readings.sh
                                  │  git push
                                  └──────────────────────►  Streamlit (snapshot)
```

---

## ✨ Features

- Present hydration — latest % with Dry / Moist / Optimal / Soggy badges
- Day history — 00:00–24:00 military-time chart, list ↔ point highlight
- Plant labels from `plant_id` (e.g. *Gynura Aurantiaca*) even if older CSV names differ
- Authenticated wipe from the dashboard
- Matching Streamlit layout (Altair + gauge cards) for the public portfolio

---

## 🧩 Stack

| Layer | Tech |
|------|------|
| Embedded | ESP32 (Arduino), ADC sensing, calibration, NTP-aligned posts |
| Host | Raspberry Pi, `systemd`, SSH deploy |
| API | FastAPI, SQLite, CSV export, API-key middleware |
| Home UI | Installable PWA (manifest), Chart.js |
| Portfolio | Streamlit, pandas, Altair |
| Hygiene | Secrets gitignored, sync script, no-cache HTML for deploys |

---

## 🚀 Quick start

**Live at home**

1. Pi service up — see [DEPLOY.md](DEPLOY.md)
2. Open **http://plant-pi.local:8000** on the same Wi‑Fi
3. Safari → Share → **Add to Home Screen**

**Portfolio snapshot** — open anytime: [https://plant-monitor.streamlit.app/](https://plant-monitor.streamlit.app/)

Refresh the data shown there from the Pi:

```bash
./scripts/sync-readings.sh
git add readings.csv && git commit -m "Update readings snapshot" && git push
```

Streamlit Cloud redeploys from `streamlit_app.py` — no secrets.

Local preview:

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

---

## 📁 Repo map

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
| `arduino.md` | Local firmware (**gitignored** — secrets) |

---

## 🔌 API (on the Pi)

With `PLANT_API_KEY` set: **GET** stays open for the dashboard; **POST / DELETE** need `X-API-Key`.

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/plants` | Latest reading per plant |
| GET | `/api/plants/{id}/history?day=YYYY-MM-DD` | Day history |
| POST | `/api/moisture` | ESP32 ingest |
| DELETE | `/api/readings` | Wipe |
| GET | `/api/readings.csv` | Download CSV |

---

## 📊 Moisture bands

First match wins:

| Status | Moisture | Badge |
|--------|----------|-------|
| Dry | ≤ 20% | ![Dry](https://img.shields.io/badge/Dry-≤_20%25-c45c3e?style=flat-square) |
| Moist | ≤ 50% | ![Moist](https://img.shields.io/badge/Moist-≤_50%25-c4922a?style=flat-square) |
| Optimal | ≤ 80% | ![Optimal](https://img.shields.io/badge/Optimal-≤_80%25-2d8a55?style=flat-square) |
| Soggy | > 80% | ![Soggy](https://img.shields.io/badge/Soggy->_80%25-3d6b8a?style=flat-square) |

---

## 🔧 Ops

```bash
ssh admin@plant-pi.local
sudo systemctl status plant-server.service

./scripts/sync-readings.sh
git add readings.csv && git commit -m "Update readings snapshot" && git push
```

Full systemd + ESP32 wiring: **[DEPLOY.md](DEPLOY.md)**.

---

## 📖 Appendix: Tech vocabulary

Plain-language definitions for terms used in this project:

| Term | Meaning here |
|------|----------------|
| **IoT** (Internet of Things) | Everyday devices with sensors and network access — here, a soil probe that talks to a home server over Wi‑Fi. |
| **ESP32** | A low-cost microcontroller board with Wi‑Fi. It reads the soil sensor and POSTs moisture readings to the Pi. |
| **Raspberry Pi** | A small always-on Linux computer. It runs the FastAPI server, stores readings, and serves the home dashboard. |
| **Sensor / ADC** | The moisture probe outputs an analog voltage; the ESP32’s ADC turns that into a number that gets mapped to a % wetness. |
| **API** | A contract for machines to talk — e.g. `POST /api/moisture` for the ESP32, `GET /api/plants` for the dashboard. |
| **FastAPI** | The Python web framework that implements that API on the Pi. |
| **SQLite** | A file-based database on the Pi (`plants.db`) that stores every reading. |
| **CSV** | A simple spreadsheet-style log (`readings.csv`) also written on the Pi and synced into GitHub for the portfolio. |
| **PWA** (Progressive Web App) | A website that can be installed to the phone home screen and feels app-like. The live dashboard at `plant-pi.local:8000` is the PWA. |
| **Streamlit** | A Python toolkit for data apps. Used here for the *public* portfolio view (not the live home monitor): [plant-monitor.streamlit.app](https://plant-monitor.streamlit.app/). |
| **Time series** | Data indexed by time — moisture % over hours and days, plotted on a 00:00–24:00 axis. |
| **Data analytics** | Exploring and summarizing those readings (averages, status bands, day charts) to understand plant hydration. |
| **Data science** | Broader practice of asking questions with data — here: what does “healthy moisture” look like for each plant over time? |
| **Data engineering** | Building reliable pipelines so data flows from sensor → storage → UI without babysitting (ingest API, SQLite/CSV, sync script). |
| **Visualization** | Charts, gauges, and badges that make moisture status obvious at a glance (Chart.js at home, Altair on Streamlit). |
| **Web development** | HTML/CSS/JS (and Streamlit) used to ship those interfaces as real products, not notebooks alone. |
| **systemd** | Linux service manager that keeps the Pi server running after reboot. |
| **API key** | A shared secret (`PLANT_API_KEY`) required for POST/DELETE so random clients can’t spam or wipe data. |

---

<p align="center">
  <img alt="Made with" src="https://img.shields.io/badge/Made_with-💚-2d5a3d?style=flat-square">
  <img alt="IoT" src="https://img.shields.io/badge/IoT-ESP32_%2B_Pi-c4922a?style=flat-square">
  <a href="LICENSE"><img alt="MIT" src="https://img.shields.io/badge/License-MIT-2d5a3d?style=flat-square"></a>
</p>

<p align="center">
  <sub>Built by Dulf · personal IoT + portfolio project · fork freely for other sensors</sub>
</p>
