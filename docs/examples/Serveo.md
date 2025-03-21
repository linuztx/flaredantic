# Flaredantic Serveo Examples 📚

This document provides various examples of how to use Flaredantic with Serveo tunnels in different scenarios.

## Basic Examples

### Simple HTTP Server
```python
from http.server import HTTPServer, SimpleHTTPRequestHandler
from flaredantic import ServeoTunnel, ServeoConfig

# Create a basic HTTP server
server = HTTPServer(('localhost', 8000), SimpleHTTPRequestHandler)

# Create and start tunnel
config = ServeoConfig(port=8000)
with ServeoTunnel(config) as tunnel:
    print(f"Server accessible at: {tunnel.tunnel_url}")
    server.serve_forever()
```

### TCP Database Connection
```python
from flaredantic import ServeoTunnel, ServeoConfig
import psycopg2

# Create TCP tunnel to a PostgreSQL database
config = ServeoConfig(port=5432, tcp=True)
with ServeoTunnel(config) as tunnel:
    print(f"Database accessible at: {tunnel.tunnel_url}")
    
    # Extract host and port from tunnel URL
    host, port_str = tunnel.tunnel_url.replace("serveo.net:", "").split(":")
    port = int(port_str)
    
    # Connect to your database through the tunnel
    conn = psycopg2.connect(
        host="serveo.net",
        port=port,
        database="mydatabase",
        user="postgres",
        password="password"
    )
    
    # Use connection...
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    record = cursor.fetchone()
    print(f"Database version: {record[0]}")
    
    # Close connection
    cursor.close()
    conn.close()
```

### Django Development Server
```python
from flaredantic import ServeoTunnel, ServeoConfig
import subprocess

# Start Django development server
django_process = subprocess.Popen(['python', 'manage.py', 'runserver', '8000'])

# Create tunnel to Django server
config = ServeoConfig(
    port=8000,
    verbose=True  # Enable logging for debugging
)
with ServeoTunnel(config) as tunnel:
    print(f"Django site available at: {tunnel.tunnel_url}")
    try:
        django_process.wait()
    finally:
        django_process.terminate()
```

## Advanced Examples

### FastAPI with Background Tasks
```python
from fastapi import FastAPI
from flaredantic import ServeoTunnel, ServeoConfig
import uvicorn

app = FastAPI()
tunnel = None

@app.on_event("startup")
async def startup_event():
    global tunnel
    config = ServeoConfig(
        port=8000,
        verbose=True  # Enable logging for debugging
    )
    tunnel = ServeoTunnel(config)
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

### Flask Application
```python
from flask import Flask
from flaredantic import ServeoTunnel, ServeoConfig
import threading

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World!'

def run_tunnel():
    config = ServeoConfig(
        port=5000,
        verbose=True  # Enable logging for debugging
    )
    with ServeoTunnel(config) as tunnel:
        print(f"Flask app available at: {tunnel.tunnel_url}")
        app.run(port=5000)

if __name__ == '__main__':
    threading.Thread(target=run_tunnel).start()
```

## TCP Forwarding Examples

### SSH Server Access
```python
from flaredantic import ServeoTunnel, ServeoConfig
import subprocess

# Create a TCP tunnel to local SSH server (usually port 22)
config = ServeoConfig(port=22, tcp=True)
with ServeoTunnel(config) as tunnel:
    print(f"SSH server accessible at: {tunnel.tunnel_url}")
    
    # Example command to show connection string
    host, port = tunnel.tunnel_url.split(":")
    port = port.strip()
    print(f"Connect using: ssh -p {port} your-username@{host}")
    
    # Keep tunnel open until user presses Enter
    input("Press Enter to close the tunnel...")
```

### Redis Server Access
```python
from flaredantic import ServeoTunnel, ServeoConfig
import redis
import time

# Create a TCP tunnel to local Redis server
config = ServeoConfig(port=6379, tcp=True)
with ServeoTunnel(config) as tunnel:
    print(f"Redis server accessible at: {tunnel.tunnel_url}")
    
    # Extract port from tunnel URL
    host, port_str = tunnel.tunnel_url.split(":")
    port = int(port_str)
    
    # Connect to Redis through the tunnel
    r = redis.Redis(host=host, port=port)
    
    # Example operations
    r.set('tunnel_test', 'Hello via Serveo tunnel!')
    value = r.get('tunnel_test')
    print(f"Retrieved from Redis: {value.decode('utf-8')}")
    
    # Keep tunnel open for 60 seconds
    print("Keeping tunnel open for 60 seconds...")
    time.sleep(60)
```

## Error Handling Examples

### SSH Client Check
```python
from flaredantic import ServeoTunnel, ServeoConfig, SSHError, ServeoError
from flaredantic.utils.ssh import is_ssh_installed

def create_serveo_tunnel(port: int, tcp: bool = False):
    # Check SSH installation first
    if not is_ssh_installed():
        print("SSH client is not installed. Please install OpenSSH and try again.")
        return None
    
    config = ServeoConfig(port=port, tcp=tcp, verbose=True)
    
    try:
        tunnel = ServeoTunnel(config)
        tunnel.start()
        return tunnel
    except SSHError as e:
        print(f"SSH Error: {str(e)}")
        return None
    except ServeoError as e:
        print(f"Serveo Error: {str(e)}")
        return None

# Usage
tunnel = create_serveo_tunnel(8080)
if tunnel:
    print(f"Tunnel URL: {tunnel.tunnel_url}")
    input("Press Enter to stop the tunnel...")
    tunnel.stop()
```

### Serveo Availability Check
```python
from flaredantic import ServeoTunnel, ServeoConfig, ServeoError
from flaredantic.utils.serveo import is_serveo_up

def create_tunnel_if_serveo_available(port: int):
    if not is_serveo_up():
        print("Serveo is currently unavailable. Please try again later.")
        return None
    
    config = ServeoConfig(port=port, verbose=True)
    
    try:
        tunnel = ServeoTunnel(config)
        tunnel.start()
        return tunnel
    except ServeoError as e:
        print(f"Serveo Error: {str(e)}")
        return None

# Usage
tunnel = create_tunnel_if_serveo_available(8080)
if tunnel:
    print(f"Tunnel URL: {tunnel.tunnel_url}")
    input("Press Enter to stop the tunnel...")
    tunnel.stop()
```

## Common Issues and Solutions

### SSH Key Issues
If you encounter SSH key issues with Serveo:
```bash
# Remove known hosts file
rm ~/.flaredantic/ssh/known_hosts

# Or use a custom location
config = ServeoConfig(
    port=8080,
    ssh_dir=Path.home() / ".custom-ssh-dir"
)
```

### SSH Not Installed
If SSH is not installed on your system:

```bash
# On Debian/Ubuntu
sudo apt-get install openssh-client

# On RedHat/CentOS/Fedora
sudo dnf install openssh-clients

# On macOS
brew install openssh

# On Windows
# Install Git for Windows which includes SSH or use Windows OpenSSH client
``` 