import os
import socket

_orig_getaddrinfo = socket.getaddrinfo
_applied = False


def _patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    direct_ip = os.getenv("QDRANT_DIRECT_IP")
    qdrant_url = os.getenv("QDRANT_URL", "")
    if direct_ip and qdrant_url and host in qdrant_url:
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (direct_ip, port))]
    results = _orig_getaddrinfo(host, port, family, type, proto, flags)
    ipv4 = [r for r in results if r[0] == socket.AF_INET]
    return ipv4 if ipv4 else results


def apply() -> None:
    global _applied
    if not _applied:
        socket.getaddrinfo = _patched_getaddrinfo
        _applied = True
