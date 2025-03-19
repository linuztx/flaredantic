import argparse
import signal
import sys
from . import FlareTunnel, FlareConfig
from . import ServeoTunnel, ServeoConfig

def signal_handler(sig, frame):
    sys.exit(0)

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Flaredantic - Create tunnels with ease",
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

    parser.add_argument(
        "--tunnel",
        choices=["cloudflare", "serveo"],
        default="cloudflare",
        help="Tunnel provider to use"
    )

    # Add TCP argument
    parser.add_argument(
        "--tcp",
        action="store_true",
        help="Enable TCP forwarding (Serveo only)"
    )
    
    args = parser.parse_args()
    
    # Auto-switch to Serveo if TCP flag is set
    if args.tcp:
        args.tunnel = "serveo"
    
    # Handle Ctrl+C gracefully
    signal.signal(signal.SIGINT, signal_handler)
    
    # Create appropriate config and tunnel based on choice
    if args.tunnel == "cloudflare":
        config = FlareConfig(
            port=args.port,
            timeout=args.timeout,
            verbose=args.verbose
        )
        tunnel = FlareTunnel(config)
    else:  # serveo
        config = ServeoConfig(
            port=args.port,
            timeout=args.timeout,
            verbose=args.verbose,
            tcp=args.tcp
        )
        tunnel = ServeoTunnel(config)
    
    try:
        with tunnel:
            print(f"\nTunnel is running! Press Ctrl+C to stop.")
            signal.pause()  # Wait for Ctrl+C
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 