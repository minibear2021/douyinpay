"""Transfer API service (merchant transfers to Douyin wallet)."""

from douyinpay.api._base import BaseService


class TransferService(BaseService):
    """Service for merchant-to-wallet transfers."""

    def create_batch(
        self,
        *,
        out_batch_no: str,
        batch_name: str,
        total_amount: int,
        total_num: int,
        transfer_detail_list: list[dict],
        mchid: str | None = None,
    ) -> dict:
        """Create a transfer batch."""
        body = {
            "out_batch_no": out_batch_no,
            "batch_name": batch_name,
            "total_amount": total_amount,
            "total_num": total_num,
            "transfer_detail_list": transfer_detail_list,
            "mchid": mchid or self._client.config.mchid,
        }
        return self._request("POST", "/v1/transfer/batches", body)

    def query_batch(self, out_batch_no: str, *, mchid: str | None = None) -> dict:
        """Query a transfer batch by out_batch_no."""
        mid = mchid or self._client.config.mchid
        return self._request("GET", f"/v1/transfer/batches/out-batch-no/{out_batch_no}?mchid={mid}")
