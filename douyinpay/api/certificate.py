"""Certificate management API service."""

from douyinpay.api._base import BaseService


class CertificateService(BaseService):
    """Service for downloading Douyin Pay platform certificates.

    The platform certificates response is AES-GCM encrypted and must be
    decrypted with the merchant's encrypt_key. This service triggers
    certificate download through the certificate manager, which handles
    decryption transparently.
    """

    def get_platform_certificates(self) -> list[dict]:
        """Download and return the latest platform certificates.

        Returns a list of dicts, each containing:
        - cert_no: certificate serial number
        - cert_type: "RSA"
        - effective_time, expire_time: validity period
        - cert_pem: decrypted PEM content
        """
        cert_mgr = self._client.cert_manager
        # Force refresh
        cert_mgr._update()
        certs = []
        with cert_mgr._lock:
            for serial_no, cert_pem in sorted(cert_mgr._certs.items()):
                certs.append({"cert_no": serial_no, "cert_pem": cert_pem})
        return certs
