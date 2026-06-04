import pytest
import httpx
from douyinpay._errors import (
    DouyinPayError,
    ServiceError,
    SignatureError,
    DecryptionError,
    NetworkError,
)


class TestErrorHierarchy:
    """All custom errors must subclass DouyinPayError."""

    def test_service_error_is_douyinpay_error(self):
        assert issubclass(ServiceError, DouyinPayError)

    def test_signature_error_is_douyinpay_error(self):
        assert issubclass(SignatureError, DouyinPayError)

    def test_decryption_error_is_douyinpay_error(self):
        assert issubclass(DecryptionError, DouyinPayError)

    def test_network_error_is_douyinpay_error(self):
        assert issubclass(NetworkError, DouyinPayError)

    def test_errors_are_exceptions(self):
        assert issubclass(DouyinPayError, Exception)


class TestServiceError:
    def test_str_representation(self):
        err = ServiceError("ORDER_NOT_FOUND", "The order was not found")
        assert str(err) == "[ORDER_NOT_FOUND] The order was not found"

    def test_with_detail_dict(self):
        detail = {"order_id": "123", "reason": "expired"}
        err = ServiceError("ORDER_NOT_FOUND", "The order was not found", detail=detail)
        assert err.detail == detail
        assert err.code == "ORDER_NOT_FOUND"
        assert err.message == "The order was not found"


class TestNetworkError:
    def test_wraps_original_exception(self):
        request = httpx.Request("GET", "https://api.douyinpay.com/test")
        response = httpx.Response(500, request=request)
        original = httpx.HTTPStatusError(
            "Server error", request=request, response=response
        )
        err = NetworkError("Request failed", original=original)
        assert err.__cause__ is original
        assert str(err) == "Request failed"
