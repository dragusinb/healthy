"""
Netopia Payments integration service.

Handles payment initiation, IPN webhooks, and subscription management
for the Romanian payment processor.
"""
import os
import base64
import hashlib
import hmac
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, Tuple
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Netopia configuration from environment
NETOPIA_SIGNATURE = os.getenv("NETOPIA_SIGNATURE", "")
NETOPIA_PUBLIC_KEY_PATH = os.getenv("NETOPIA_PUBLIC_KEY_PATH", "keys/netopia_public.cer")
NETOPIA_PRIVATE_KEY_PATH = os.getenv("NETOPIA_PRIVATE_KEY_PATH", "keys/netopia_private.key")
NETOPIA_API_URL = os.getenv("NETOPIA_API_URL", "https://secure.mobilpay.ro")
NETOPIA_SANDBOX = os.getenv("NETOPIA_SANDBOX", "true").lower() == "true"

# Use sandbox URL for testing
if NETOPIA_SANDBOX:
    NETOPIA_API_URL = "https://sandboxsecure.mobilpay.ro"

# Pricing in RON
SUBSCRIPTION_PRICES = {
    "premium_monthly": {
        "amount": 5.00,
        "currency": "RON",
        "description": "Analize.online Premium - Lunar",
        "interval": "monthly",
        "interval_days": 30,
    },
    "premium_yearly": {
        "amount": 40.00,
        "currency": "RON",
        "description": "Analize.online Premium - Anual",
        "interval": "yearly",
        "interval_days": 365,
    },
    "family_monthly": {
        "amount": 10.00,
        "currency": "RON",
        "description": "Analize.online Family - Lunar",
        "interval": "monthly",
        "interval_days": 30,
    },
}


