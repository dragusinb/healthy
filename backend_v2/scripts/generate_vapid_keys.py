#!/usr/bin/env python3
"""
Generate VAPID keys for Web Push notifications.

VAPID (Voluntary Application Server Identification) keys are used to
identify your server to push services.

Usage:
    python generate_vapid_keys.py

Output:
    Prints VAPID_PRIVATE_KEY and VAPID_PUBLIC_KEY in base64 format.
    Add these to your .env file.

Requirements:
    pip install py-vapid
"""

try:
    from py_vapid import Vapid
except ImportError:
    print("Error: py-vapid not installed.")
    print("Install with: pip install py-vapid")
    exit(1)


def generate_vapid_keys():
    """Generate a new VAPID key pair."""
    print("Generating VAPID keys for Web Push notifications...")
    print("-" * 60)

    vapid = Vapid()
    vapid.generate_keys()

    # Get keys in the format needed for Web Push
    private_key = vapid.private_key_pem
    public_key = vapid.public_key

    print("\nAdd these to your .env file:\n")
    print(f"VAPID_PRIVATE_KEY={vapid.private_key}")
    print(f"VAPID_PUBLIC_KEY={vapid.public_key}")
    print(f"VAPID_SUBJECT=mailto:contact@analize.online")
    print("\n" + "-" * 60)
    print("\nNOTE: Keep VAPID_PRIVATE_KEY secret! Never commit it to git.")
    print("The VAPID_PUBLIC_KEY is safe to expose to clients.")


if __name__ == "__main__":
    generate_vapid_keys()
