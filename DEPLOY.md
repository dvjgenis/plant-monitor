# Deploy plant-monitor to Raspberry Pi

Deploy the **current Mac project** to the Pi. Do not paste the outdated tutorial snippets — use these files.

## Prerequisites

- Pi reachable via SSH: `ssh admin@plant-pi.local`
- SSH key auth configured (see Raspberry Pi Imager)
- Step 1 on Pi already done:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv git -y
```

## 1. Copy files from Mac

On your Mac (not inside SSH):

```bash
cd ~/Desktop/plant-monitor
scp main.py requirements.txt admin@plant-pi.local:~/plant-monitor/
scp static/index.html static/manifest.json static/icon.svg admin@plant-pi.local:~/plant-monitor/static/
```

Do **not** copy `venv/`, `plants.db`, `readings.csv`, or `__pycache__`.

## 2. Python environment on Pi

```bash
ssh admin@plant-pi.local
mkdir -p ~/plant-monitor/static
cd ~/plant-monitor
python3 -m venv venv
source venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

Smoke test:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Visit `http://plant-pi.local:8000`, then `Ctrl+C`.

## 3. systemd (24/7 service)

```bash
sudo nano /etc/systemd/system/plant-server.service
```

Paste:

```ini
[Unit]
Description=Plant Hydration FastAPI Server
After=network.target

[Service]
User=admin
WorkingDirectory=/home/admin/plant-monitor
Environment=PLANT_API_KEY=your-generated-key-here
ExecStart=/home/admin/plant-monitor/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable plant-server.service
sudo systemctl start plant-server.service
sudo systemctl status plant-server.service
```

Logs: `journalctl -u plant-server.service -f`

For remote Streamlit access, set `PLANT_API_KEY` and expose the API via Cloudflare Tunnel — see [STREAMLIT.md](STREAMLIT.md).

## 4. ESP32 endpoint

On the Pi:

```bash
hostname -I
```

Update `serverName` in [arduino.md](arduino.md) (Sketch B):

```cpp
const char* serverName = "http://10.0.0.43:8000/api/moisture";
```

Upload to the ESP32 from Arduino IDE.

## 5. Verify

- Dashboard: `http://plant-pi.local:8000` or `http://10.0.0.43:8000`
- Test POST from Mac:

```bash
curl -X POST http://plant-pi.local:8000/api/moisture \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -d '{"plant_id":1,"raw_value":2000,"moisture_percentage":45.5}'
```

- CSV grows at `~/plant-monitor/readings.csv` on the Pi

## Updating after code changes

Re-copy files from Mac, then restart the service:

```bash
scp main.py requirements.txt admin@plant-pi.local:~/plant-monitor/
scp static/index.html static/manifest.json static/icon.svg admin@plant-pi.local:~/plant-monitor/static/
ssh admin@plant-pi.local "sudo systemctl restart plant-server.service"
```