class NetopiaService:
    """Service for handling Netopia payments."""

    def __init__(self):
        self.signature = NETOPIA_SIGNATURE
        self.api_url = NETOPIA_API_URL
        self.public_key = self._load_public_key()
        self.private_key = self._load_private_key()

    def _load_public_key(self):
        """Load Netopia public key for encryption."""
        try:
            if os.path.exists(NETOPIA_PUBLIC_KEY_PATH):
                with open(NETOPIA_PUBLIC_KEY_PATH, "rb") as f:
                    from cryptography import x509
                    cert = x509.load_pem_x509_certificate(f.read(), default_backend())
                    return cert.public_key()
        except Exception as e:
            print(f"Warning: Could not load Netopia public key: {e}")
        return None

    def _load_private_key(self):
        """Load private key for decrypting IPN."""
        try:
            if os.path.exists(NETOPIA_PRIVATE_KEY_PATH):
                with open(NETOPIA_PRIVATE_KEY_PATH, "rb") as f:
                    return serialization.load_pem_private_key(
                        f.read(),
                        password=None,
                        backend=default_backend()
                    )
        except Exception as e:
            print(f"Warning: Could not load Netopia private key: {e}")
        return None

    def create_payment_request(
        self,
        user_id: int,
        user_email: str,
        plan_type: str,
        return_url: str,
        confirm_url: str,
        billing_info: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a Netopia payment request.

        Args:
            user_id: User's ID
            user_email: User's email
            plan_type: One of 'premium_monthly', 'premium_yearly', 'family_monthly'
            return_url: URL to redirect after payment
            confirm_url: IPN callback URL

        Returns:
            Dict with 'env_key', 'data', and 'url' for form submission
        """
        if plan_type not in SUBSCRIPTION_PRICES:
            raise ValueError(f"Invalid plan type: {plan_type}")

        price_info = SUBSCRIPTION_PRICES[plan_type]
        order_id = f"HA-{user_id}-{plan_type}-{uuid.uuid4().hex[:8]}"

        # Build XML payment request
        root = ET.Element("order", {
            "type": "card",
            "id": order_id,
            "timestamp": datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        })

        # Signature (merchant ID)
        ET.SubElement(root, "signature").text = self.signature

        # Invoice details
        invoice = ET.SubElement(root, "invoice", {
            "currency": price_info["currency"],
            "amount": str(price_info["amount"])
        })
        ET.SubElement(invoice, "details").text = price_info["description"]

        # Billing contact info
        contact_info = ET.SubElement(invoice, "contact_info")
        billing = ET.SubElement(contact_info, "billing", {"type": "person"})

        if billing_info:
            ET.SubElement(billing, "first_name").text = billing_info.get("first_name", "")
            ET.SubElement(billing, "last_name").text = billing_info.get("last_name", "")
            ET.SubElement(billing, "email").text = billing_info.get("email", user_email)
            ET.SubElement(billing, "phone").text = billing_info.get("phone", "")

            address = ET.SubElement(billing, "address")
            ET.SubElement(address, "city").text = billing_info.get("city", "")
            ET.SubElement(address, "country").text = billing_info.get("country", "642")  # Romania
        else:
            ET.SubElement(billing, "email").text = user_email

        # URLs
        ET.SubElement(root, "url", {"return": return_url, "confirm": confirm_url})

        # Custom params for our tracking
        params = ET.SubElement(root, "params")
        ET.SubElement(params, "param", {"name": "user_id"}).text = str(user_id)
        ET.SubElement(params, "param", {"name": "plan_type"}).text = plan_type
        ET.SubElement(params, "param", {"name": "interval"}).text = price_info["interval"]

        # Convert to XML string
        xml_string = ET.tostring(root, encoding="unicode")

        # Encrypt the XML with Netopia's public key
        encrypted_data = self._encrypt_request(xml_string)

        return {
            "env_key": encrypted_data["env_key"],
            "data": encrypted_data["data"],
            "url": f"{self.api_url}/card/redirect",
            "order_id": order_id,
            "amount": price_info["amount"],
            "currency": price_info["currency"],
            "description": price_info["description"],
        }

    def _encrypt_request(self, xml_data: str) -> Dict[str, str]:
        """Encrypt payment request using Netopia's public key."""
        if not self.public_key:
            # For development without keys, return base64 encoded data
            return {
                "env_key": base64.b64encode(b"dev_mode_no_key").decode(),
                "data": base64.b64encode(xml_data.encode()).decode()
            }

        # Generate random AES key
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        import secrets

        aes_key = secrets.token_bytes(32)  # 256-bit key
        iv = secrets.token_bytes(16)

        # Encrypt XML with AES
        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        # Pad data to block size
        block_size = 16
        padded_data = xml_data.encode()
        padding_length = block_size - (len(padded_data) % block_size)
        padded_data += bytes([padding_length] * padding_length)

        encrypted_xml = iv + encryptor.update(padded_data) + encryptor.finalize()

        # Encrypt AES key with RSA public key
        encrypted_key = self.public_key.encrypt(
            aes_key,
            padding.PKCS1v15()
        )

        return {
            "env_key": base64.b64encode(encrypted_key).decode(),
            "data": base64.b64encode(encrypted_xml).decode()
        }

    def decrypt_ipn(self, env_key: str, data: str) -> Dict[str, Any]:
        """
        Decrypt IPN notification from Netopia.

        Returns parsed payment data.
        """
        if not self.private_key:
            # Development mode - try to decode as plain base64
            try:
                xml_data = base64.b64decode(data).decode()
                return self._parse_ipn_xml(xml_data)
            except:
                return {"error": "Cannot decrypt - no private key"}

        try:
            # Decrypt AES key with private key
            encrypted_key = base64.b64decode(env_key)
            aes_key = self.private_key.decrypt(
                encrypted_key,
                padding.PKCS1v15()
            )

            # Decrypt data with AES
            encrypted_data = base64.b64decode(data)
            iv = encrypted_data[:16]
            ciphertext = encrypted_data[16:]

            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            padded_data = decryptor.update(ciphertext) + decryptor.finalize()

            # Remove padding
            padding_length = padded_data[-1]
            xml_data = padded_data[:-padding_length].decode()

            return self._parse_ipn_xml(xml_data)

        except Exception as e:
            return {"error": f"Decryption failed: {str(e)}"}

    def _parse_ipn_xml(self, xml_data: str) -> Dict[str, Any]:
        """Parse IPN XML response."""
        try:
            root = ET.fromstring(xml_data)

            # Extract order info
            order_id = root.get("id", "")
            timestamp = root.get("timestamp", "")

            # Extract mobilpay element
            mobilpay = root.find(".//mobilpay")
            action = ""
            error_code = ""
            error_message = ""

            if mobilpay is not None:
                action_elem = mobilpay.find("action")
                if action_elem is not None:
                    action = action_elem.text or ""

                error_elem = mobilpay.find("error")
                if error_elem is not None:
                    error_code = error_elem.get("code", "")
                    error_message = error_elem.text or ""

            # Extract custom params
            params = {}
            for param in root.findall(".//param"):
                name = param.get("name", "")
                value = param.text or ""
                params[name] = value

            # Determine payment status
            status = "unknown"
            if action == "confirmed":
                status = "confirmed"
            elif action == "confirmed_pending":
                status = "pending"
            elif action == "paid_pending":
                status = "pending"
            elif action == "paid":
                status = "paid"
            elif action == "canceled":
                status = "canceled"
            elif action == "credit":
                status = "refunded"

            return {
                "order_id": order_id,
                "timestamp": timestamp,
                "status": status,
                "action": action,
                "error_code": error_code,
                "error_message": error_message,
                "params": params,
                "user_id": params.get("user_id"),
                "plan_type": params.get("plan_type"),
                "interval": params.get("interval"),
            }

        except Exception as e:
            return {"error": f"XML parsing failed: {str(e)}"}

    def create_ipn_response(self, error_code: int = 0, error_type: int = 0, error_message: str = "") -> str:
        """
        Create IPN response XML.

        Args:
            error_code: 0 for success, non-zero for error
            error_type: Error type (1=permanent, 2=temporary)
            error_message: Error description
        """
        root = ET.Element("crc")

        if error_code == 0:
            root.text = "0"
        else:
            root.set("error_type", str(error_type))
            root.set("error_code", str(error_code))
            root.text = error_message

        return '<?xml version="1.0" encoding="utf-8"?>' + ET.tostring(root, encoding="unicode")

    def get_plan_info(self, plan_type: str) -> Optional[Dict[str, Any]]:
        """Get information about a subscription plan."""
        return SUBSCRIPTION_PRICES.get(plan_type)

    def get_all_plans(self) -> Dict[str, Any]:
        """Get all available subscription plans."""
        return SUBSCRIPTION_PRICES.copy()


# Singleton instance
_netopia_service = None


def get_netopia_service() -> NetopiaService:
    """Get the Netopia service singleton."""
    global _netopia_service
    if _netopia_service is None:
        _netopia_service = NetopiaService()
    return _netopia_service
