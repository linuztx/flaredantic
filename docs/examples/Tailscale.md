# Flaredantic Tailscale Funnel Examples 📚

This document provides various examples of how to use Flaredantic with Tailscale Funnel in different scenarios.

## How It Works

Tailscale Funnel exposes a local port to the internet at `https://<machine>.<tailnet>.ts.net`. Flaredantic picks the Tailscale node to serve it from:

- **Tailscale is installed and running** (Linux, macOS, Windows): the tunnel is served from that machine, so no extra login is needed. Flaredantic never logs it in, brings it up or changes its settings.
- **No Tailscale is running** (Linux only): Flaredantic downloads the Tailscale binaries to `~/.flaredantic` and runs its own node in userspace networking mode, with its state in `~/.flaredantic/tailscale-state`. You log in once; later runs reuse the login.

The Funnel only lives as long as the tunnel: it is removed as soon as the tunnel stops.

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

### Multiple Tunnels
With the Tailscale installed on your machine, Funnel can listen on ports 443, 8443 and 10000, so up to three tunnels can run at once:
```python
from flaredantic import TailscaleTunnel, TailscaleConfig

with TailscaleTunnel(TailscaleConfig(port=8000)) as app, \
     TailscaleTunnel(TailscaleConfig(port=9000, https_port=8443)) as admin:
    print(f"App:   {app.tunnel_url}")    # https://<machine>.<tailnet>.ts.net
    print(f"Admin: {admin.tunnel_url}")  # https://<machine>.<tailnet>.ts.net:8443
    input("Press Enter to stop...")
```

The node Flaredantic runs itself serves one tunnel at a time. To run more, give each tunnel its own `state_dir` and `hostname` so it runs as a separate node.

## Login

### Browser Login
The first time Flaredantic runs its own node, it prints a login link:
```
[INFO] To authenticate, visit: https://login.tailscale.com/a/...
```
Open it in any browser, on any device, and log in to your Tailscale account.

The first time Funnel is used in a tailnet, a tailnet admin also has to allow it:
```
[INFO] Funnel is not enabled on your tailnet. To enable, visit: https://login.tailscale.com/f/funnel?node=...
```

Flaredantic waits up to `login_timeout` seconds (300 by default) for both.

### Headless Login with an Auth Key
On servers, notebooks and CI, log in with an [auth key](https://tailscale.com/kb/1085/auth-keys) instead. Generate one in the [admin console](https://login.tailscale.com/admin/settings/keys):
```python
import os
from flaredantic import TailscaleTunnel, TailscaleConfig

config = TailscaleConfig(
    port=8080,
    auth_key=os.environ["TS_AUTHKEY"],
    hostname="my-server"  # Tunnel URL: https://my-server.<tailnet>.ts.net
)

with TailscaleTunnel(config) as tunnel:
    print(f"Tunnel URL: {tunnel.tunnel_url}")
    input("Press Enter to stop...")
```

The key is only used for the first login. Passing `auth_key="file:/path/to/key"` reads it from a file, which keeps the key out of the process list.

### Separate Node on a Machine with Tailscale
Set `use_system=False` to run Flaredantic's own node even when Tailscale is installed, for example to give the tunnel its own name (Linux only):
```python
from flaredantic import TailscaleTunnel, TailscaleConfig

config = TailscaleConfig(port=8080, use_system=False, hostname="demo")

with TailscaleTunnel(config) as tunnel:
    print(f"Tunnel URL: {tunnel.tunnel_url}")  # https://demo.<tailnet>.ts.net
    input("Press Enter to stop...")
```

## Account Management

### Changing Accounts / Logging Out
If the tunnel runs on the Tailscale installed on your machine, use the Tailscale app or `tailscale logout` / `tailscale switch`.

For the node Flaredantic runs itself, delete its state directory (or your custom `state_dir`). The next run asks you to log in again:
```bash
rm -rf ~/.flaredantic/tailscale-state
```

The old machine stays in your tailnet until you remove it from the [Machines page](https://login.tailscale.com/admin/machines).

## Advanced Examples

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

### Showing the Login Link in Your App
Login and Funnel approval links are sent as `INFO` notifications with the link in `data["url"]`, so a web app can show them to the user:
```python
from flaredantic import TailscaleTunnel, TailscaleConfig, NotifyEvent, NotifyData, notifier

def on_event(event: NotifyData) -> None:
    if event.event == NotifyEvent.INFO and event.data:
        print(f"Action needed: {event.message}")
    elif event.event == NotifyEvent.TUNNEL_URL:
        print(f"Tunnel ready: {event.data['url']}")

notifier.subscribe(on_event)

with TailscaleTunnel(TailscaleConfig(port=8000)) as tunnel:
    input("Press Enter to stop...")
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
        except TailscaleError as e:
            if attempt == max_retries - 1:
                raise
            print(f"Attempt {attempt + 1} failed: {e}. Retrying...")
            time.sleep(2)
```

`TailscaleError` covers both `TailscaleDownloadError` and `TailscaleTunnelError`.

## Common Issues and Solutions

### Access Denied (Linux)
Only root or the Tailscale operator can change Funnel settings. Allow your user once:
```bash
sudo tailscale set --operator=$USER
```

### Tailscale Is Not Connected
Flaredantic won't log in or bring up the Tailscale installed on your machine. Run `tailscale up` or connect from the Tailscale app, then try again.

### Funnel Not Available
- `Funnel is not enabled on your tailnet`: open the printed link as a tailnet admin.
- `HTTPS must be enabled` or `"funnel" node attribute not set`: see the [Funnel setup guide](https://tailscale.com/kb/1223/funnel).

### Port Already in Use
`listener already exists for port 443` means something on this machine already serves that port, such as another tunnel or `tailscale serve`. Use `https_port=8443` or `https_port=10000`, or check `tailscale funnel status`.

### Node Already Running
`A Tailscale node started by flaredantic is already running` means another tunnel is using the same `state_dir`. Stop it, or give each tunnel its own `state_dir` and `hostname`.
