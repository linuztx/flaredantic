# Flaredantic Microsoft Dev Tunnels Examples 📚

This document provides various examples of how to use Flaredantic with Microsoft Dev Tunnelss in different scenarios.

## Basic Examples

### Simple HTTP Server
```python
from http.server import HTTPServer, SimpleHTTPRequestHandler
from flaredantic import MicrosoftTunnel, MicrosoftConfig
import threading
import time

# Create a basic HTTP server
server = HTTPServer(('localhost', 8000), SimpleHTTPRequestHandler)
server_thread = threading.Thread(target=server.serve_forever, daemon=True)
server_thread.start()

# Create and start tunnel
config = MicrosoftConfig(port=8000)
with MicrosoftTunnel(config) as tunnel:
    print(f"Server accessible at: {tunnel.tunnel_url}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping server...")
```

### Custom Tunnel ID
You can reuse a specific tunnel ID if available:
```python
from flaredantic import MicrosoftTunnel, MicrosoftConfig

config = MicrosoftConfig(
    port=8080,
    tunnel_id="my-custom-tunnel-id",
    verbose=True
)

with MicrosoftTunnel(config) as tunnel:
    print(f"Tunnel URL: {tunnel.tunnel_url}")
    input("Press Enter to stop...")
```

## Account Management

### Changing Accounts / Logging Out
If you need to switch accounts or force a re-login, you can manually use the binary that `flaredantic` manages.

The binary is located in `~/.flaredantic/microsoft` (or your custom `bin_dir`).

**To logout:**
```bash
# Navigate to the binary directory
cd ~/.flaredantic/

# Run the logout command
./devtunnel user logout
```

After logging out, the next time you run your Python script with `MicrosoftTunnel`, it will prompt you for a new device login.

**To check current login status:**
```bash
cd ~/.flaredantic/
./devtunnel user show
```

## Advanced Examples

### Device Login Flow
Microsoft Dev Tunnelss support device login authentication (enabled by default):
```python
from flaredantic import MicrosoftTunnel, MicrosoftConfig

config = MicrosoftConfig(
    port=8080,
    device_login=True,  # Enable device login flow
    verbose=True       # Show login code and instructions
)

# First run will prompt: "Browse to https://github.com/login/device and enter code: XXXX"
with MicrosoftTunnel(config) as tunnel:
    print(f"Tunnel URL: {tunnel.tunnel_url}")
    input("Press Enter to stop...")
```

### FastAPI Integration
```python
import uvicorn
from fastapi import FastAPI
from flaredantic import MicrosoftTunnel, MicrosoftConfig
import threading

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "online", "provider": "Microsoft Dev Tunnels"}

def start_tunnel():
    config = MicrosoftConfig(port=8000)
    tunnel = MicrosoftTunnel(config)
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

### Django Integration
```python
import os
import sys
import time
import threading
from flaredantic import MicrosoftTunnel, MicrosoftConfig
from django.core.management import execute_from_command_line

def run_tunnel():
    config = MicrosoftConfig(port=8000)
    with MicrosoftTunnel(config) as tunnel:
        print(f"Django site available at: {tunnel.tunnel_url}")
        # Keep tunnel alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    
    # Start tunnel in background
    tunnel_thread = threading.Thread(target=run_tunnel, daemon=True)
    tunnel_thread.start()
    
    execute_from_command_line(sys.argv)
```

## Error Handling Examples

### Connection Retry Logic
```python
from flaredantic import MicrosoftTunnel, MicrosoftConfig, TunnelError
import time

def create_tunnel_with_retry(port: int, max_retries: int = 3):
    config = MicrosoftConfig(port=port, verbose=True)
    
    for attempt in range(max_retries):
        try:
            tunnel = MicrosoftTunnel(config)
            tunnel.start()
            return tunnel
        except TunnelError as e:
            if attempt == max_retries - 1:
                raise
            print(f"Attempt {attempt + 1} failed: {e}. Retrying...")
            time.sleep(2)
```

## Common Issues and Solutions

### Login Required
If the tunnel fails to start with login errors:
1. Ensure `verbose=True` is set to see the login code.
2. Complete the device login flow at https://github.com/login/device.
3. The token is cached locally, so subsequent runs won't require login.

### Port Conflicts
If you see "hosting port" errors:
- Ensure the local service is running on the specified port.
- Check if another tunnel is already using the same `tunnel_id`.
