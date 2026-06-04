import base64
import pytest

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding

from douyinpay._auth import (
    SignResult,
    sign_request,
    build_verify_message,
    verify_signature,
    _build_sign_message,
)
from douyinpay._errors import SignatureError


class TestSignResult:
    def test_fields_populated(self):
        result = SignResult(
            mchid="8020221008775523",
            serial_no="41A48FEF2A9F04C5",
            nonce_str="abc123def456",
            timestamp=1717000000,
            signature="dGVzdA==",
            sign_type="RSA",
        )
        assert result.mchid == "8020221008775523"
        assert result.serial_no == "41A48FEF2A9F04C5"
        assert result.nonce_str == "abc123def456"
        assert result.timestamp == 1717000000
        assert result.signature == "dGVzdA=="
        assert result.sign_type == "RSA"

    def test_sign_type_defaults_to_rsa(self):
        result = SignResult(
            mchid="8020221008775523",
            serial_no="41A48FEF2A9F04C5",
            nonce_str="abc123",
            timestamp=1717000000,
            signature="dGVzdA==",
        )
        assert result.sign_type == "RSA"

    def test_to_header_format(self):
        result = SignResult(
            mchid="8020221008775523",
            serial_no="41A48FEF2A9F04C5",
            nonce_str="abc123def456",
            timestamp=1717000000,
            signature="dGVzdA==",
        )
        header = result.to_header()
        assert header.startswith("DouyinPay-RSA")
        assert 'mchid="8020221008775523"' in header
        assert 'serial_no="41A48FEF2A9F04C5"' in header
        assert 'nonce_str="abc123def456"' in header
        assert 'timestamp="1717000000"' in header
        assert 'signature="dGVzdA=="' in header


class TestSignRequestRSA:
    def test_sign_request_rsa(
        self, rsa_private_key_pem, test_mchid, rsa_cert_serial
    ):
        result = sign_request(
            method="POST",
            path="/v1/orders",
            body='{"amount":100}',
            mchid=test_mchid,
            serial_no=rsa_cert_serial,
            private_key_pem=rsa_private_key_pem,
        )
        assert result.mchid == test_mchid
        assert result.serial_no == rsa_cert_serial
        assert result.sign_type == "RSA"
        assert result.timestamp > 0
        assert len(result.nonce_str) == 32
        assert result.nonce_str.isalnum()
        assert len(result.signature) > 0

        # verify it is valid base64
        decoded = base64.b64decode(result.signature)
        assert len(decoded) == 256  # 2048-bit RSA signature

    def test_sign_request_get_empty_body(
        self, rsa_private_key_pem, test_mchid, rsa_cert_serial
    ):
        result = sign_request(
            method="GET",
            path="/v1/orders/123",
            body="",
            mchid=test_mchid,
            serial_no=rsa_cert_serial,
            private_key_pem=rsa_private_key_pem,
        )
        assert result.sign_type == "RSA"
        assert len(result.signature) > 0

    def test_nonce_is_unique(
        self, rsa_private_key_pem, test_mchid, rsa_cert_serial
    ):
        result1 = sign_request(
            method="POST",
            path="/v1/orders",
            body="{}",
            mchid=test_mchid,
            serial_no=rsa_cert_serial,
            private_key_pem=rsa_private_key_pem,
        )
        result2 = sign_request(
            method="POST",
            path="/v1/orders",
            body="{}",
            mchid=test_mchid,
            serial_no=rsa_cert_serial,
            private_key_pem=rsa_private_key_pem,
        )
        assert result1.nonce_str != result2.nonce_str

    def test_signature_differs_for_different_bodies(
        self, rsa_private_key_pem, test_mchid, rsa_cert_serial
    ):
        result1 = sign_request(
            method="POST",
            path="/v1/orders",
            body='{"amount":100}',
            mchid=test_mchid,
            serial_no=rsa_cert_serial,
            private_key_pem=rsa_private_key_pem,
        )
        result2 = sign_request(
            method="POST",
            path="/v1/orders",
            body='{"amount":200}',
            mchid=test_mchid,
            serial_no=rsa_cert_serial,
            private_key_pem=rsa_private_key_pem,
        )
        assert result1.signature != result2.signature

    def test_to_header_format(
        self, rsa_private_key_pem, test_mchid, rsa_cert_serial
    ):
        result = sign_request(
            method="POST",
            path="/v1/orders",
            body='{"amount":100}',
            mchid=test_mchid,
            serial_no=rsa_cert_serial,
            private_key_pem=rsa_private_key_pem,
        )
        header = result.to_header()
        assert header.startswith("DouyinPay-RSA")
        assert f'mchid="{test_mchid}"' in header
        assert f'serial_no="{rsa_cert_serial}"' in header
        assert f'nonce_str="{result.nonce_str}"' in header
        assert f'timestamp="{result.timestamp}"' in header
        assert f'signature="{result.signature}"' in header


