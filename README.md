# Flaredantic ☁️

[![PyPI version](https://badge.fury.io/py/flaredantic.svg)](https://badge.fury.io/py/flaredantic)
[![Python Versions](https://img.shields.io/pypi/pyversions/flaredantic.svg)](https://pypi.org/project/flaredantic/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Flaredantic is a Python library that simplifies the process of creating Cloudflare tunnels, making it easy to expose your local services to the internet. It's designed to be a user-friendly alternative to ngrok, localtunnel, and similar services, leveraging Cloudflare's robust infrastructure.

## 🌟 Features

- 🔌 Zero-configuration tunnels
- 🔒 Secure HTTPS endpoints
- 🚀 Easy-to-use Python API
- 📦 Automatic binary management
- 🎯 Cross-platform support (Windows, macOS, Linux)
- 🔄 Context manager support
- 📊 Download progress tracking

## 🎯 Why Flaredantic?

While tools like ngrok are great, Cloudflare tunnels offer several advantages:
- Free and unlimited tunnels
- Better stability and performance
- Cloudflare's security features
- No rate limiting

Flaredantic makes it dead simple to use Cloudflare tunnels in your Python projects!

![Flaredantic Demo](./docs/res/demo.png)

## 🚀 Installation

```bash
pip install flaredantic
```

## 📖 Quick Start

### Basic Usage

```python
from flaredantic import FlareTunnel, TunnelConfig

# Create a tunnel for your local server running on port 8000
config = TunnelConfig(port=8000)
with FlareTunnel(config) as tunnel:
    print(f"Your service is available at: {tunnel.tunnel_url}")
    # Your application code here
    input("Press Enter to stop the tunnel...")
```

### Custom Configuration

```python
from flaredantic import FlareTunnel
from pathlib import Path

# Configure tunnel with custom settings
tunnel = FlareTunnel({
    "port": 3000,
    "bin_dir": Path.home() / ".my-tunnels",
    "timeout": 60,
    "quiet": True
})

# Start the tunnel
tunnel.start()
print(f"Access your service at: {tunnel.tunnel_url}")

# Stop when done
tunnel.stop()
```

### Async Web Application Example (FastAPI)

```python
from fastapi import FastAPI, BackgroundTasks
from flaredantic import FlareTunnel
import uvicorn
import threading

app = FastAPI()
tunnel = None

@app.on_event("startup")
async def startup_event():
    global tunnel
    tunnel = FlareTunnel({"port": 8000})
    tunnel.start()
    print(f"API available at: {tunnel.tunnel_url}")

@app.on_event("shutdown")
async def shutdown_event():
    if tunnel:
        tunnel.stop()

@app.get("/")
def read_root():
    return {"status": "online"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

## ⚙️ Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| port | int | Required | Local port to expose |
| bin_dir | Path | ~/.flaredantic | Directory for cloudflared binary |
| timeout | int | 30 | Tunnel start timeout in seconds |
| quiet | bool | False | Suppress progress output |

## 📚 More Examples

For more detailed examples and use cases, check out our [Examples Documentation](docs/examples/Examples.md), which includes:

- HTTP Server examples
- Django integration
- FastAPI applications
- Flask applications
- Custom configurations
- Error handling
- Development vs Production setups
- And more!

---