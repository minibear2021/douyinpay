import base64
import time

from douyinpay._certificate import CertificateManager
from douyinpay._cipher import aes_encrypt


ENCRYPT_KEY = bytes(32)  # 32 zero bytes
SIGN_TYPE = "RSA"


def _make_cert_response(serial_no: str, cert_pem: str) -> dict:
    """Build a realistic API response with AES-encrypted certificate."""
    nonce, ct = aes_encrypt(ENCRYPT_KEY, cert_pem.encode(), b"")
    return {
        "certificates": [
            {
                "cert_no": serial_no,
                "effective_time": "20230322042245",
                "expire_time": "20280320042245",
                "cert_type": "RSA",
                "encrypt_certificate": {
                    "cipher_text": base64.b64encode(ct).decode(),
                    "algorithm": "AEAD-AES-256-GCM",
                    "nonce": nonce.decode(),
                },
            }
        ]
    }


class TestCertificateManager:
    def test_get_returns_none_for_unknown_serial(self):
        mgr = CertificateManager(ENCRYPT_KEY, SIGN_TYPE)
        assert mgr.get_certificate("UNKNOWN") is None

    def test_get_returns_cached_cert(self):
        mgr = CertificateManager(ENCRYPT_KEY, SIGN_TYPE)
        mgr._certs["SERIAL1"] = "-----BEGIN CERTIFICATE-----\nCERT1\n-----END CERTIFICATE-----"
        assert mgr.get_certificate("SERIAL1") == "-----BEGIN CERTIFICATE-----\nCERT1\n-----END CERTIFICATE-----"

    def test_ensure_certificates_downloads_and_decrypts(self):
        mgr = CertificateManager(ENCRYPT_KEY, SIGN_TYPE)
        cert_pem = "-----BEGIN CERTIFICATE-----\nREAL_CERT\n-----END CERTIFICATE-----"
        mock_data = _make_cert_response("S1", cert_pem)
        mgr.set_fetcher(lambda: mock_data)
        mgr.ensure_certificates()
        assert mgr.get_certificate("S1") == cert_pem

    def test_filters_by_sign_type(self):
        """Certificates with mismatched cert_type should be skipped."""
        mgr = CertificateManager(ENCRYPT_KEY, "RSA")
        nonce, ct = aes_encrypt(ENCRYPT_KEY, b"sm2_cert", b"")
        mock_data = {
            "certificates": [{
                "cert_no": "SM2SERIAL",
                "cert_type": "SM2",
                "effective_time": "2023",
                "expire_time": "2028",
                "encrypt_certificate": {
                    "cipher_text": base64.b64encode(ct).decode(),
                    "algorithm": "AEAD-AES-256-GCM",
                    "nonce": nonce.decode(),
                },
            }]
        }
        mgr.set_fetcher(lambda: mock_data)
        mgr.ensure_certificates()
        assert mgr.get_certificate("SM2SERIAL") is None  # filtered out

    def test_ensure_certificates_skips_when_fresh(self):
        mgr = CertificateManager(ENCRYPT_KEY, SIGN_TYPE)
        mgr._certs = {"OLD": "old_cert"}
        mgr._last_update = time.time()
        mgr.set_fetcher(lambda: {"certificates": []})
        mgr.ensure_certificates()
        assert mgr.get_certificate("OLD") == "old_cert"

    def test_update_does_not_remove_existing_certs(self):
        mgr = CertificateManager(ENCRYPT_KEY, SIGN_TYPE)
        mgr._certs = {"OLD": "old_cert"}
        cert_pem = "-----BEGIN CERTIFICATE-----\nNEW_CERT\n-----END CERTIFICATE-----"
        mock_data = _make_cert_response("NEW", cert_pem)
        mgr.set_fetcher(lambda: mock_data)
        mgr._update()
        assert mgr.get_certificate("OLD") == "old_cert"
        assert mgr.get_certificate("NEW") == cert_pem

    def test_ensure_certificates_does_nothing_without_fetcher(self):
        mgr = CertificateManager(ENCRYPT_KEY, SIGN_TYPE)
        mgr.ensure_certificates()
        assert mgr._last_update == 0
