import base64
import json as _json

from douyinpay._auth import build_verify_message, verify_signature
from douyinpay._certificate import CertificateManager
from douyinpay._cipher import aes_decrypt
from douyinpay._config import Config
from douyinpay._errors import SignatureError


class NotificationParser:
    """Parses and validates Douyin Pay callback notifications.

    Verifies the signature, decrypts the AES-256-GCM encrypted resource,
    and returns the parsed business data.
    """

    def __init__(self, config: Config, cert_manager: CertificateManager) -> None:
        self._config = config
        self._cert_mgr = cert_manager

    def parse(
        self,
        body: str,
        signature: str,
        timestamp: str,
        nonce: str,
        serial: str,
    ) -> dict:
        """Parse and validate a callback notification.

        Args:
            body: Raw HTTP request body (JSON string).
            signature: Value of the Douyinpay-Signature header.
            timestamp: Value of the Douyinpay-Timestamp header.
            nonce: Value of the Douyinpay-Nonce header.
            serial: Value of the Douyinpay-Serial header.

        Returns:
            Decrypted business data as a dict (contains fields like
            appid, mchid, out_trade_no, transaction_id, trade_state, etc.)

        Raises:
            SignatureError: if signature verification fails.
            DecryptionError: if AES decryption fails.
        """
        # 1. Verify signature
        self._cert_mgr.ensure_certificates()
        cert_pem = self._cert_mgr.get_certificate(serial)
        if cert_pem is None:
            raise SignatureError(f"Unknown certificate serial in notification: {serial}")

        verify_msg = build_verify_message(int(timestamp), nonce, body)
        verify_signature(verify_msg, signature, cert_pem)

        # 2. Parse JSON
        data = _json.loads(body)
        resource = data["resource"]

        # 3. Decrypt ciphertext
        # ciphertext is base64-encoded
        ciphertext = base64.b64decode(resource["ciphertext"])
        # nonce is a raw string, used directly as bytes (like Go SDK)
        nonce_bytes = resource["nonce"].encode("ascii")
        aad = resource.get("associated_data", "").encode("ascii")
        key = self._config.encrypt_key_bytes

        plaintext = aes_decrypt(key, ciphertext, nonce_bytes, aad)
        return _json.loads(plaintext)
