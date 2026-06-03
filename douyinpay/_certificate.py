import base64
import threading
import time
from typing import Callable

from douyinpay._cipher import aes_decrypt


class CertificateManager:
    """Manages platform certificates with automatic periodic updates.

    Holds a mapping of certificate serial numbers to PEM-encoded public keys.
    Thread-safe. Default update interval is 6 hours.
    """

    def __init__(self, encrypt_key_bytes: bytes, sign_type: str = "RSA") -> None:
        self._certs: dict[str, str] = {}
        self._lock = threading.Lock()
        self._last_update: float = 0
        self._update_interval: float = 6 * 3600
        self._encrypt_key = encrypt_key_bytes
        self._sign_type = sign_type
        self._fetcher: Callable[[], dict] | None = None

    def set_fetcher(self, fetcher: Callable[[], dict]) -> None:
        """Set the callback that downloads raw platform certificate JSON.

        The callback should make an unsigned request to
        GET /v1/merchant/certificates/getPlatformCertificates
        and return the parsed JSON dict.
        """
        self._fetcher = fetcher

    def get_certificate(self, serial_no: str) -> str | None:
        """Return the PEM certificate for the given serial number, or None."""
        with self._lock:
            return self._certs.get(serial_no)

    def ensure_certificates(self) -> None:
        """Refresh certificates if the update interval has elapsed."""
        if self._fetcher is None:
            return
        if time.time() - self._last_update < self._update_interval:
            return
        self._update()

    def _update(self) -> None:
        raw = self._fetcher()
        new_certs = self._parse(raw)
        with self._lock:
            self._certs.update(new_certs)
        self._last_update = time.time()

    def _parse(self, raw: dict) -> dict[str, str]:
        """Parse the certificate API response, decrypting each cert PEM.

        Only processes certificates matching the configured sign_type
        (e.g. RSA users only get RSA platform certs), matching Go SDK.
        """
        result: dict[str, str] = {}
        for item in raw.get("certificates", []):
            # Skip certs that don't match our sign type
            if item.get("cert_type") != self._sign_type:
                continue
            serial_no = item["cert_no"]
            enc = item["encrypt_certificate"]
            # ciphertext is base64-encoded
            ciphertext = base64.b64decode(enc["cipher_text"])
            # nonce is a raw string, used directly as bytes (like Go SDK)
            nonce = enc["nonce"].encode("ascii")
            aad = enc.get("associated_data", "").encode("ascii")
            cert_pem = aes_decrypt(
                self._encrypt_key, ciphertext, nonce, aad
            ).decode("utf-8")
            result[serial_no] = cert_pem
        return result
