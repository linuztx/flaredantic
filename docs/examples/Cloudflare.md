# Flaredantic Cloudflare Examples 📚

This document provides various examples of how to use Flaredantic with Cloudflare tunnels in different scenarios.

## Basic Examples

### Simple HTTP Server
```python
from http.server import HTTPServer, SimpleHTTPRequestHandler
from flaredantic import FlareTunnel, FlareConfig

# Create a basic HTTP server
server = HTTPServer(('localhost', 8000), SimpleHTTPRequestHandler)

# Create and start tunnel
config = FlareConfig(port=8000)
with FlareTunnel(config) as tunnel:
    print(f"Server accessible at: {tunnel.tunnel_url}")
    server.serve_forever()
```

### Django Development Server
```python
from flaredantic import FlareTunnel, FlareConfig
import subprocess

# Start Django development server
django_process = subprocess.Popen(['python', 'manage.py', 'runserver', '8000'])

# Create tunnel to Django server
config = FlareConfig(
    port=8000,
    verbose=True  # Enable logging for debugging
)
with FlareTunnel(config) as tunnel:
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
from flaredantic import FlareTunnel, FlareConfig
import uvicorn

app = FastAPI()
tunnel = None

@app.on_event("startup")
async def startup_event():
    global tunnel
    config = FlareConfig(
        port=8000,
        verbose=True  # Enable logging for debugging
    )
    tunnel = FlareTunnel(config)
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

### Development vs Production Example
```python
from flaredantic import FlareTunnel, FlareConfig
import os

# Configure based on environment
is_dev = os.getenv("ENVIRONMENT") == "development"
config = FlareConfig(
    port=8000,
    verbose=is_dev,     # Show debug output in development
    timeout=30 if is_dev else 60
)

with FlareTunnel(config) as tunnel:
    print(f"Service available at: {tunnel.tunnel_url}")
    input("Press Enter to stop the tunnel...")
```

To run this example:
```bash
# For development environment:
export ENVIRONMENT=development
python your_app.py

# For production environment:
export ENVIRONMENT=production
python your_app.py
```

## Testing Examples

### Basic HTTP Server Test
```python
from flaredantic import FlareTunnel, FlareConfig
import requests
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler

def test_tunnel():
    # Start local server
    server = HTTPServer(('localhost', 8000), SimpleHTTPRequestHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    # Create tunnel
    config = FlareConfig(port=8000, verbose=True)
    with FlareTunnel(config) as tunnel:
        # Test the connection
        response = requests.get(tunnel.tunnel_url)
        print(f"Status Code: {response.status_code}")
        
    server.shutdown()
```

## Error Handling Examples

### Retry Logic
```python
from flaredantic import FlareTunnel, FlareConfig, CloudflaredError
import time

def create_tunnel_with_retry(port: int, max_retries: int = 3):
    config = FlareConfig(port=port, verbose=True)
    
    for attempt in range(max_retries):
        try:
            tunnel = FlareTunnel(config)
            tunnel.start()
            return tunnel
        except CloudflaredError as e:
            if attempt == max_retries - 1:
                raise
            print(f"Attempt {attempt + 1} failed, retrying...")
            time.sleep(2)
```

To run this example:
```bash
# Save as retry_example.py and run:
python retry_example.py

# To test with different ports:
python -c "
from retry_example import create_tunnel_with_retry
tunnel = create_tunnel_with_retry(8000)
print(f'Tunnel URL: {tunnel.tunnel_url}')
"
```

## Common Issues and Solutions

### Port Already in Use
If you get a "Port already in use" error:
```bash
# Find process using the port
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### Permission Issues
If you encounter permission issues with binary installation:
```bash
# Fix permissions for the binary directory
chmod 755 ~/.flaredantic
``` 