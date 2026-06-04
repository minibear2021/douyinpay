"""退款 API 服务 — 申请退款、查询退款。"""

from douyinpay.api._base import BaseService


class RefundService(BaseService):
    """退款相关接口。"""

    def create(
        self,
        *,
        out_refund_no: str,
        amount: dict,
        transaction_id: str | None = None,
        out_trade_no: str | None = None,
        reason: str | None = None,
        notify_url: str | None = None,
        mchid: str | None = None,
    ) -> dict:
        """申请退款。

        Args:
            out_refund_no: 商户退款单号，只能是数字、大小写字母_-|*@，商户系统内部唯一，长度1-64。
            amount: 金额信息，格式为 {"refund": int(分), "total": int(分), "currency": "CNY"}。
            transaction_id: 抖音支付订单号，与 out_trade_no 二选一。
            out_trade_no: 商户订单号，与 transaction_id 二选一。
            reason: 退款原因，会展示在用户的退款消息中，非必填，最长80个字符。
            notify_url: 退款结果通知地址，优先于商户平台配置的回调地址，非必填。
            mchid: 直连商户号，默认使用 Config 中配置的值。

        Returns:
            包含 refund_id、out_refund_no、status 等退款信息。
            status 枚举: SUCCESS(成功) / PROCESSING(处理中) / CLOSED(已关闭)。
        """
        body = _remove_none({
            "transaction_id": transaction_id,
            "out_trade_no": out_trade_no,
            "out_refund_no": out_refund_no,
            "amount": amount,
            "reason": reason,
            "notify_url": notify_url,
            "mchid": mchid or self._client.config.mchid,
        })
        return self._request("POST", "/v1/trade/refund/domestic/refunds", body)

    def query_by_out_refund_no(self, out_refund_no: str, *, mchid: str | None = None) -> dict:
        """通过商户退款单号查询退款状态。

        建议在提交退款申请后 1 分钟发起查询。

        Args:
            out_refund_no: 商户退款单号，长度1-64。
            mchid: 直连商户号，默认使用 Config 中配置的值。

        Returns:
            包含 refund_id、status、amount、channel 等退款详情。
            status 枚举: SUCCESS(成功) / PROCESSING(处理中) / CLOSED(关闭) / ABNORMAL(异常)。
        """
        mid = mchid or self._client.config.mchid
        return self._request("GET", f"/v1/trade/refund/domestic/refunds/{out_refund_no}?mchid={mid}")


def _remove_none(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None}
