import io
import socket
import qrcode

def get_local_ip() -> str:
    """Detects the computer's local Wi-Fi / LAN IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8"), 80)
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close() 
    return ip

def gen_qr_bytes(target_url: str) -> bytes:
    """Generates a PNG QR code in memory for a given URL."""
    img = qrcode.make(target_url)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()