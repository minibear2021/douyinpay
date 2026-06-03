import json as _json
import time

import httpx

from douyinpay._auth import sign_request, build_verify_message, verify_signature
from douyinpay._certificate import CertificateManager
from douyinpay._config import Config
from douyinpay._errors import NetworkError, ServiceError, SignatureError


class AsyncDouyinPayClient:
    """Asynchronous HTTP client for the Douyin Pay API.

    Handles request signing, response verification, and automatic
    platform certificate management transparently.

    Usage::

        async with AsyncDouyinPayClient(config) as client:
            resp = await client.payments.app_prepay(...)
    """

    def __init__(self, config: Config) -> None:
        self._config = config
        self._cert_mgr = CertificateManager(config.encrypt_key_bytes, config.sign_type)
        self._http = httpx.AsyncClient(
            base_url=config.base_url,
            timeout=30,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        self._setup_cert_fetcher()

    def _setup_cert_fetcher(self) -> None:
        # The cert fetcher uses a sync client to avoid asyncio nesting issues.
        # This is fine because cert downloads are infrequent (every 6 hours).
        sync_http = httpx.Client(
            base_url=self._config.base_url,
            timeout=30,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

        def fetch() -> dict:
            path = "/v1/merchant/certificates/getPlatformCertificates"
            body_str = ""
            sign_result = sign_request(
                method="GET",
                path=path,
                body=body_str,
                mchid=self._config.mchid,
                serial_no=self._config.serial_no,
                private_key_pem=self._config.private_key,
                sign_type=self._config.sign_type,
            )
            headers = {"Authorization": sign_result.to_header()}
            resp = sync_http.request("GET", path, headers=headers)
            if not resp.is_success:
                error_data = resp.json() if resp.content else {}
                raise ServiceError(
                    code=error_data.get("code", "UNKNOWN"),
                    message=error_data.get("message", resp.reason_phrase),
                    detail=error_data.get("detail"),
                )
            return resp.json() if resp.content else {}

        self._cert_mgr.set_fetcher(fetch)

    async def request(self, method: str, path: str, body: dict | None = None) -> dict:
        body_str = _json.dumps(body, separators=(",", ":")) if body else ""

        sign_result = sign_request(
            method=method,
            path=path,
            body=body_str,
            mchid=self._config.mchid,
            serial_no=self._config.serial_no,
            private_key_pem=self._config.private_key,
            sign_type=self._config.sign_type,
        )

        headers = {"Authorization": sign_result.to_header()}

        try:
            resp = await self._http.request(method, path, content=body_str or None, headers=headers)
        except httpx.HTTPError as e:
            raise NetworkError(str(e), e)

        self._verify_response(resp)

        if not resp.is_success:
            error_data = resp.json() if resp.content else {}
            raise ServiceError(
                code=error_data.get("code", "UNKNOWN"),
                message=error_data.get("message", resp.reason_phrase),
                detail=error_data.get("detail"),
            )

        return resp.json() if resp.content else {}

    def _verify_response(self, resp: httpx.Response) -> None:
        sig = resp.headers.get("Douyinpay-Signature")
        ts = resp.headers.get("Douyinpay-Timestamp")
        nonce = resp.headers.get("Douyinpay-Nonce")
        serial = resp.headers.get("Douyinpay-Serial")

        if not all([sig, ts, nonce, serial]):
            return

        now = int(time.time())
        if abs(now - int(ts)) >= 300:
            raise SignatureError(
                f"Response timestamp {ts} is outside the 5-minute window (now: {now})"
            )

        self._cert_mgr.ensure_certificates()
        cert_pem = self._cert_mgr.get_certificate(serial)
        if cert_pem is None:
            raise SignatureError(f"Unknown certificate serial in response: {serial}")

        message = build_verify_message(int(ts), nonce, resp.text)
        verify_signature(message, sig, cert_pem)

    @property
    def cert_manager(self) -> CertificateManager:
        return self._cert_mgr

    @property
    def config(self) -> Config:
        return self._config

    @property
    def payments(self):
        from douyinpay.api.payments import PaymentsService
        return PaymentsService(self)

    @property
    def refunds(self):
        from douyinpay.api.refund import RefundService
        return RefundService(self)

    @property
    def bills(self):
        from douyinpay.api.bill import BillService
        return BillService(self)

    @property
    def profit_sharing(self):
        from douyinpay.api.profit_sharing import ProfitSharingService
        return ProfitSharingService(self)

    @property
    def transfers(self):
        from douyinpay.api.transfer import TransferService
        return TransferService(self)

    @property
    def certificates(self):
        from douyinpay.api.certificate import CertificateService
        return CertificateService(self)

    async def close(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "AsyncDouyinPayClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
