import socket

def is_serveo_up() -> bool:
    """Check if serveo SSH service is up"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex(("serveo.net", 22))
        sock.close()
        return result == 0
    except:
        return False