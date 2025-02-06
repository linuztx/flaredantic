<div align="center">

![Flaredantic Logo](./docs/res/flaredantic.jpg)

# `Flaredantic`

[![PyPI version](https://badge.fury.io/py/flaredantic.svg)](https://badge.fury.io/py/flaredantic)
[![Python Versions](https://img.shields.io/pypi/pyversions/flaredantic.svg)](https://pypi.org/project/flaredantic/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Monthly Downloads](https://pepy.tech/badge/flaredantic/month)](https://pepy.tech/project/flaredantic)

Flaredantic is a Python library that simplifies the process of creating Cloudflare tunnels, making it easy to expose your local services to the internet. It's designed to be a user-friendly alternative to ngrok, localtunnel, and similar services, leveraging Cloudflare's robust infrastructure.

</div>

## 🌟 Features

- 🔌 Zero-configuration tunnels
- 🔒 Secure HTTPS endpoints
- 🚀 Easy-to-use Python API
- 💻 Command-line interface (CLI)
- 📦 Automatic binary management
- 🎯 Cross-platform support (Windows, macOS, Linux)
- 🔄 Context manager support
- 📊 Download progress tracking
- 📝 Detailed logging with verbose mode

## 🎯 Why Flaredantic?

While tools like ngrok are great, Cloudflare tunnels offer several advantages:
- Free and unlimited tunnels
- Better stability and performance
- Cloudflare's security features
- No rate limiting

Flaredantic makes it dead simple to use Cloudflare tunnels in your Python projects!

## 🚀 Installation

```bash
pip install flaredantic
```

After installation, you can use either the CLI command `flare` or the Python API.

## 📖 Quick Start

### Command Line Usage

The simplest way to create a tunnel is using the CLI:

```bash
# Basic usage - expose port 8080 with verbose output
flare --port 8080 -v
```

CLI Options:
```
-p, --port     Local port to expose (required)
-t, --timeout  Tunnel start timeout in seconds (default: 30)
-v, --verbose  Show detailed progress output
```

### Python API Usage

#### Basic Usage

```python
from flaredantic import FlareTunnel, FlareConfig

# Create a tunnel for your local server running on port 8000
config = FlareConfig(port=8080)
with FlareTunnel(config) as tunnel:
    print(f"Your service is available at: {tunnel.tunnel_url}")
    # Your application code here
    input("Press Enter to stop the tunnel...")
```

### Custom Configuration

```python
from flaredantic import FlareTunnel, FlareConfig
from pathlib import Path

# Configure tunnel with custom settings
config = FlareConfig(
    port=8080,
    bin_dir=Path.home() / ".my-tunnels",
    timeout=60,
    verbose=True  # Enable detailed logging
)

# Create and start tunnel
with FlareTunnel(config) as tunnel:
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

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| port | int | Required | Local port to expose |
| bin_dir | Path | ~/.flaredantic | Directory for cloudflared binary |
| timeout | int | 30 | Tunnel start timeout in seconds |
| verbose | bool | False | Show detailed progress and debug output |

## 📚 More Examples

For more detailed examples and use cases, check out more [examples](docs/examples/Examples.md).
- HTTP Server example
- Django integration
- FastAPI application
- Flask application
- Custom configuration
- Error handling
- Development vs Production setup

---