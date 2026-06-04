"""支付 API 服务 — App/H5/JSAPI/Native 支付下单、查询、关单及客户端调起签名。"""

import base64
import secrets
import time

from douyinpay.api._base import BaseService
from douyinpay._auth import sign_request


class PaymentsService(BaseService):
    """支付相关接口。"""

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
        """App 支付下单。

        Args:
            appid: 应用ID，商户在抖音开放平台申请的应用ID，全局唯一。
            description: 商品描述，展示在用户抖音钱包账单的"商品说明"内，最长127个字符。
            out_trade_no: 商户订单号，只能是数字、大小写字母_-*且在同一个商户号下唯一，长度6-32。
            notify_url: 通知地址，必须为直接可访问的HTTPS URL，不允许携带查询串。
            amount: 订单金额，格式为 {"total": int(分), "currency": "CNY"}。
            mchid: 直连商户号，由抖音支付生成并下发，默认使用 Config 中配置的值。
            time_expire: 交易结束时间，RFC 3339 格式（yyyy-MM-DDTHH:mm:ss+TIMEZONE），非必填。
            attach: 附加数据，在查询API和支付通知中原样返回，非必填，最长1024。
            goods_tag: 优惠标记，JSON格式，用于业务场景/个性化策略/指定优惠信息区分，非必填。
            scene_info: 场景信息，包含 payer_client_ip（用户终端IP）等，非必填。
            settle_info: 结算信息，包含 profit_sharing（是否分账）等，非必填。

        Returns:
            {"prepay_id": "dy..."}，prepay_id 有效期为2小时。
        """
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

    def sign_for_client(
        self,
        *,
        appid: str,
        prepay_id: str,
        timestamp: int | None = None,
        nonce_str: str | None = None,
    ) -> dict:
        """生成客户端调起支付的签名参数（App / JSAPI 通用）。

        Args:
            appid: 应用ID。
            prepay_id: 预支付交易会话ID，由下单接口返回。
            timestamp: Unix 时间戳（秒），不传则使用当前时间。
            nonce_str: 随机字符串，不长于32位，不传则自动生成。

        Returns:
            {appid, partnerid, prepayid, package, noncestr, timestamp, sign}
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
        """H5 支付下单。

        Args:
            appid: 应用ID，商户在抖音开放平台申请的应用ID，全局唯一。
            description: 商品描述，展示在用户抖音钱包账单的"商品说明"内，最长127个字符。
            out_trade_no: 商户订单号，只能是数字、大小写字母_-*且在同一个商户号下唯一，长度6-32。
            notify_url: 通知地址，必须为直接可访问的HTTPS URL，不允许携带查询串。
            amount: 订单金额，格式为 {"total": int(分), "currency": "CNY"}。
            mchid: 直连商户号，默认使用 Config 中配置的值。
            time_expire: 交易结束时间，RFC 3339 格式，非必填。
            attach: 附加数据，在查询API和支付通知中原样返回，非必填。
            goods_tag: 优惠标记，JSON格式，非必填。
            scene_info: 场景信息，包含 payer_client_ip 等，H5 支付建议传递。
            settle_info: 结算信息，包含 profit_sharing（是否分账）等，非必填。

        Returns:
            {prepay_id: "dy...", h5_url: "..."}
        """
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
        """JSAPI 支付下单（含小程序支付）。

        Args:
            appid: 应用ID，商户在抖音开放平台申请的应用ID，全局唯一。
            description: 商品描述，展示在用户抖音钱包账单的"商品说明"内，最长127个字符。
            out_trade_no: 商户订单号，只能是数字、大小写字母_-*且在同一个商户号下唯一，长度6-32。
            notify_url: 通知地址，必须为直接可访问的HTTPS URL，不允许携带查询串。
            amount: 订单金额，格式为 {"total": int(分), "currency": "CNY"}。
            mchid: 直连商户号，默认使用 Config 中配置的值。
            time_expire: 交易结束时间，RFC 3339 格式，非必填。
            attach: 附加数据，在查询API和支付通知中原样返回，非必填。
            goods_tag: 优惠标记，JSON格式，非必填。
            scene_info: 场景信息，包含 payer_client_ip 等，非必填。
            settle_info: 结算信息，包含 profit_sharing（是否分账）等，非必填。

        Returns:
            {prepay_id: "dy..."}
        """
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
        """Native（扫码）支付下单。

        Args:
            appid: 应用ID，商户在抖音开放平台申请的应用ID，全局唯一。
            description: 商品描述，展示在用户抖音钱包账单的"商品说明"内，最长127个字符。
            out_trade_no: 商户订单号，只能是数字、大小写字母_-*且在同一个商户号下唯一，长度6-32。
            notify_url: 通知地址，必须为直接可访问的HTTPS URL，不允许携带查询串。
            amount: 订单金额，格式为 {"total": int(分), "currency": "CNY"}。
            mchid: 直连商户号，默认使用 Config 中配置的值。
            time_expire: 交易结束时间，RFC 3339 格式，非必填。
            attach: 附加数据，在查询API和支付通知中原样返回，非必填。
            goods_tag: 优惠标记，JSON格式，非必填。
            scene_info: 场景信息，包含 payer_client_ip 等，非必填。
            settle_info: 结算信息，包含 profit_sharing（是否分账）等，非必填。

        Returns:
            {prepay_id: "dy...", qr_code: "..."}
        """
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

    # ---- 通用查询 / 关单 ----

    def query(self, transaction_id: str, *, mchid: str | None = None) -> dict:
        """通过抖音支付订单号查询订单。

        Args:
            transaction_id: 抖音支付系统生成的订单号，长度1-32。
            mchid: 直连商户号，默认使用 Config 中配置的值。

        Returns:
            包含 trade_state、amount、payer、success_time 等完整的订单信息。
        """
        mid = mchid or self._client.config.mchid
        return self._request("GET", f"/v1/trade/transactions/id/{transaction_id}?mchid={mid}")

    def query_by_out_trade_no(self, out_trade_no: str, *, mchid: str | None = None) -> dict:
        """通过商户订单号查询订单。

        Args:
            out_trade_no: 商户系统内部订单号，长度6-32。
            mchid: 直连商户号，默认使用 Config 中配置的值。

        Returns:
            包含 trade_state、amount、payer、success_time 等完整的订单信息。
        """
        mid = mchid or self._client.config.mchid
        return self._request("GET", f"/v1/trade/transactions/out-trade-no/{out_trade_no}?mchid={mid}")

    def close(self, out_trade_no: str, *, mchid: str | None = None) -> dict:
        """关闭未支付的订单。

        注：关单没有时间限制，建议在订单生成后间隔几分钟（最短5分钟）再调用。

        Args:
            out_trade_no: 商户订单号，长度6-32。
            mchid: 直连商户号，默认使用 Config 中配置的值。

        Returns:
            空字典（HTTP 200 表示成功）。
        """
        mid = mchid or self._client.config.mchid
        return self._request("POST", f"/v1/trade/transactions/out-trade-no/{out_trade_no}/close", {"mchid": mid})


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
    """构造客户端调起支付签名（App/JSAPI 通用）。

    签名串格式（4行，每行以 \\n 结束）：
        appid
        timestamp
        noncestr
        prepayid
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
