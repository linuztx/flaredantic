import os

def is_ssh_installed() -> bool:
    """Check if SSH client is installed"""
    return os.system('ssh -V > /dev/null 2>&1') == 0 