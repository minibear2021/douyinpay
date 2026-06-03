"""Payment API service — App/H5/JSAPI/Native/MiniProgram payments.

Covers: prepay, query, close, and client-side signing helpers.
"""

import base64
import secrets
import time

from douyinpay.api._base import BaseService
from douyinpay._auth import sign_request


class PaymentsService(BaseService):
    """Service for all payment methods."""

    # ---- App 支付 ----

    def app_prepay(
        self,
        *,
        appid: str,
        description: str,
        out_trade_no: str,
        notify_url: str,
        amount: dict,
        mchid: str | None = None,
        time_expire: str | None = None,
        attach: str | None = None,
        goods_tag: str | None = None,
        scene_info: dict | None = None,
        settle_info: dict | None = None,
    ) -> dict:
        """Create an App payment order. Returns {prepay_id: ...}."""
        body = _remove_none({
            "appid": appid,
            "mchid": mchid or self._client.config.mchid,
            "description": description,
            "out_trade_no": out_trade_no,
            "notify_url": notify_url,
            "amount": amount,
            "time_expire": time_expire,
            "attach": attach,
            "goods_tag": goods_tag,
            "scene_info": scene_info,
            "settle_info": settle_info,
        })
        return self._request("POST", "/v1/trade/transactions/app", body)

    def app_sign_for_client(
        self,
        *,
        appid: str,
        prepay_id: str,
        timestamp: int | None = None,
        nonce_str: str | None = None,
    ) -> dict:
        """Generate client-side signing parameters for App payment.

        The sign uses a 4-line message: appid + timestamp + noncestr + prepayid.
        Returns {appid, partnerid, prepayid, package, noncestr, timestamp, sign}.
        """
        return _build_client_sign_params(
            appid=appid,
            mchid=self._client.config.mchid,
            prepay_id=prepay_id,
            private_key_pem=self._client.config.private_key,
            sign_type=self._client.config.sign_type,
            timestamp=timestamp,
            nonce_str=nonce_str,
        )

    # ---- H5 支付 ----

    def h5_prepay(
        self,
        *,
        appid: str,
        description: str,
        out_trade_no: str,
        notify_url: str,
        amount: dict,
        mchid: str | None = None,
        time_expire: str | None = None,
        attach: str | None = None,
        goods_tag: str | None = None,
        scene_info: dict | None = None,
        settle_info: dict | None = None,
    ) -> dict:
        """Create an H5 payment order. Returns {prepay_id: ..., h5_url: ...}."""
        body = _remove_none({
            "appid": appid,
            "mchid": mchid or self._client.config.mchid,
            "description": description,
            "out_trade_no": out_trade_no,
            "notify_url": notify_url,
            "amount": amount,
            "time_expire": time_expire,
            "attach": attach,
            "goods_tag": goods_tag,
            "scene_info": scene_info,
            "settle_info": settle_info,
        })
        return self._request("POST", "/v1/trade/transactions/h5", body)

    # ---- JSAPI 支付 ----

    def jsapi_prepay(
        self,
        *,
        appid: str,
        description: str,
        out_trade_no: str,
        notify_url: str,
        amount: dict,
        mchid: str | None = None,
        time_expire: str | None = None,
        attach: str | None = None,
        goods_tag: str | None = None,
        scene_info: dict | None = None,
        settle_info: dict | None = None,
    ) -> dict:
        """Create a JSAPI payment order. Returns {prepay_id: ...}."""
        body = _remove_none({
            "appid": appid,
            "mchid": mchid or self._client.config.mchid,
            "description": description,
            "out_trade_no": out_trade_no,
            "notify_url": notify_url,
            "amount": amount,
            "time_expire": time_expire,
            "attach": attach,
            "goods_tag": goods_tag,
            "scene_info": scene_info,
            "settle_info": settle_info,
        })
        return self._request("POST", "/v1/trade/transactions/jsapi", body)

    def jsapi_sign_for_client(
        self,
        *,
        appid: str,
        prepay_id: str,
        timestamp: int | None = None,
        nonce_str: str | None = None,
    ) -> dict:
        """Generate client-side signing parameters for JSAPI payment."""
        return _build_client_sign_params(
            appid=appid,
            mchid=self._client.config.mchid,
            prepay_id=prepay_id,
            private_key_pem=self._client.config.private_key,
            sign_type=self._client.config.sign_type,
            timestamp=timestamp,
            nonce_str=nonce_str,
        )

    # ---- Native 支付 ----

    def native_prepay(
        self,
        *,
        appid: str,
        description: str,
        out_trade_no: str,
        notify_url: str,
        amount: dict,
        mchid: str | None = None,
        time_expire: str | None = None,
        attach: str | None = None,
        goods_tag: str | None = None,
        scene_info: dict | None = None,
        settle_info: dict | None = None,
    ) -> dict:
        """Create a Native payment order. Returns {prepay_id: ..., qr_code: ...}."""
        body = _remove_none({
            "appid": appid,
            "mchid": mchid or self._client.config.mchid,
            "description": description,
            "out_trade_no": out_trade_no,
            "notify_url": notify_url,
            "amount": amount,
            "time_expire": time_expire,
            "attach": attach,
            "goods_tag": goods_tag,
            "scene_info": scene_info,
            "settle_info": settle_info,
        })
        return self._request("POST", "/v1/trade/transactions/native", body)

    # ---- 通用查询 / 关闭 ----

    def query(self, transaction_id: str, *, mchid: str | None = None) -> dict:
        """Query an order by Douyin Pay transaction ID."""
        mid = mchid or self._client.config.mchid
        return self._request("GET", f"/v1/trade/transactions/{transaction_id}?mchid={mid}")

    def query_by_out_trade_no(self, out_trade_no: str, *, mchid: str | None = None) -> dict:
        """Query an order by merchant's out_trade_no."""
        mid = mchid or self._client.config.mchid
        return self._request("GET", f"/v1/trade/transactions/out-trade-no/{out_trade_no}?mchid={mid}")

    def close(self, transaction_id: str, *, mchid: str | None = None) -> dict:
        """Close an unpaid order."""
        mid = mchid or self._client.config.mchid
        return self._request("POST", f"/v1/trade/transactions/{transaction_id}/close", {"mchid": mid})


