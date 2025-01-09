# Flaredantic Examples 📚

This document provides various examples of how to use Flaredantic in different scenarios.

## Basic Examples

### Simple HTTP Server
```python
from http.server import HTTPServer, SimpleHTTPRequestHandler
from flaredantic import FlareTunnel, TunnelConfig

# Create a basic HTTP server
server = HTTPServer(('localhost', 8000), SimpleHTTPRequestHandler)

# Create and start tunnel
with FlareTunnel({"port": 8000}) as tunnel:
    print(f"Server accessible at: {tunnel.tunnel_url}")
    server.serve_forever()
```

To run this example:
```bash
# Save as simple_server.py and run:
python simple_server.py

# Your local files will be served at the tunnel URL
```

### Django Development Server
```python
from flaredantic import FlareTunnel
import subprocess

# Start Django development server
django_process = subprocess.Popen(['python', 'manage.py', 'runserver', '8000'])

# Create tunnel to Django server
with FlareTunnel({"port": 8000}) as tunnel:
    print(f"Django site available at: {tunnel.tunnel_url}")
    try:
        django_process.wait()
    finally:
        django_process.terminate()
```

To run this example:
```bash
# First, ensure you're in your Django project directory
cd your_django_project

# Save as django_tunnel.py and run:
python django_tunnel.py

# Your Django site will be available at the tunnel URL
```

## Advanced Examples

### FastAPI with Background Tasks
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

To run this example:
```bash
# Install required dependencies
pip install fastapi uvicorn

# Save as fastapi_app.py and run:
uvicorn fastapi_app:app --reload

# Your FastAPI application will be available at the tunnel URL
# Test the API:
curl https://your-tunnel-url.trycloudflare.com/
```

### Flask Application
```python
from flask import Flask
from flaredantic import FlareTunnel
import threading

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Bruce Gwapo!'

def run_tunnel():
    with FlareTunnel({"port": 5000}):
        app.run(port=5000)

if __name__ == '__main__':
    threading.Thread(target=run_tunnel).start()
```

To run this example:
```bash
# Install Flask
pip install flask

# Save as flask_app.py and run:
python flask_app.py

# Test the application:
curl https://your-tunnel-url.trycloudflare.com/
```

### Custom Binary Location
```python
from pathlib import Path
from flaredantic import FlareTunnel, TunnelConfig

config = TunnelConfig(
    port=8000,
    bin_dir=Path("/usr/local/bin"),
    timeout=60
)

with FlareTunnel(config) as tunnel:
    print(f"Using custom binary from: {config.bin_dir}")
    print(f"Service available at: {tunnel.tunnel_url}")
```

To run this example:
```bash
# Ensure you have write permissions to /usr/local/bin
sudo mkdir -p /usr/local/bin
sudo chown $USER /usr/local/bin

# Save as custom_binary.py and run:
python custom_binary.py
```

### Development vs Production Example
```python
from flaredantic import FlareTunnel
import os

# Configure based on environment
is_dev = os.getenv("ENVIRONMENT") == "development"
tunnel = FlareTunnel({
    "port": 8000,
    "quiet": not is_dev,  # Show output only in development
    "timeout": 30 if is_dev else 60
})
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
from flaredantic import FlareTunnel
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
    with FlareTunnel({"port": 8000}) as tunnel:
        # Test the connection
        response = requests.get(tunnel.tunnel_url)
        print(f"Status Code: {response.status_code}")
        
    server.shutdown()
```

To run this test:
```bash
# Install requests for testing
pip install requests

# Save as test_tunnel.py and run:
python test_tunnel.py
```

## Error Handling Examples

### Retry Logic
```python
from flaredantic import FlareTunnel, CloudflaredError
import time

def create_tunnel_with_retry(port: int, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            tunnel = FlareTunnel({"port": port})
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
# Save as retry_example.py
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