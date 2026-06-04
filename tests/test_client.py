import json
import base64
from unittest.mock import patch, MagicMock

import pytest
import httpx

from douyinpay._client import DouyinPayClient
from douyinpay._config import Config
from douyinpay._errors import NetworkError, ServiceError, SignatureError


@pytest.fixture
def config(rsa_private_key_pem):
    return Config(
        mchid="123",
        serial_no="ABC",
        private_key=rsa_private_key_pem,
        encrypt_key="0123456789abcdef0123456789abcdef",
        sign_type="RSA",
    )


@pytest.fixture
def client(config):
    return DouyinPayClient(config)


class TestClientRequest:
    def test_get_request(self, client, rsa_public_key_pem):
        mock_resp = httpx.Response(
            200,
            json={"key": "value"},
            headers={
                "Douyinpay-Timestamp": "1722072480",
                "Douyinpay-Nonce": "testnonce",
                "Douyinpay-Serial": "TESTSERIAL",
            },
        )
        client._cert_mgr._certs["TESTSERIAL"] = rsa_public_key_pem
        with patch.object(client._http, "request", return_value=mock_resp) as mock_req:
            resp = client.request("GET", "/v1/test")
            assert resp == {"key": "value"}
            mock_req.assert_called_once()

    def test_post_request(self, client, rsa_public_key_pem):
        mock_resp = httpx.Response(
            200,
            json={"prepay_id": "dyxxx"},
            headers={
                "Douyinpay-Timestamp": "1722072480",
                "Douyinpay-Nonce": "testnonce",
                "Douyinpay-Serial": "TESTSERIAL",
            },
        )
        client._cert_mgr._certs["TESTSERIAL"] = rsa_public_key_pem
        with patch.object(client._http, "request", return_value=mock_resp):
            resp = client.request("POST", "/v1/trade/transactions/app", body={"amount": {"total": 100}})
            assert resp == {"prepay_id": "dyxxx"}

    def test_service_error(self, client):
        mock_resp = httpx.Response(
            400,
            json={"code": "PARAM_ERROR", "message": "参数错误", "detail": {"field": "x"}},
        )
        with patch.object(client._http, "request", return_value=mock_resp):
            with pytest.raises(ServiceError) as exc:
                client.request("POST", "/v1/test", body={})
            assert exc.value.code == "PARAM_ERROR"
            assert exc.value.message == "参数错误"
            assert exc.value.detail == {"field": "x"}

    def test_network_error(self, client):
        import httpx
        with patch.object(client._http, "request", side_effect=httpx.ConnectError("connection refused")):
            with pytest.raises(NetworkError):
                client.request("GET", "/v1/test")

    def test_signature_verification_fails_unknown_serial(self, client):
        mock_resp = httpx.Response(
            200,
            json={},
            headers={
                "Douyinpay-Timestamp": "1",
                "Douyinpay-Nonce": "x",
                "Douyinpay-Serial": "UNKNOWN",
                "Douyinpay-Signature": "bad",
            },
        )
        with patch.object(client._http, "request", return_value=mock_resp):
            with pytest.raises(SignatureError):
                client.request("GET", "/v1/test")


class TestClientCertDownload:
    def test_cert_fetcher_is_set(self, client):
        assert client._cert_mgr._fetcher is not None

    def test_raw_request_used_for_cert_download(self, client, rsa_public_key_pem):
        import base64
        from douyinpay._cipher import aes_encrypt
        # Build a realistic encrypted cert response
        cert_pem = "-----BEGIN CERTIFICATE-----\nCERT\n-----END CERTIFICATE-----"
        nonce, ct = aes_encrypt(client.config.encrypt_key_bytes, cert_pem.encode(), b"")
        mock_data = {
            "certificates": [{
                "cert_no": "S1",
                "cert_type": "RSA",
                "effective_time": "20300101000000",
                "expire_time": "20350101000000",
                "encrypt_certificate": {
                    "cipher_text": base64.b64encode(ct).decode(),
                    "algorithm": "AEAD-AES-256-GCM",
                    "nonce": nonce.decode(),
                },
            }]
        }
        mock_resp = httpx.Response(200, json=mock_data)
        client._cert_mgr._certs["TESTSERIAL"] = rsa_public_key_pem
        with patch.object(client._http, "request", return_value=mock_resp) as mock_req:
            client._cert_mgr.ensure_certificates()
            assert mock_req.called
            assert client._cert_mgr.get_certificate("S1") == cert_pem


class TestClientContextManager:
    def test_context_manager(self, config):
        with DouyinPayClient(config) as c:
            assert c._http is not None
        # After exit, http client should be closed
        assert c._http.is_closed
