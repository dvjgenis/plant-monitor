#!/usr/bin/env python3
"""Generate VAPID keys for Web Push. Run once, then put the values in systemd env."""

from __future__ import annotations

import base64
import sys

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def main() -> int:
    private_key = ec.generate_private_key(ec.SECP256R1())
    priv_raw = private_key.private_numbers().private_value.to_bytes(32, "big")
    pub_raw = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )

    print("# Add these to /etc/systemd/system/plant-server.service under [Service]:")
    print(f"Environment=VAPID_PRIVATE_KEY={b64url(priv_raw)}")
    print(f"Environment=VAPID_PUBLIC_KEY={b64url(pub_raw)}")
    print("Environment=VAPID_CONTACT=mailto:you@example.com")
    print()
    print("# Then: sudo systemctl daemon-reload && sudo systemctl restart plant-server.service")
    return 0


if __name__ == "__main__":
    sys.exit(main())
