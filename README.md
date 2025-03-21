<div align="center">

![Flaredantic Logo](./docs/res/flaredantic.jpg)

# `Flaredantic`

[![PyPI version](https://badge.fury.io/py/flaredantic.svg)](https://badge.fury.io/py/flaredantic)
[![Python Versions](https://img.shields.io/pypi/pyversions/flaredantic.svg)](https://pypi.org/project/flaredantic/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Monthly Downloads](https://pepy.tech/badge/flaredantic/month)](https://pepy.tech/project/flaredantic)

Flaredantic is a Python library that simplifies the process of creating tunnels to expose your local services to the internet. It supports both Cloudflare and Serveo tunneling services, making it a user-friendly alternative to ngrok, localtunnel, and similar tools.

</div>

## 🌟 Features

- 🔌 Zero-configuration tunnels
- 🔒 Secure HTTPS endpoints
- 🚀 Easy-to-use Python API
- 💻 Command-line interface (CLI)
- 📦 Automatic binary management
- 🔄 Multiple tunnel providers (Cloudflare, Serveo)
- 🌐 TCP forwarding support (Serveo)
- 🎯 Cross-platform support (Windows, macOS, Linux)
- 📱 Android support via Termux
- 🔄 Context manager support
- 📊 Download progress tracking
- 📝 Detailed logging with verbose mode

## 🎯 Why Flaredantic?

While tools like ngrok are great, Flaredantic offers several advantages:
- Free and unlimited tunnels
- Multiple tunnel providers to choose from
- Better stability and performance
- TCP forwarding with Serveo
- No rate limiting

Flaredantic makes it dead simple to use tunnels in your Python projects!

## 🚀 Installation

```bash
pip install flaredantic
```

After installation, you can use either the CLI command `flare` or the Python API.

## 📖 Quick Start

### Command Line Usage

The simplest way to create a tunnel is using the CLI:

```bash
# Basic usage with Cloudflare (default) - expose port 8080 with verbose output
flare --port 8080 -v

# Use Serveo tunnel instead
flare --port 8080 --tunnel serveo

# TCP forwarding with Serveo
flare --port 5432 --tcp
```

CLI Options:
```
-p, --port     Local port to expose (required)
-t, --timeout  Tunnel start timeout in seconds (default: 30)
-v, --verbose  Show detailed progress output
--tunnel       Tunnel provider to use [cloudflare, serveo] (default: cloudflare)
--tcp          Use Serveo with TCP forwarding (overrides --tunnel)
```

### Python API Usage

#### Basic Usage with Cloudflare

```python
from flaredantic import FlareTunnel, FlareConfig

# Create a tunnel for your local server running on port 8000
config = FlareConfig(port=8080)
with FlareTunnel(config) as tunnel:
    print(f"Your service is available at: {tunnel.tunnel_url}")
    # Your application code here
    input("Press Enter to stop the tunnel...")
```

#### Basic Usage with Serveo

```python
from flaredantic.tunnel.serveo import ServeoTunnel, ServeoConfig

# Create a tunnel using Serveo
config = ServeoConfig(port=8080)
with ServeoTunnel(config) as tunnel:
    print(f"Your service is available at: {tunnel.tunnel_url}")
    # Your application code here
    input("Press Enter to stop the tunnel...")
```

#### TCP Forwarding with Serveo

```python
from flaredantic.tunnel.serveo import ServeoTunnel, ServeoConfig

# Create a TCP tunnel using Serveo
config = ServeoConfig(port=5432, tcp=True)
with ServeoTunnel(config) as tunnel:
    print(f"TCP tunnel available at: {tunnel.tunnel_url}")
    # Your application code here
    input("Press Enter to stop the tunnel...")
```

### Custom Configuration

```python
from flaredantic import FlareTunnel, FlareConfig
from flaredantic.tunnel.serveo import ServeoTunnel, ServeoConfig
from pathlib import Path

# Configure Cloudflare tunnel with custom settings
cloudflare_config = FlareConfig(
    port=8080,
    bin_dir=Path.home() / ".my-tunnels",
    timeout=60,
    verbose=True  # Enable detailed logging
)

# Configure Serveo tunnel with custom settings
serveo_config = ServeoConfig(
    port=8080,
    ssh_dir=Path.home() / ".my-tunnels/ssh",  # Custom SSH directory
    timeout=60,
    verbose=True  # Enable detailed logging
)

# Create and start tunnel (choose one)
with FlareTunnel(cloudflare_config) as tunnel:
    print(f"Access your service at: {tunnel.tunnel_url}")
    input("Press Enter to stop the tunnel...")
```

### Flask Application
```python
from flask import Flask
from flaredantic import FlareTunnel, FlareConfig
import threading

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World!'

def run_tunnel():
    config = FlareConfig(
        port=5000,
        verbose=True  # Enable logging for debugging
    )
    with FlareTunnel(config) as tunnel:
        print(f"Flask app available at: {tunnel.tunnel_url}")
        app.run(port=5000)

if __name__ == '__main__':
    threading.Thread(target=run_tunnel).start()
```

## ⚙️ Configuration Options

### Cloudflare Tunnel Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| port | int | Required | Local port to expose |
| bin_dir | Path | ~/.flaredantic | Directory for cloudflared binary |
| timeout | int | 30 | Tunnel start timeout in seconds |
| verbose | bool | False | Show detailed progress and debug output |

### Serveo Tunnel Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| port | int | Required | Local port to expose |
| ssh_dir | Path | ~/.flaredantic/ssh | Directory for SSH configuration |
| timeout | int | 30 | Tunnel start timeout in seconds |
| verbose | bool | False | Show detailed progress and debug output |
| tcp | bool | False | Enable TCP forwarding instead of HTTP |

## 📦 Requirements

- **Cloudflare tunnel**: No additional requirements (binary auto-downloaded)
- **Serveo tunnel**: Requires SSH client to be installed

> **❗️Note:** Serveo servers might occasionally be unavailable as they are a free service. Flaredantic automatically detects when Serveo is down and provides a clear error message. Consider using Cloudflare tunnels if you need guaranteed availability.

## 📚 More Examples

For more detailed examples and use cases, check out our examples:
- [Cloudflare Examples](docs/examples/Cloudflare.md) - HTTP Server, Django, FastAPI, Flask
- [Serveo Examples](docs/examples/Serveo.md) - HTTP, TCP, SSH forwarding, database access

---