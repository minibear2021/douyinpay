"""Bill API service."""

from douyinpay.api._base import BaseService


class BillService(BaseService):
    """Service for downloading various bill types."""

    def trade(self, bill_date: str, *, mchid: str | None = None) -> dict:
        """Request a trade bill for the given date (YYYY-MM-DD)."""
        body = {"bill_date": bill_date, "mchid": mchid or self._client.config.mchid}
        return self._request("POST", "/v1/bill/tradebill", body)

    def fund(self, bill_date: str, *, mchid: str | None = None) -> dict:
        """Request a fund bill."""
        body = {"bill_date": bill_date, "mchid": mchid or self._client.config.mchid}
        return self._request("POST", "/v1/bill/fundbill", body)

    def settlement(self, bill_date: str, *, mchid: str | None = None) -> dict:
        """Request a settlement bill."""
        body = {"bill_date": bill_date, "mchid": mchid or self._client.config.mchid}
        return self._request("POST", "/v1/bill/settlementbill", body)

    def profit_sharing(self, bill_date: str, *, mchid: str | None = None) -> dict:
        """Request a profit sharing bill."""
        body = {"bill_date": bill_date, "mchid": mchid or self._client.config.mchid}
        return self._request("POST", "/v1/bill/profitsharingbill", body)

    def download(self, download_url: str) -> bytes:
        """Download a bill file from the given URL (returned by the request APIs)."""
        import httpx
        resp = httpx.get(download_url, timeout=60)
        resp.raise_for_status()
        return resp.content
