# Remote access (Streamlit Cloud + Cloudflare Tunnel)

View plant moisture from anywhere. The Pi stays at home; Streamlit Cloud pulls data through a public HTTPS tunnel.

## Architecture

```text
ESP32  →  Pi FastAPI (LAN)  ←  Cloudflare Tunnel  ←  Streamlit Cloud  ←  you
```

- **Home LAN:** ESP32 posts to `http://10.0.0.43:8000/api/moisture`
- **Anywhere:** Streamlit app calls `https://your-tunnel-host/api/plants` with an API key

## 1. Generate an API key

On your Mac:

```bash
openssl rand -hex 24
```

Save this value — you will use it in three places: Pi systemd, Streamlit secrets, and the Arduino sketch.

## 2. Enable the API key on the Pi

Edit the systemd service:

```bash
ssh admin@plant-pi.local
sudo nano /etc/systemd/system/plant-server.service
```

Add under `[Service]`:

```ini
Environment=PLANT_API_KEY=your-generated-key-here
```

Redeploy updated code and restart:

```bash
# from Mac
cd ~/Desktop/plant-monitor
scp main.py admin@plant-pi.local:~/plant-monitor/
ssh admin@plant-pi.local "sudo systemctl daemon-reload && sudo systemctl restart plant-server.service"
```

Test (replace URL and key):

```bash
curl -H "X-API-Key: YOUR_KEY" http://plant-pi.local:8000/api/plants
```

## 3. Cloudflare Tunnel on the Pi

### Quick tunnel (no domain — good for first test)

```bash
ssh admin@plant-pi.local
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb
cloudflared tunnel --url http://127.0.0.1:8000
```

Copy the `https://….trycloudflare.com` URL — use it as `PI_API_URL` in Streamlit secrets.  
Note: this URL changes each time you restart the quick tunnel.

### Named tunnel (stable URL — recommended for production)

Requires a domain on Cloudflare (free plan is fine).

```bash
cloudflared tunnel login
cloudflared tunnel create plant-pi
cloudflared tunnel route dns plant-pi plants.yourdomain.com
```

Create `/home/admin/.cloudflared/config.yml`:

```yaml
tunnel: <TUNNEL_UUID>
credentials-file: /home/admin/.cloudflared/<TUNNEL_UUID>.json

ingress:
  - hostname: plants.yourdomain.com
    service: http://127.0.0.1:8000
  - service: http_status:404
```

Install as a service:

```bash
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

Your public API base URL: `https://plants.yourdomain.com`

## 4. Deploy on Streamlit Cloud

1. Push this repo to GitHub (`dvjgenis/plant-monitor`)
2. Go to [share.streamlit.io](https://share.streamlit.io) → **Create app**
3. Repository: `dvjgenis/plant-monitor`, branch `main`, main file: `streamlit_app.py`
4. **Settings → Secrets:**

```toml
PI_API_URL = "https://your-tunnel-hostname"
PLANT_API_KEY = "same-key-as-pi-systemd"
```

5. Deploy and open your public Streamlit URL from phone or laptop.

## 5. Update the ESP32

In Sketch B ([arduino.md](arduino.md)), after `Content-Type`:

```cpp
http.addHeader("X-API-Key", "YOUR_KEY_HERE");
```

Upload to the board. Without this header, POSTs will return **401** once `PLANT_API_KEY` is set on the Pi.

## Troubleshooting

| Symptom | Check |
|---------|--------|
| Streamlit "Could not reach Pi API" | `sudo systemctl status cloudflared` and `plant-server.service` on Pi |
| 401 Unauthorized | API key mismatch between Pi, Streamlit secrets, and Arduino |
| ESP32 Response Code -1 or 401 | Wi-Fi OK? Key header added? Pi reachable on LAN? |
| Quick tunnel URL stopped working | Restart tunnel; update Streamlit `PI_API_URL` secret |

Pi logs: `journalctl -u plant-server.service -f`  
Tunnel logs: `journalctl -u cloudflared -f`
