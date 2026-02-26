"""HMAC signer for webhook security."""

import hashlib
import hmac
import json
from typing import Any, Dict


class WebhookSigner:
    """
    Signs and verifies webhook payloads using HMAC-SHA256.
    
    Usage:
        signer = WebhookSigner(secret)
        signature = signer.sign(payload)
        is_valid = signer.verify(payload, signature)
    """

    def __init__(self, secret: str):
        self.secret = secret.encode("utf-8")

    def sign(self, payload: Dict[str, Any]) -> str:
        """
        Sign a payload.
        
        Args:
            payload: Payload dictionary
        
        Returns:
            HMAC signature string (hex)
        """
        # Serialize payload consistently
        payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))

        # Create HMAC
        signature = hmac.new(
            self.secret,
            payload_json.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return f"sha256={signature}"

    def verify(self, payload: Dict[str, Any], signature: str) -> bool:
        """
        Verify a payload signature.
        
        Args:
            payload: Payload dictionary
            signature: Signature to verify
        
        Returns:
            True if signature is valid
        """
        expected = self.sign(payload)
        return hmac.compare_digest(expected, signature)

    def extract_signature(self, header_value: str) -> str:
        """
        Extract signature from header value.
        
        Supports formats:
        - "sha256=abc123..."
        - "sha256:abc123..."
        - "abc123..."
        """
        if "=" in header_value:
            return header_value.split("=", 1)[1]
        if ":" in header_value:
            return header_value.split(":", 1)[1]
        return header_value
