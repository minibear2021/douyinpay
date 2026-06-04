"""账单 API 服务 — 申请交易/资金/结算/分账账单及下载账单文件。"""

from douyinpay.api._base import BaseService


class BillService(BaseService):
    """账单相关接口。

    所有申请类接口返回 {"download_url": "...", "hash_type": "SHA1", "hash_value": "..."}
    download_url 有效期为 5 分钟，建议在次日 10 点后获取。
    """

    def trade(self, bill_date: str, *, mchid: str | None = None, tar_type: str = "GZIP") -> dict:
        """申请交易账单。

        Args:
            bill_date: 账单日期，格式 yyyy-MM-dd，仅支持三个月内的账单。
            mchid: 直连商户号，默认使用 Config 中配置的值。
            tar_type: 压缩类型，枚举值: GZIP（返回 .gzip 压缩包）。

        Returns:
            {"download_url": "...", "hash_type": "SHA1", "hash_value": "..."}
        """
        mid = mchid or self._client.config.mchid
        return self._request(
            "GET",
            f"/v1/bill/tradebill?mchid={mid}&bill_date={bill_date}&tar_type={tar_type}",
        )

    def fund(self, bill_date: str, *, mchid: str | None = None, tar_type: str = "GZIP") -> dict:
        """申请资金账单。

        Args:
            bill_date: 账单日期，格式 yyyy-MM-dd。
            mchid: 直连商户号，默认使用 Config 中配置的值。
            tar_type: 压缩类型，枚举值: GZIP。

        Returns:
            {"download_url": "...", "hash_type": "SHA1", "hash_value": "..."}
        """
        mid = mchid or self._client.config.mchid
        return self._request(
            "GET",
            f"/v1/bill/fundflowbill?mchid={mid}&bill_date={bill_date}&tar_type={tar_type}",
        )

    def settlement(self, bill_date: str, *, mchid: str | None = None, tar_type: str = "GZIP") -> dict:
        """申请结算账单。

        Args:
            bill_date: 账单日期，格式 yyyy-MM-dd。
            mchid: 直连商户号，默认使用 Config 中配置的值。
            tar_type: 压缩类型，枚举值: GZIP。

        Returns:
            {"download_url": "...", "hash_type": "SHA1", "hash_value": "..."}
        """
        mid = mchid or self._client.config.mchid
        return self._request(
            "GET",
            f"/v1/bill/billapply?mchid={mid}&bill_date={bill_date}&bill_type=SETTLEMENT&tar_type={tar_type}",
        )

    def profit_sharing(self, bill_date: str, *, mchid: str | None = None, tar_type: str = "GZIP") -> dict:
        """申请分账账单。

        Args:
            bill_date: 账单日期，格式 yyyy-MM-dd。
            mchid: 直连商户号，默认使用 Config 中配置的值。
            tar_type: 压缩类型，枚举值: GZIP。

        Returns:
            {"download_url": "...", "hash_type": "SHA1", "hash_value": "..."}
        """
        mid = mchid or self._client.config.mchid
        return self._request(
            "GET",
            f"/v1/bill/splitbill?mchid={mid}&bill_date={bill_date}&tar_type={tar_type}",
        )

    def download(self, download_url: str) -> bytes:
        """下载账单文件。

        Args:
            download_url: 由申请账单接口返回的 download_url，有效期 5 分钟。

        Returns:
            账单文件的原始字节内容。
        """
        import httpx
        resp = httpx.get(download_url, timeout=60)
        resp.raise_for_status()
        return resp.content
