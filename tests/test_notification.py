import base64
import json

import pytest

from douyinpay._auth import build_verify_message
from douyinpay._certificate import CertificateManager
from douyinpay._cipher import aes_encrypt
from douyinpay._config import Config
from douyinpay._errors import SignatureError, DecryptionError
from douyinpay._notification import NotificationParser
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


@pytest.fixture
def notif_config():
    return Config(
        mchid="123",
        serial_no="ABC",
        private_key="unused",
        encrypt_key="0123456789abcdef0123456789abcdef",
        sign_type="RSA",
    )


@pytest.fixture
def cert_mgr(rsa_public_key_pem):
    mgr = CertificateManager(bytes(32), "RSA")
    mgr._certs["TESTSERIAL"] = rsa_public_key_pem
    return mgr


class TestNotificationParser:
    def test_parse_success(self, notif_config, cert_mgr, rsa_private_key_pem):
        parser = NotificationParser(notif_config, cert_mgr)

        key = notif_config.encrypt_key_bytes
        plaintext = json.dumps({
            "appid": "test_app",
            "mchid": "123",
            "out_trade_no": "ORD001",
            "transaction_id": "TXN001",
            "trade_state": "SUCCESS",
        }).encode("utf-8")
        nonce, ciphertext = aes_encrypt(key, plaintext, b"")

        body = json.dumps({
            "id": "DY-xxx",
            "create_time": "2022-11-30T21:51:32+08:00",
            "event_type": "TRANSACTION.SUCCESS",
            "resource_type": "encrypt-resource",
            "summary": "支付成功",
            "resource": {
                "original_type": "transaction",
                "algorithm": "AEAD-AES-256-GCM",
                "ciphertext": base64.b64encode(ciphertext).decode(),
                "associated_data": "",
                "nonce": nonce.decode(),
                "mchid": "123",
            },
        })

        ts = 1722072480
        verify_msg = build_verify_message(ts, "noncestr", body)
        private_key = serialization.load_pem_private_key(
            rsa_private_key_pem.encode(), password=None
        )
        sig = base64.b64encode(
            private_key.sign(verify_msg.encode(), padding.PKCS1v15(), hashes.SHA256())
        ).decode()

        result = parser.parse(body, sig, str(ts), "noncestr", "TESTSERIAL")
        assert result["out_trade_no"] == "ORD001"
        assert result["trade_state"] == "SUCCESS"

    def test_parse_unknown_serial(self, notif_config, cert_mgr):
        parser = NotificationParser(notif_config, cert_mgr)
        with pytest.raises(SignatureError, match="Unknown certificate"):
            parser.parse("{}", "sig", "123", "nonce", "UNKNOWN_SERIAL")

    def test_parse_bad_signature(self, notif_config, cert_mgr):
        parser = NotificationParser(notif_config, cert_mgr)
        body = "{}"
        with pytest.raises(SignatureError):
            parser.parse(body, "badsignature==", "123", "nonce", "TESTSERIAL")
