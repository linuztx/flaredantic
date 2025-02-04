import argparse
import signal
import sys
from . import FlareTunnel, FlareConfig

def signal_handler(sig, frame):
    sys.exit(0)

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Flaredantic - Create Cloudflare tunnels with ease",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "-p", "--port",
        type=int,
        required=True,
        help="Local port to expose"
    )
    
    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=30,
        help="Tunnel start timeout in seconds"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed progress output"
    )
    
    args = parser.parse_args()
    
    # Handle Ctrl+C gracefully
    signal.signal(signal.SIGINT, signal_handler)
    
    # Create and start tunnel
    config = FlareConfig(
        port=args.port,
        timeout=args.timeout,
        verbose=args.verbose
    )
    
    try:
        with FlareTunnel(config):
            print(f"\nTunnel is running! Press Ctrl+C to stop.")
            signal.pause()  # Wait for Ctrl+C
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 