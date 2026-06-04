from unittest.mock import patch

import pytest

from douyinpay._client import DouyinPayClient
from douyinpay._config import Config
from douyinpay.api.payments import PaymentsService


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


class TestPaymentsService:
    def test_app_prepay(self, client):
        svc = PaymentsService(client)
        with patch.object(client, "request", return_value={"prepay_id": "dyxxx"}) as mock_req:
            result = svc.app_prepay(
                appid="test_app",
                description="商品",
                out_trade_no="ORD001",
                notify_url="https://example.com/notify",
                amount={"total": 100, "currency": "CNY"},
            )
            assert result == {"prepay_id": "dyxxx"}
            mock_req.assert_called_once()
            args = mock_req.call_args
            assert args[0][0] == "POST"
            assert args[0][1] == "/v1/trade/transactions/app"

    def test_h5_prepay(self, client):
        svc = PaymentsService(client)
        with patch.object(client, "request", return_value={"prepay_id": "dyxxx", "h5_url": "https://..."}):
            result = svc.h5_prepay(
                appid="test_app",
                description="商品",
                out_trade_no="ORD001",
                notify_url="https://example.com/notify",
                amount={"total": 100, "currency": "CNY"},
            )
            assert result["prepay_id"] == "dyxxx"

    def test_query(self, client):
        svc = PaymentsService(client)
        with patch.object(client, "request", return_value={"trade_state": "SUCCESS"}):
            result = svc.query("TXN001")
            assert result["trade_state"] == "SUCCESS"

    def test_query_by_out_trade_no(self, client):
        svc = PaymentsService(client)
        with patch.object(client, "request", return_value={"trade_state": "SUCCESS"}):
            result = svc.query_by_out_trade_no("ORD001")
            assert result["trade_state"] == "SUCCESS"

    def test_close(self, client):
        svc = PaymentsService(client)
        with patch.object(client, "request", return_value={}):
            result = svc.close("TXN001")
            assert result == {}

    def test_app_sign_for_client(self, client):
        svc = PaymentsService(client)
        result = svc.app_sign_for_client(appid="test", prepay_id="dyxxx", timestamp=123, nonce_str="abc")
        assert result["appid"] == "test"
        assert result["partnerid"] == "123"
        assert result["prepayid"] == "dyxxx"
        assert result["package"] == "Sign=DYPay"
        assert result["timestamp"] == "123"
        assert result["noncestr"] == "abc"
        assert "sign" in result

    def test_jsapi_sign_for_client(self, client):
        svc = PaymentsService(client)
        result = svc.jsapi_sign_for_client(appid="test", prepay_id="dyxxx")
        assert result["prepayid"] == "dyxxx"
        assert "sign" in result
