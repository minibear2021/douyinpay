"""Refund API service."""

from douyinpay.api._base import BaseService


class RefundService(BaseService):
    """Service for refund operations."""

    def create(
        self,
        *,
        transaction_id: str | None = None,
        out_trade_no: str | None = None,
        out_refund_no: str,
        amount: dict,
        reason: str | None = None,
        notify_url: str | None = None,
        mchid: str | None = None,
    ) -> dict:
        """Create a refund. Either transaction_id or out_trade_no must be provided."""
        body = _remove_none({
            "transaction_id": transaction_id,
            "out_trade_no": out_trade_no,
            "out_refund_no": out_refund_no,
            "amount": amount,
            "reason": reason,
            "notify_url": notify_url,
            "mchid": mchid or self._client.config.mchid,
        })
        return self._request("POST", "/v1/trade/refunds", body)

    def query_by_out_refund_no(self, out_refund_no: str, *, mchid: str | None = None) -> dict:
        """Query a refund by merchant's out_refund_no."""
        mid = mchid or self._client.config.mchid
        return self._request("GET", f"/v1/trade/refunds/out-refund-no/{out_refund_no}?mchid={mid}")


def _remove_none(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None}
