"""
Port Finder and Network Interface Discovery.
Handles binding verification, port fallback (>10000), and LAN IP resolution.
"""

import socket
import logging
from typing import List, Tuple

logger = logging.getLogger("port_finder")

def is_port_available(host: str, port: int) -> bool:
    """Check if a specific host:port can be bound for listening."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind((host, port))
        sock.close()
        return True
    except (socket.error, PermissionError, OSError) as e:
        logger.debug(f"Port {port} cannot be bound on {host}: {e}")
        return False
    finally:
        try:
            sock.close()
        except Exception:
            pass


def find_free_high_port(host: str = "0.0.0.0", start_port: int = 10080, max_port: int = 65535) -> int:
    """Find the next available port strictly higher than 10000."""
    # First try common 10000+ conventions
    preferred_ports = [10080, 18080, 10000, 10800, 10088]
    for port in preferred_ports:
        if port > 10000 and is_port_available(host, port):
            return port

    # Sequential search
    for port in range(max(10001, start_port), max_port):
        if is_port_available(host, port):
            return port

    # System dynamic port allocation fallback (> 10000)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, 0))
        allocated_port = s.getsockname()[1]
        if allocated_port > 10000:
            return allocated_port

    return 10080


def resolve_web_port(preferred_port: int = 80, host: str = "0.0.0.0") -> Tuple[int, bool]:
    """
    Determines the port to use.
    If preferred_port (default 80) is available, returns (preferred_port, False).
    If occupied or lacks permission, selects an available port > 10000 and returns (port, True).
    """
    if is_port_available(host, preferred_port):
        return preferred_port, False
    
    fallback_port = find_free_high_port(host)
    return fallback_port, True


def get_local_ip_addresses() -> List[str]:
    """Discover all non-loopback IPv4 addresses on the host."""
    ips = []
    try:
        # Connect to an external address (does not actually send data) to determine primary routing IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        s.connect(("8.8.8.8", 80))
        primary_ip = s.getsockname()[0]
        s.close()
        if primary_ip and primary_ip not in ips and not primary_ip.startswith("127."):
            ips.append(primary_ip)
    except Exception:
        pass

    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = info[4][0]
            if ip not in ips and not ip.startswith("127."):
                ips.append(ip)
    except Exception:
        pass

    if not ips:
        ips.append("127.0.0.1")

    return ips