class TestVerifySignature:
    def test_verify_response_signature(
        self, rsa_private_key_pem, rsa_public_key_pem
    ):
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding

        # Sign a simulated response verification message
        timestamp = 1717000000
        nonce = "abc123def456"
        body = '{"code":"SUCCESS"}'

        message = build_verify_message(timestamp, nonce, body)

        private_key = serialization.load_pem_private_key(
            rsa_private_key_pem.encode("utf-8"),
            password=None,
        )
        raw_sig = private_key.sign(
            message.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        signature_b64 = base64.b64encode(raw_sig).decode("utf-8")

        result = verify_signature(
            message=message,
            signature_b64=signature_b64,
            public_key_pem=rsa_public_key_pem,
        )
        assert result is True

    def test_verify_bad_signature_fails(
        self, rsa_public_key_pem
    ):
        message = build_verify_message(
            timestamp=1717000000,
            nonce="abc123",
            body='{}',
        )
        # totally wrong signature
        bad_sig = base64.b64encode(b"\x00" * 256).decode("utf-8")
        with pytest.raises(SignatureError):
            verify_signature(
                message=message,
                signature_b64=bad_sig,
                public_key_pem=rsa_public_key_pem,
            )

    def test_verify_bad_base64_raises(self, rsa_public_key_pem):
        message = build_verify_message(
            timestamp=1717000000,
            nonce="abc123",
            body='{}',
        )
        with pytest.raises(SignatureError, match="base64"):
            verify_signature(
                message=message,
                signature_b64="!!!not-valid-base64!!!",
                public_key_pem=rsa_public_key_pem,
            )

    def test_verify_with_certificate_pem(self, rsa_private_key_pem, rsa_public_key_pem):
        """Verification should work with a cert PEM (not just public key)."""
        # Build a self-signed certificate PEM for testing
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes as _hashes
        from cryptography.hazmat.backends import default_backend
        import datetime

        now = datetime.datetime.now(datetime.UTC)
        private_key = serialization.load_pem_private_key(
            rsa_private_key_pem.encode(), password=None, backend=default_backend()
        )
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
            x509.NameAttribute(NameOID.COMMON_NAME, "Test Cert"),
        ])
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now)
            .not_valid_after(now + datetime.timedelta(days=1))
            .sign(private_key, _hashes.SHA256(), default_backend())
        )
        cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode()

        # Sign with private key, verify using the cert PEM
        message = build_verify_message(1717000000, "abc123", '{}')
        sig_bytes = private_key.sign(message.encode(), padding.PKCS1v15(), _hashes.SHA256())
        sig = base64.b64encode(sig_bytes).decode()

        assert verify_signature(message, sig, cert_pem) is True


class TestBuildVerifyMessage:
    def test_build_verify_message_format(self):
        message = build_verify_message(
            timestamp=1717000000,
            nonce="abc123",
            body='{"code":"SUCCESS"}',
        )
        expected = '1717000000\nabc123\n{"code":"SUCCESS"}\n'
        assert message == expected

    def test_empty_body(self):
        message = build_verify_message(
            timestamp=1717000000,
            nonce="abc123",
            body="",
        )
        assert message == "1717000000\nabc123\n\n"

    def test_numeric_body(self):
        message = build_verify_message(
            timestamp=1717000000,
            nonce="abc123",
            body="12345",
        )
        assert message == "1717000000\nabc123\n12345\n"


class TestBuildSignMessage:
    def test_format(self):
        msg = _build_sign_message(
            method="POST",
            path="/v1/orders",
            timestamp=1717000000,
            nonce_str="abc123",
            body='{"amount":100}',
        )
        expected = 'POST\n/v1/orders\n1717000000\nabc123\n{"amount":100}\n'
        assert msg == expected

    def test_get_empty_body(self):
        msg = _build_sign_message(
            method="GET",
            path="/v1/orders/123",
            timestamp=1717000000,
            nonce_str="abc123",
            body="",
        )
        expected = "GET\n/v1/orders/123\n1717000000\nabc123\n\n"
        assert msg == expected


class TestSM2Signing:
    def test_sign_request_sm2(self, sm2_key_hex, test_mchid, rsa_cert_serial):
        priv, _ = sm2_key_hex
        result = sign_request(
            method="POST",
            path="/v1/test",
            body='{"amount":100}',
            mchid=test_mchid,
            serial_no=rsa_cert_serial,
            private_key_pem=priv,
            sign_type="SM2",
        )
        assert result.sign_type == "SM2"
        assert len(result.nonce_str) == 32
        assert len(result.signature) > 0

    def test_sign_result_to_header_sm2(self, sm2_key_hex, test_mchid, rsa_cert_serial):
        priv, _ = sm2_key_hex
        result = sign_request(
            method="POST",
            path="/v1/test",
            body="{}",
            mchid=test_mchid,
            serial_no=rsa_cert_serial,
            private_key_pem=priv,
            sign_type="SM2",
        )
        header = result.to_header()
        assert header.startswith("DouyinPay-SM2 ")

    def test_sm2_sign_and_verify(self, sm2_key_hex):
        priv, pub = sm2_key_hex
        from gmssl.sm2 import CryptSM2
        import secrets

        message = b"test message for sm2"
        sm2_signer = CryptSM2(private_key=priv, public_key="")
        sig_hex = sm2_signer.sign(message, secrets.token_hex(32))
        sig_b64 = base64.b64encode(sig_hex.encode("utf-8")).decode("utf-8")

        assert verify_signature(
            message=message.decode("utf-8"),
            signature_b64=sig_b64,
            public_key_pem=pub,
            sign_type="SM2",
        ) is True

    def test_sm2_verify_bad_signature_fails(self, sm2_key_hex):
        _, pub = sm2_key_hex
        message = "test message"
        # Create a base64-encoded fake signature of correct length (128 hex chars = 64 bytes)
        bad_sig = base64.b64encode(b"\x00" * 64).decode("utf-8")
        with pytest.raises(SignatureError):
            verify_signature(
                message=message,
                signature_b64=bad_sig,
                public_key_pem=pub,
                sign_type="SM2",
            )
