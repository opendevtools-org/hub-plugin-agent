"""WireGuard configs for one custom plugin.

The Hub Pi dials the plugin machine. AllowedIPs is only that peer, so the
Pi keeps its normal default route. Frontend and backend REST both use the
tunnel address.
"""

from __future__ import annotations

import base64
import hashlib
import os
from urllib.parse import urlparse

_P = 2**255 - 19
_A24 = 121665


def _x25519(scalar: bytes, point: bytes) -> bytes:
    key = bytearray(scalar)
    key[0] &= 248
    key[31] &= 127
    key[31] |= 64
    clamped = int.from_bytes(key, "little")
    u = bytearray(point)
    u[31] &= 127
    x1 = int.from_bytes(u, "little")
    x2, z2, x3, z3 = 1, 0, x1, 1
    swap = 0
    for bit in range(254, -1, -1):
        kt = (clamped >> bit) & 1
        swap ^= kt
        if swap:
            x2, x3 = x3, x2
            z2, z3 = z3, z2
        swap = kt
        a = (x2 + z2) % _P
        aa = (a * a) % _P
        b = (x2 - z2) % _P
        bb = (b * b) % _P
        e = (aa - bb) % _P
        c = (x3 + z3) % _P
        d = (x3 - z3) % _P
        da = (d * a) % _P
        cb = (c * b) % _P
        x3 = pow(da + cb, 2, _P)
        z3 = (x1 * pow(da - cb, 2, _P)) % _P
        x2 = (aa * bb) % _P
        z2 = (e * (aa + _A24 * e)) % _P
    if swap:
        x2, z2 = x3, z3
    return ((x2 * pow(z2, _P - 2, _P)) % _P).to_bytes(32, "little")


def keypair() -> tuple[str, str]:
    private = os.urandom(32)
    public = _x25519(private, (9).to_bytes(32, "little"))
    return base64.b64encode(private).decode(), base64.b64encode(public).decode()


def tunnel_hosts(plugin_id: str) -> tuple[str, str]:
    digest = hashlib.sha256(plugin_id.encode()).digest()
    second = 64 + (digest[0] % 64)
    third = digest[1]
    return f"10.{second}.{third}.1", f"10.{second}.{third}.2"


def parse_endpoint(value: str) -> str:
    text = value.strip()
    host, sep, port = text.rpartition(":")
    if not sep or not host or not port.isdigit() or not (0 < int(port) < 65536):
        raise SystemExit("VPN endpoint must look like host:51820.")
    return f"{host}:{int(port)}"


def tunnel_http_url(server: str, tunnel_ip: str) -> str:
    parsed = urlparse(server)
    port = parsed.port
    if port is None:
        port = 443 if parsed.scheme == "https" else 80
    return f"{parsed.scheme}://{tunnel_ip}:{port}"


def pi_config(
    *,
    private_key: str,
    address: str,
    peer_public: str,
    peer_ip: str,
    endpoint: str,
) -> str:
    return (
        "[Interface]\n"
        f"PrivateKey = {private_key}\n"
        f"Address = {address}/32\n\n"
        "[Peer]\n"
        f"PublicKey = {peer_public}\n"
        f"AllowedIPs = {peer_ip}/32\n"
        f"Endpoint = {endpoint}\n"
        "PersistentKeepalive = 25\n"
    )


def server_config(*, private_key: str, address: str, peer_public: str, peer_ip: str, port: int) -> str:
    return (
        "[Interface]\n"
        f"PrivateKey = {private_key}\n"
        f"Address = {address}/32\n"
        f"ListenPort = {port}\n\n"
        "[Peer]\n"
        f"PublicKey = {peer_public}\n"
        f"AllowedIPs = {peer_ip}/32\n"
    )
