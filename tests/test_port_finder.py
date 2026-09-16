"""
Unit Tests for Port Finder and Network Discovery.
"""

import socket
import pytest
from backend.port_finder import is_port_available, find_free_high_port, resolve_web_port, get_local_ip_addresses

def test_is_port_available():
    # Bind an ephemeral port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        # While socket is open, is_port_available should return False
        assert is_port_available("127.0.0.1", port) is False

    # Once closed, should return True
    assert is_port_available("127.0.0.1", port) is True


def test_find_free_high_port():
    high_port = find_free_high_port("127.0.0.1")
    assert high_port > 10000, f"Expected port > 10000, got {high_port}"
    assert is_port_available("127.0.0.1", high_port) is True


def test_resolve_web_port_occupied_fallback():
    # Occupy a test port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        occupied_port = s.getsockname()[1]

        # Request this occupied port
        resolved_port, was_fallback = resolve_web_port(preferred_port=occupied_port, host="127.0.0.1")
        assert was_fallback is True
        assert resolved_port > 10000
        assert resolved_port != occupied_port


def test_get_local_ip_addresses():
    ips = get_local_ip_addresses()
    assert len(ips) > 0
    for ip in ips:
        parts = ip.split(".")
        assert len(parts) == 4, f"Invalid IPv4: {ip}"
