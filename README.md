<p align="center">
  <img src="static/icon.svg" alt="Plant Hydration Hub" width="88" height="88">
</p>

<h1 align="center">Dulf’s Plant Hydration Hub</h1>

<p align="center">
  <strong>ESP32 → Raspberry Pi → live home PWA · public Streamlit portfolio</strong>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-FastAPI-2d5a3d?style=flat-square">
  <img alt="ESP32" src="https://img.shields.io/badge/Hardware-ESP32-c4922a?style=flat-square">
  <img alt="Raspberry Pi" src="https://img.shields.io/badge/Host-Raspberry%20Pi-2d8a55?style=flat-square">
  <img alt="Streamlit" src="https://img.shields.io/badge/Portfolio-Streamlit-c45c3e?style=flat-square">
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

---

## 🏠 Two views — live vs portfolio

| | Home PWA | Streamlit Cloud |
|---|---|---|
| Who | Dulf, on home Wi‑Fi | Visitors / recruiters |
| Where | `http://plant-pi.local:8000` | Streamlit Cloud app |
| Data | Live Pi SQLite + CSV | Committed `readings.csv` |
| Updates | ~every 30s | After sync + `git push` |
| Secrets | API key for POST/DELETE | None |

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

**Portfolio snapshot**

```bash
./scripts/sync-readings.sh
git add readings.csv && git commit -m "Update readings snapshot" && git push
```

Streamlit Cloud redeploys from `streamlit_app.py` — no secrets.

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

| Status | Moisture |
|--------|----------|
| Dry | ≤ 20% |
| Moist | ≤ 50% |
| Optimal | ≤ 80% |
| Soggy | > 80% |

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

<p align="center">
  <sub>Built by Dulf · personal IoT + portfolio project · fork freely for other sensors</sub>
</p>
