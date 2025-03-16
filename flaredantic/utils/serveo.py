import requests

def is_serveo_up() -> bool:
    """Check if serveo is up"""
    try:
        response = requests.get("https://serveo.net", timeout=3)
        return response.status_code == 200
    except:
        return False