# ---- Helpers ----

def _remove_none(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None}


def _build_client_sign_params(
    *,
    appid: str,
    mchid: str,
    prepay_id: str,
    private_key_pem: str,
    sign_type: str,
    timestamp: int | None = None,
    nonce_str: str | None = None,
) -> dict:
    """Build the 4-line signing message for client-side payment invocation.

    Message format:
        appid\n
        timestamp\n
        noncestr\n
        prepayid\n
    """
    ts = timestamp or int(time.time())
    nonce = nonce_str or secrets.token_urlsafe(24)[:32]

    message = f"{appid}\n{ts}\n{nonce}\n{prepay_id}\n"

    if sign_type == "SM2":
        from gmssl.sm2 import CryptSM2
        k_hex = secrets.token_hex(32)
        sm2 = CryptSM2(private_key=private_key_pem, public_key="")
        sign = base64.b64encode(sm2.sign(message.encode(), k_hex).encode()).decode()
    else:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.backends import default_backend
        pk = serialization.load_pem_private_key(
            private_key_pem.encode(), password=None, backend=default_backend()
        )
        raw = pk.sign(message.encode(), padding.PKCS1v15(), hashes.SHA256())
        sign = base64.b64encode(raw).decode()

    return {
        "appid": appid,
        "partnerid": mchid,
        "prepayid": prepay_id,
        "package": "Sign=DYPay",
        "noncestr": nonce,
        "timestamp": str(ts),
        "sign": sign,
    }
