"""分账 API 服务 — 请求分账、完结分账、查询分账、分账回退、添加分账接收方。"""

from douyinpay.api._base import BaseService


class ProfitSharingService(BaseService):
    """分账相关接口。

    请求分账和完结分账为异步受理模式，最终结果通过回调通知或查询接口获取。
    """

    def create_order(
        self,
        *,
        appid: str,
        transaction_id: str,
        out_order_no: str,
        receivers: list[dict],
        unfreeze_unsplit: bool = True,
        notify_url: str | None = None,
        mchid: str | None = None,
    ) -> dict:
        """请求分账。

        订单支付成功后，将结算后的资金分给分账接收方。
        单笔订单最多发起 50 次分账请求，每次最多分给 50 个接收方。

        Args:
            appid: 应用ID，商户在抖音开放平台申请的应用ID，全局唯一。
            transaction_id: 抖音支付订单号，原支付交易对应的订单号。
            out_order_no: 商户分账单号，只能是数字、大小写字母_-*，商户系统内部唯一，长度6-32。
            receivers: 分账接收方列表，每项包含:
                - type: 分账接收方类型，MERCHANT_ID（商户号）或 PERSONAL_OPENID（个人OpenID）
                - account: 分账接收方账号（商户号或个人 OpenID）
                - amount: 分账金额，单位为分
                - description: 分账描述
                - name: 分账接收方全称（MERCHANT_ID 时必传，需用平台证书公钥加密）
            unfreeze_unsplit: 是否解冻剩余未分账资金，true 表示剩余资金结算给商户。
            notify_url: 分账结果回调地址，非必填。
            mchid: 直连商户号，默认使用 Config 中配置的值。

        Returns:
            {"transaction_id": "...", "out_order_no": "...", "order_id": "...", "mchid": "..."}
        """
        body = _remove_none({
            "appid": appid,
            "transaction_id": transaction_id,
            "out_order_no": out_order_no,
            "receivers": receivers,
            "unfreeze_unsplit": unfreeze_unsplit,
            "notify_url": notify_url,
            "mchid": mchid or self._client.config.mchid,
        })
        return self._request("POST", "/v1/trade/profitsharing/orders", body)

    def finish_order(
        self,
        *,
        transaction_id: str,
        out_order_no: str,
        description: str | None = None,
        notify_url: str | None = None,
        mchid: str | None = None,
    ) -> dict:
        """完结分账。

        将剩余未分账的金额全部解冻给本商户。异步处理模式。

        Args:
            transaction_id: 抖音支付订单号。
            out_order_no: 商户分账单号。
            description: 完结分账原因描述，会在分账账单中体现，非必填。
            notify_url: 通知地址，非必填。
            mchid: 直连商户号，默认使用 Config 中配置的值。

        Returns:
            {"transaction_id": "...", "out_order_no": "...", "order_id": "...", "mchid": "..."}
        """
        body = _remove_none({
            "transaction_id": transaction_id,
            "out_order_no": out_order_no,
            "description": description,
            "notify_url": notify_url,
            "mchid": mchid or self._client.config.mchid,
        })
        return self._request("POST", "/v1/trade/profitsharing/finish-orders", body)

    def query(
        self,
        out_order_no: str,
        *,
        transaction_id: str,
        mchid: str | None = None,
    ) -> dict:
        """查询分账结果。

        商户分账单号和抖音支付分账单号二选一。

        Args:
            out_order_no: 商户分账单号。
            transaction_id: 抖音支付订单号。
            mchid: 直连商户号，默认使用 Config 中配置的值。

        Returns:
            包含 state（分账单状态）、receivers（分账接收方列表及分账结果）等详情。
            state 枚举: PROCESSING(处理中) / FINISHED(分账完成)
        """
        mid = mchid or self._client.config.mchid
        path = f"/v1/trade/profitsharing/orders/{out_order_no}?transaction_id={transaction_id}&mchid={mid}"
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
        """分账回退。

        将已分账的资金从分账接收方回退给分账方。
        仅支持对 MERCHANT_ID 类型且分账成功（result=SUCCESS）的分账进行回退，回退时限为 180 天。

        Args:
            out_order_no: 商户分账单号。
            out_return_no: 商户回退单号，商户系统内部唯一。
            return_mchid: 回退商户号（原分账接收方商户号）。
            amount: 回退金额，单位为分，不能超过原始分给该接收方的金额。
            description: 回退原因描述。
            mchid: 直连商户号，默认使用 Config 中配置的值。

        Returns:
            包含 out_order_no、out_return_no、return_id、result 等回退详情。
            result 枚举: PROCESSING(处理中) / SUCCESS(已成功) / FAILED(已失败)
        """
        body = _remove_none({
            "out_order_no": out_order_no,
            "out_return_no": out_return_no,
            "return_mchid": return_mchid,
            "amount": amount,
            "description": description,
            "mchid": mchid or self._client.config.mchid,
        })
        return self._request("POST", "/v1/trade/profitsharing/return-orders", body)

    def add_receiver(
        self,
        *,
        appid: str,
        type: str,
        account: str,
        name: str,
        relation_type: str,
        custom_relation: str | None = None,
        mchid: str | None = None,
    ) -> dict:
        """添加分账接收方。

        商户分账接收方数量上限为 2 万。

        Args:
            appid: 商户应用ID。
            type: 分账接收方类型，MERCHANT_ID（商户号）或 PERSONAL_OPENID（个人OpenID）。
            account: 分账接收方账号（MERCHANT_ID 时为商户号，PERSONAL_OPENID 时为 OpenID）。
            name: 分账接收方全称，需使用抖音支付平台证书公钥加密（RSA-PKCS#1 v1.5）。
            relation_type: 与分账方的关系类型，枚举值: SERVICE_PROVIDER(服务商) / STORE(门店) /
                STAFF(员工) / STORE_OWNER(店主) / PARTNER(合作伙伴) / HEADQUARTER(总部) /
                BRAND(品牌方) / DISTRIBUTOR(分销商) / USER(用户) / SUPPLIER(供应商) / CUSTOM(自定义)。
            custom_relation: 自定义分账关系，当 relation_type 为 CUSTOM 时必填，最多10个字。
            mchid: 直连商户号，默认使用 Config 中配置的值。

        Returns:
            {"type": "...", "account": "...", "name": "...", "relation_type": "..."}
        """
        body = _remove_none({
            "appid": appid,
            "type": type,
            "account": account,
            "name": name,
            "relation_type": relation_type,
            "custom_relation": custom_relation,
            "mchid": mchid or self._client.config.mchid,
        })
        return self._request("POST", "/v1/trade/profitsharing/receivers/add", body)


def _remove_none(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None}
