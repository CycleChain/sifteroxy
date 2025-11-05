# Sifteroxy

**sift(er) + proxy** — fetch, sift, verify, and publish working proxies *atomically*.

---

## 🚀 What is it?

Sifteroxy is a tiny, fast, and reliable proxy list **collector + validator**. It pulls free proxies from multiple public sources, deduplicates them, **validates** via real HTTP(S) requests, and **atomically publishes** a clean `TXT` list you can plug into other tools.

### Why Sifteroxy?

* **Atomic publish**: never serve half‑written files (tmp → fsync → rename).
* **Preview backup**: previous good file is kept as `*.prev`.
* **Parallel validation** with configurable concurrency.
* **Protocol filters**: HTTP, HTTPS, SOCKS4, SOCKS5.
* **Metrics JSON** (optional): latency, total time, status, count.
* **Cron/systemd friendly**: ready‑made scripts.

---

## 🧰 Installation

Requires **Python 3.9+**.

### Quick Installation (Recommended)

For automated systemd service/timer setup:

```bash
sudo ./install.sh
sudo ./active.sh  # Activate the timer
```

This will:
- Install Python dependencies
- Copy files to `/opt/sifteroxy`
- Set up systemd service and timer
- Configure automatic runs every 30 minutes

### Manual Installation

#### 1. Install Dependencies

```bash
pip install -U requests "requests[socks]"
```

#### 2. Copy Files

```bash
sudo mkdir -p /opt/sifteroxy
sudo cp sifteroxy.py sources.json proxy_update.sh /opt/sifteroxy/
sudo chmod +x /opt/sifteroxy/sifteroxy.py
sudo chmod +x /opt/sifteroxy/proxy_update.sh
```

#### 3. Install Systemd Service & Timer

```bash
sudo cp sifteroxy.service /etc/systemd/system/
sudo cp sifteroxy.timer /etc/systemd/system/
sudo systemctl daemon-reload
```

#### 4. Activate Timer

```bash
sudo ./active.sh
# Or manually:
sudo systemctl enable --now sifteroxy.timer
```

#### 5. Verify Installation

```bash
sudo systemctl status sifteroxy.timer
sudo systemctl status sifteroxy.service
```

### Deactivate Timer

To stop and disable automatic runs:

```bash
sudo ./deactive.sh
# Or manually:
sudo systemctl stop sifteroxy.timer
sudo systemctl disable sifteroxy.timer
```

---

## ✨ Quick Start

```bash
# Default: all protocols, atomic publish to ./proxies_alive.txt
python3 sifteroxy.py

# Only HTTP/HTTPS, higher concurrency, custom output
python3 sifteroxy.py --protocols http,https --concurrency 200 --out http_alive.txt

# Only SOCKS proxies, strict timeout, custom test URL
python3 sifteroxy.py --protocols socks4,socks5 --timeout 3 --test-url https://ifconfig.me

# Also write metrics to JSON
python3 sifteroxy.py --metrics metrics.json

# English language, sort fastest to slowest (default)
python3 sifteroxy.py --language en --order desc

# Turkish language, sort slowest to fastest
python3 sifteroxy.py --language tr --order asc
```

**Atomic publish + preview** (built‑in):

* Writes to `out.tmp` → `fsync(file)` → optional `out.prev` → `rename(tmp→out)` → `fsync(dir)`.
* Readers always see either the **old complete** or the **new complete** file.

Toggle preview:

```bash
python3 sifteroxy.py --out /path/alive.txt --no-preview  # disables out.prev
```

**Language & Sorting**:

* Use `--language en` for English log messages (default: Turkish)
* Use `--order desc` to sort proxies from fastest to slowest (default)
* Use `--order asc` to sort proxies from slowest to fastest
* Progress percentage is shown during validation

---

## ⚙️ CLI Options

* `--protocols http,https,socks4,socks5`
* `--timeout 5`
* `--concurrency 128`
* `--test-url https://httpbin.org/ip`
* `--no-tls-verify`
* `--out proxies_alive.txt`
* `--metrics metrics.json`
* `--max-sources 0` (limit per protocol)
* `--no-preview` (skip creating `*.prev`)
* `--log-level INFO|DEBUG|WARNING|ERROR`
* `--language tr|en` (default: `tr`) - Language for log messages
* `--order desc|asc` (default: `desc`) - Sort order: `desc` = fastest to slowest, `asc` = slowest to fastest

---

## ⏱️ Cron & systemd

**Cron (every 10 min):**

```
*/10 * * * * /opt/proxy-manager/proxy_update.sh
```

**systemd service:**

```
[Unit]
Description=Sifteroxy fetch & validate (atomic publish)
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
WorkingDirectory=/opt/proxy-manager
ExecStart=/opt/proxy-manager/proxy_update.sh
Nice=5
```

**systemd timer:**

```
[Unit]
Description=Run Sifteroxy periodically

[Timer]
OnBootSec=5min
OnUnitActiveSec=30min
AccuracySec=1min
Persistent=true

[Install]
WantedBy=timers.target
```

---

## 📚 Sources

Sifteroxy uses several public, community‑maintained raw lists (e.g., popular GitHub repos). Proxy sources are configured in `sources.json` file in the project root. You can edit this JSON file to add, remove, or modify source URLs for each protocol (http, https, socks4, socks5).

The `sources.json` file has the following structure:
```json
{
  "http": ["url1", "url2", ...],
  "https": ["url1", "url2", ...],
  "socks4": ["url1", "url2", ...],
  "socks5": ["url1", "url2", ...]
}
```

If `sources.json` is not found, the script will fall back to default sources.

---

## 🛡️ Legal

Use Sifteroxy **only** for lawful purposes and with systems you are authorized to test. You are responsible for compliance with all applicable laws and terms of service.

---

## 🤝 Contributing

PRs & issues are welcome. Keep changes small, documented, and covered by basic tests. Follow conventional commits if possible.


---

## Branding

* **Name:** Sifteroxy (sift(er) + proxy)
* **Repo:** `sifteroxy`
* **CLI:** `sifteroxy` (alias: `siftx`)
* **Tagline:** *“fetch, sift, verify, publish — atomically.”*