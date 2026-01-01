import subprocess
import shutil


def is_ssh_installed() -> bool:
    """Check if SSH client is installed (cross-platform)"""
    if shutil.which("ssh"):
        return True
    try:
        subprocess.run(
            ["ssh", "-V"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False 
