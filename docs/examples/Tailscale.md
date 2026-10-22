# Flaredantic Tailscale Funnel Examples 📚

This document provides various examples of how to use Flaredantic with Tailscale Funnel in different scenarios.

## How It Works

Tailscale Funnel publishes a local port on the internet at `https://<hostname>.<tailnet>.ts.net`.

- **Linux**: Flaredantic downloads the official `tailscale` and `tailscaled` binaries to `~/.flaredantic/tailscale` and runs a private `tailscaled` in userspace networking mode. It needs no root and leaves any existing Tailscale install alone. It joins your tailnet as its own machine, named `flaredantic` by default.
- **macOS / Windows**: Flaredantic uses the installed [Tailscale app](https://tailscale.com/download), so the URL uses that machine's name.

On the first run you get a login link. If Funnel is not enabled for your tailnet yet, you get a second link to enable it. Both are one-time steps: the login is saved and reused on later runs.

## Basic Examples

### Simple HTTP Server
```python
from http.server import HTTPServer, SimpleHTTPRequestHandler
from flaredantic import TailscaleTunnel, TailscaleConfig
import threading
import time

# Create a basic HTTP server
server = HTTPServer(('localhost', 8000), SimpleHTTPRequestHandler)
server_thread = threading.Thread(target=server.serve_forever, daemon=True)
server_thread.start()

# Create and start tunnel
config = TailscaleConfig(port=8000)
with TailscaleTunnel(config) as tunnel:
    print(f"Server accessible at: {tunnel.tunnel_url}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping server...")
```

### Custom Hostname
The hostname becomes the first part of the URL:
```python
from flaredantic import TailscaleTunnel, TailscaleConfig

config = TailscaleConfig(
    port=8080,
    hostname="my-app",  # https://my-app.<tailnet>.ts.net
    verbose=True
)

with TailscaleTunnel(config) as tunnel:
    print(f"Tunnel URL: {tunnel.tunnel_url}")
    input("Press Enter to stop...")
```

### Login Without a Browser (Auth Key)
For servers, containers and CI, create an auth key in the [admin console](https://login.tailscale.com/admin/settings/keys) and pass it in:
```python
import os
from flaredantic import TailscaleTunnel, TailscaleConfig

config = TailscaleConfig(
    port=8080,
    auth_key=os.environ["MY_TAILSCALE_KEY"]
)

with TailscaleTunnel(config) as tunnel:
    print(f"Tunnel URL: {tunnel.tunnel_url}")
    input("Press Enter to stop...")
```

If `auth_key` is not set, the `TS_AUTHKEY` environment variable is used, which also works from the CLI:
```bash
TS_AUTHKEY=tskey-auth-... flare --port 8080 --tunnel tailscale
```

The key is only needed for the first login, later runs reuse the saved login. For short-lived environments, a reusable ephemeral key keeps your machine list clean, since ephemeral machines are removed after they go offline.

### Using an Existing Tailscale Install
To publish through the machine's own Tailscale node instead of a private one:
```python
from flaredantic import TailscaleTunnel, TailscaleConfig

config = TailscaleConfig(port=8080, use_system=True)

with TailscaleTunnel(config) as tunnel:
    print(f"Tunnel URL: {tunnel.tunnel_url}")  # https://<machine-name>.<tailnet>.ts.net
    input("Press Enter to stop...")
```

- This is always the case on macOS and Windows; make sure the Tailscale app is running.
- On Linux, this needs root, or running `sudo tailscale set --operator=$USER` once.
- Flaredantic does not change the settings of your install. It only runs `tailscale up` when Tailscale is logged out or disconnected.

## Account Management

### Files
The private `tailscaled` (Linux) keeps everything in `~/.flaredantic/tailscale` (or `tailscale` inside your custom `bin_dir`):

- `tailscale`, `tailscaled`: the binaries
- `state/`: login state and HTTPS certificates
- `tailscaled.log`: daemon log of the last run

### Changing Accounts / Logging Out
While no tunnel is running, delete the saved state:
```bash
rm -rf ~/.flaredantic/tailscale/state
```

The next run will prompt you for a new login. Remove the old machine from the [machines page](https://login.tailscale.com/admin/machines) if it is still listed.

**To check the status while a tunnel is running:**
```bash
cd ~/.flaredantic/tailscale/
./tailscale --socket=tailscaled.sock status
```

## Advanced Examples

### Login and Enable Links in a Frontend
The login and Funnel enablement links are sent as `INFO` notifications with a `url`, so a web UI can show them:
```python
from flaredantic import TailscaleTunnel, TailscaleConfig, NotifyEvent, notifier

def on_event(event):
    if event.event == NotifyEvent.INFO and event.data and "url" in event.data:
        print(f"Action needed, open: {event.data['url']}")
    elif event.event == NotifyEvent.TUNNEL_URL:
        print(f"Tunnel ready: {event.data['url']}")

notifier.subscribe(on_event)

with TailscaleTunnel(TailscaleConfig(port=8080)) as tunnel:
    input("Press Enter to stop...")
```

### FastAPI Integration
```python
import uvicorn
from fastapi import FastAPI
from flaredantic import TailscaleTunnel, TailscaleConfig

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "online", "provider": "Tailscale Funnel"}

def start_tunnel():
    config = TailscaleConfig(port=8000)
    tunnel = TailscaleTunnel(config)
    url = tunnel.start()
    print(f"FastAPI app available at: {url}")
    return tunnel

if __name__ == "__main__":
    # Start tunnel in background
    tunnel = start_tunnel()

    try:
        uvicorn.run(app, host="127.0.0.1", port=8000)
    finally:
        tunnel.stop()
```

## Error Handling Examples

### Connection Retry Logic
```python
from flaredantic import TailscaleTunnel, TailscaleConfig, TailscaleError
import time

def create_tunnel_with_retry(port: int, max_retries: int = 3):
    config = TailscaleConfig(port=port, verbose=True)

    for attempt in range(max_retries):
        try:
            tunnel = TailscaleTunnel(config)
            tunnel.start()
            return tunnel
        except TailscaleError as e:  # TailscaleDownloadError or TailscaleTunnelError
            if attempt == max_retries - 1:
                raise
            print(f"Attempt {attempt + 1} failed: {e}. Retrying...")
            time.sleep(2)
```

## Common Issues and Solutions

### Funnel Is Not Enabled
On first use you may see `Funnel is not enabled for your tailnet. Open: https://login.tailscale.com/f/funnel?node=...`. Open the link and enable Funnel, Flaredantic then carries on (run it again if it already stopped).

Funnel needs MagicDNS and HTTPS certificates, which you can turn on in the [DNS settings](https://login.tailscale.com/admin/dns), and the `funnel` attribute in your tailnet policy file:
```json
"nodeAttrs": [
  {
    "target": ["autogroup:member"],
    "attr": ["funnel"]
  }
]
```

### URL Not Reachable Right Away
- After Funnel is enabled for the first time, it can take a few minutes until the public DNS name resolves.
- The first request can be slow while the HTTPS certificate is issued.

### Unexpected Hostname
If the URL ends up as `flaredantic-1.<tailnet>.ts.net`, another machine already uses the name. Remove the old machine from the [machines page](https://login.tailscale.com/admin/machines) or choose another `hostname`.

### Access Denied on Linux with `use_system=True`
The system `tailscaled` only lets root or its operator change the Funnel config. Run `sudo tailscale set --operator=$USER` once, or use the default private daemon instead.

### Daemon Problems
If the private daemon fails to start, check `~/.flaredantic/tailscale/tailscaled.log`.
