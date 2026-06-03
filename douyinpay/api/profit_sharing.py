"""Profit sharing API service."""

from douyinpay.api._base import BaseService


class ProfitSharingService(BaseService):
    """Service for profit sharing operations."""

    def create_order(
        self,
        *,
        transaction_id: str,
        out_order_no: str,
        receivers: list[dict],
        unfreeze_unsplit: bool = True,
        mchid: str | None = None,
    ) -> dict:
        """Create a profit sharing order."""
        body = _remove_none({
            "transaction_id": transaction_id,
            "out_order_no": out_order_no,
            "receivers": receivers,
            "unfreeze_unsplit": unfreeze_unsplit,
            "mchid": mchid or self._client.config.mchid,
        })
        return self._request("POST", "/v1/profitsharing/orders", body)

    def finish_order(self, transaction_id: str, *, mchid: str | None = None) -> dict:
        """Finish (unfreeze remaining) a profit sharing order."""
        mid = mchid or self._client.config.mchid
        return self._request(
            "POST",
            f"/v1/profitsharing/orders/{transaction_id}/finish",
            {"transaction_id": transaction_id, "mchid": mid},
        )

    def query(self, out_order_no: str, *, transaction_id: str, mchid: str | None = None) -> dict:
        """Query a profit sharing result."""
        mid = mchid or self._client.config.mchid
        path = f"/v1/profitsharing/orders/{out_order_no}?transaction_id={transaction_id}&mchid={mid}"
        return self._request("GET", path)

    def create_return(
        self,
        *,
        out_order_no: str,
        out_return_no: str,
        return_mchid: str,
        amount: int,
        description: str,
        mchid: str | None = None,
    ) -> dict:
        """Create a profit sharing return (refund of shared funds)."""
        body = {
            "out_order_no": out_order_no,
            "out_return_no": out_return_no,
            "return_mchid": return_mchid,
            "amount": amount,
            "description": description,
            "mchid": mchid or self._client.config.mchid,
        }
        return self._request("POST", "/v1/profitsharing/return-orders", body)

    def add_receiver(
        self,
        *,
        receiver_mchid: str,
        name: str,
        relation_type: str,
        mchid: str | None = None,
    ) -> dict:
        """Add a profit sharing receiver."""
        body = {
            "receiver_mchid": receiver_mchid,
            "name": name,
            "relation_type": relation_type,
            "mchid": mchid or self._client.config.mchid,
        }
        return self._request("POST", "/v1/profitsharing/receivers/add", body)


def _remove_none(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None}
