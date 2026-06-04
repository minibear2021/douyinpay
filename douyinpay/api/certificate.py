"""证书管理 API 服务 — 下载抖音支付平台证书。

平台证书用于验证回调签名和加密敏感字段。证书每 6 小时自动刷新。
"""

from douyinpay.api._base import BaseService


class CertificateService(BaseService):
    """证书下载接口。

    返回的证书内容经 AES-GCM 加密，由 CertificateManager 自动解密。
    """

    def get_platform_certificates(self) -> list[dict]:
        """下载平台证书列表。

        返回解密后的证书信息。调用频率限制：单个商户号 100 次/秒。

        Returns:
            证书列表，每项包含:
            - cert_no: 证书序列号
            - cert_type: 证书类型（RSA）
            - effective_time: 生效时间，格式 YYMMDDHHMMSS
            - expire_time: 失效时间，格式 YYMMDDHHMMSS
            - cert_pem: 解密后的 PEM 格式公钥
        """
        cert_mgr = self._client.cert_manager
        cert_mgr._update()
        certs = []
        with cert_mgr._lock:
            for serial_no, cert_pem in sorted(cert_mgr._certs.items()):
                certs.append({"cert_no": serial_no, "cert_pem": cert_pem})
        return certs
