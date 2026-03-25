"""
DNS-over-HTTPS support.

Patches socket.getaddrinfo so that all DNS lookups made by `requests`
go through a DoH resolver instead of the OS/ISP resolver.
Useful when an ISP blocks domains at the DNS level.
"""

import socket
import sys
from typing import Any

# Public DoH servers
SERVERS = {
    'cloudflare': 'https://cloudflare-dns.com/dns-query',
    'google':     'https://dns.google/dns-query',
    'quad9':      'https://dns.quad9.net/dns-query',
}

_original_getaddrinfo = socket.getaddrinfo
_active = False


def enable(server: str = 'cloudflare') -> None:
    """Patch socket.getaddrinfo to resolve via DoH.

    Args:
        server: one of 'cloudflare', 'google', 'quad9', or a full DoH URL.
    """
    global _active
    if _active:
        return

    try:
        import dns.resolver
    except ImportError:
        print(
            '[ERROR] dnspython is required for --doh. '
            'Install with: pip install "colusa-cli[doh]"',
            file=sys.stderr,
        )
        raise SystemExit(1)

    doh_url = SERVERS.get(server, server)

    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = [doh_url]

    def _doh_getaddrinfo(
        host: Any,
        port: Any,
        family: int = 0,
        type: int = 0,
        proto: int = 0,
        flags: int = 0,
    ) -> list:
        # Only intercept hostname lookups (not IP literals)
        if isinstance(host, str):
            try:
                answers = resolver.resolve(host, 'A')
                ip = str(answers[0])
                return _original_getaddrinfo(ip, port, family, type, proto, flags)
            except Exception:
                pass  # fall through to OS resolver on any DoH failure
        return _original_getaddrinfo(host, port, family, type, proto, flags)

    socket.getaddrinfo = _doh_getaddrinfo
    _active = True
    print(f'[DoH] Using {doh_url}', file=sys.stderr)
