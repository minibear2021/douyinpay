"""转账 API 服务 — 商家向用户抖音零钱转账及查询转账单。"""

from douyinpay.api._base import BaseService


class TransferService(BaseService):
    """商家转账到抖音零钱相关接口。

    仅支持查询 30 天内的转账单，超过 30 天请通过资金账单获取。
    """

    def create_batch(
        self,
        *,
        appid: str,
        out_bill_no: str,
        transfer_scene_id: str,
        openid: str,
        transfer_amount: int,
        transfer_remark: str,
        user_name: str | None = None,
        notify_url: str | None = None,
        user_recv_perception: str | None = None,
        transfer_scene_report_infos: list[dict] | None = None,
        mchid: str | None = None,
    ) -> dict:
        """商家转账到用户抖音零钱。

        Args:
            appid: 商户在抖音开放平台申请的 AppID，需与商户号绑定。
            out_bill_no: 商户订单号，只能是数字、大小写字母_-*且在同一个商户号下唯一，长度6-32。
            transfer_scene_id: 转账场景 ID，需为商户已开通且已生效的场景。
            openid: 收款用户在商户 AppID 下的唯一标识，需已完成抖音实名认证。
            transfer_amount: 转账金额，单位为分，大于 0 且不超过单笔限额。
            transfer_remark: 转账备注，不超过 32 个字符。
            user_name: 收款用户姓名，转账金额 >= 2000.00 元时必填，需用平台证书公钥加密。
            notify_url: 转账结果回调通知地址。
            user_recv_perception: 用户收款感知文案，用于零钱入账记录展示的资金来源说明。
            transfer_scene_report_infos: 转账场景报备信息列表，每项含 info_type 和 info_content。
            mchid: 直连商户号，默认使用 Config 中配置的值。

        Returns:
            {"out_bill_no": "...", "transfer_bill_no": "...", "state": "ACCEPTED", "create_time": "..."}
            state 枚举: ACCEPTED(已受理) / TRANSFERING(转账中) / SUCCESS(成功) / FAIL(失败)
        """
        body = _remove_none({
            "appid": appid,
            "out_bill_no": out_bill_no,
            "transfer_scene_id": transfer_scene_id,
            "openid": openid,
            "transfer_amount": transfer_amount,
            "transfer_remark": transfer_remark,
            "user_name": user_name,
            "notify_url": notify_url,
            "user_recv_perception": user_recv_perception,
            "transfer_scene_report_infos": transfer_scene_report_infos,
            "mchid": mchid or self._client.config.mchid,
        })
        return self._request("POST", "/v1/fund_trade/mch-transfer/transfer-bills", body)

    def query_batch(self, out_bill_no: str) -> dict:
        """通过商户订单号查询转账单。

        Args:
            out_bill_no: 商户订单号，长度6-32。

        Returns:
            包含 transfer_bill_no、state、transfer_amount、openid 等转账详情。
            state 枚举: ACCEPTED / TRANSFERING / SUCCESS / FAIL
        """
        return self._request(
            "GET",
            f"/v1/fund_trade/mch-transfer/transfer-bills/out-bill-no/{out_bill_no}",
        )

    def query_by_transfer_bill_no(self, transfer_bill_no: str) -> dict:
        """通过抖音转账单号查询转账单。

        Args:
            transfer_bill_no: 抖音支付系统生成的转账单号。

        Returns:
            包含 transfer_bill_no、state、transfer_amount 等转账详情。
        """
        return self._request(
            "GET",
            f"/v1/fund_trade/mch-transfer/transfer-bills/transfer-bill-no/{transfer_bill_no}",
        )


def _remove_none(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None}
