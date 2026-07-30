# Deploy & operations

Everything needed to run **Plant Hydration Hub** on a Raspberry Pi, keep the home PWA online, talk to the ESP32, and refresh the Streamlit portfolio snapshot.

> **Portfolio vs home:** Live demo → [plant-monitor.streamlit.app](https://plant-monitor.streamlit.app/) (CSV snapshot). Home PWA → `plant-pi.local:8000`. Details: [README.md](README.md).

---

## Prerequisites

- Pi reachable: `ssh admin@plant-pi.local`
- SSH key auth configured (Raspberry Pi Imager)
- On the Pi (once):

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv git -y
```

---

## 1. Copy project files from Mac

On the Mac (not inside SSH):

```bash
cd ~/Desktop/plant-monitor
scp main.py requirements-pi.txt admin@plant-pi.local:~/plant-monitor/
scp static/index.html static/manifest.json static/icon.svg admin@plant-pi.local:~/plant-monitor/static/
```

Do **not** copy `venv/`, `plants.db`, local `readings.csv`, or `__pycache__`. Live data lives on the Pi.

---

## 2. Python environment on the Pi

```bash
ssh admin@plant-pi.local
mkdir -p ~/plant-monitor/static
cd ~/plant-monitor
python3 -m venv venv
source venv/bin/activate
pip install -U pip
pip install -r requirements-pi.txt
```

> `requirements.txt` is for **Streamlit Cloud / Mac preview** only. The Pi uses `requirements-pi.txt` (FastAPI stack).

Smoke test:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Visit `http://plant-pi.local:8000`, then `Ctrl+C`.

---

## 3. systemd (24/7 service)

```bash
sudo nano /etc/systemd/system/plant-server.service
```

```ini
[Unit]
Description=Plant Hydration FastAPI Server
After=network.target

[Service]
User=admin
WorkingDirectory=/home/admin/plant-monitor
Environment=PLANT_API_KEY=your-generated-key-here
Environment=VAPID_PRIVATE_KEY=paste-from-generate-script
Environment=VAPID_PUBLIC_KEY=paste-from-generate-script
Environment=VAPID_CONTACT=mailto:you@example.com
ExecStart=/home/admin/plant-monitor/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Generate a key once (example): `openssl rand -hex 24`

```bash
sudo systemctl daemon-reload
sudo systemctl enable plant-server.service
sudo systemctl start plant-server.service
sudo systemctl status plant-server.service
```

Follow logs: `journalctl -u plant-server.service -f`

The same key must appear in the ESP32 sketch (`X-API-Key`) and in wipe prompts on the PWA. Keep it in local `arduino.md` (gitignored) — never commit it.

---

## 3b. Web Push (Dry alerts ≤20%)

When a plant **enters** Dry, the Pi sends a phone notification to every device that enabled alerts in the PWA. It will not re-alert every 30 minutes while still dry; after moisture rises above 20%, the next drop can alert again.

### Important: HTTPS required

Browsers only allow Web Push in a **secure context** (`https://…` or `http://localhost`). Plain `http://plant-pi.local` will show **Alerts unavailable**.

Practical options:

1. **Tailscale Serve / Funnel** or a **Cloudflare Tunnel** in front of the Pi (easiest HTTPS to a phone away from home)
2. Local reverse proxy with a trusted cert (mkcert / Caddy)

ESP32 can keep posting to the LAN IP over HTTP; only the phone’s PWA URL needs HTTPS for push subscribe.

### One-time VAPID keys (on the Pi)

```bash
cd ~/plant-monitor
source venv/bin/activate
pip install -r requirements-pi.txt
python scripts/generate-vapid-keys.py
```

Paste the printed `Environment=` lines into `plant-server.service`, then:

```bash
sudo systemctl daemon-reload
sudo systemctl restart plant-server.service
```

### Enable on your phone

1. Open the **HTTPS** PWA URL → Share → **Add to Home Screen** (iOS 16.4+)
2. Open the installed app → **Enable alerts** → Allow notifications
3. Optional test (from Mac, with API key):

```bash
curl -X POST http://plant-pi.local:8000/api/push/test \
  -H "X-API-Key: YOUR_KEY"
```

(Use your HTTPS host if that is what the phone subscribed through.)

---

## 4. ESP32 → Pi endpoint

On the Pi:

```bash
hostname -I
```

Point the sketch at that LAN IP (example):

```cpp
const char* serverName = "http://10.0.0.43:8000/api/moisture";
```

Upload from Arduino IDE over USB. After upload, the ESP32 can run from wall power on the same Wi‑Fi. Interval changes require USB again.

Current cadence: **every 30 minutes**, NTP-aligned to the clock (`:00`, `:30`). Set via `INTERVAL_MINUTES = 30` in the sketch.

Firmware reference: local `arduino.md` (gitignored).

---

## 5. Verify the live stack

- Dashboard: `http://plant-pi.local:8000` or `http://<pi-ip>:8000`
- Phone: Safari → Share → Add to Home Screen
- Test ingest from Mac:

```bash
curl -X POST http://plant-pi.local:8000/api/moisture \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -d '{"plant_id":1,"raw_value":2000,"moisture_percentage":45.5}'
```

- CSV grows at `~/plant-monitor/readings.csv` on the Pi

---

## 6. Update code after changes

```bash
scp main.py requirements-pi.txt admin@plant-pi.local:~/plant-monitor/
scp scripts/generate-vapid-keys.py admin@plant-pi.local:~/plant-monitor/scripts/
scp static/index.html static/manifest.json static/icon.svg static/sw.js admin@plant-pi.local:~/plant-monitor/static/
ssh admin@plant-pi.local "cd ~/plant-monitor && source venv/bin/activate && pip install -r requirements-pi.txt && sudo systemctl restart plant-server.service"
```

---

## 7. Streamlit portfolio (CSV snapshot)

**Live public URL:** [https://plant-monitor.streamlit.app/](https://plant-monitor.streamlit.app/)

Streamlit does **not** call the Pi. It reads [readings.csv](readings.csv) from GitHub after a push.

### First-time Streamlit Cloud

1. Repo on GitHub (e.g. `dvjgenis/plant-monitor`)
2. [share.streamlit.io](https://share.streamlit.io) → **Create app**
3. Main file: `streamlit_app.py`
4. **No secrets** required
5. Deploy

### Refresh portfolio data from Mac

```bash
./scripts/sync-readings.sh
git add readings.csv
git commit -m "Update readings snapshot"
git push
```

Cloud redeploys on push (or **Reboot app** in the Streamlit dashboard).

### Local preview

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

---

## Troubleshooting

| Symptom | Check |
|---------|--------|
| PWA blank / offline | `systemctl status plant-server` · same Wi‑Fi · `plant-pi.local` vs IP |
| ESP32 POST 401 | `PLANT_API_KEY` in systemd matches sketch header |
| Wipe fails | Enter the same API key when the PWA prompts |
| Alerts unavailable | Need HTTPS PWA URL + VAPID keys in systemd · iOS: installed Home Screen app |
| Dry alert never fires | Enable alerts on phone · check `journalctl` for “Dry alert” · de-dupe waits for recovery above 20% |
| Streamlit empty / old | Sync CSV from Pi and push; Cloud is not live |
| Upload to ESP32 fails | Board must be on USB to the Mac for flashing |
| Sync script fails | Pi CSV empty or missing header — check ESP32 posts and Pi service |

---

## Related

- [README.md](README.md) — architecture, PWA vs Streamlit, skills
- `arduino.md` — local firmware + secrets (not in git)
