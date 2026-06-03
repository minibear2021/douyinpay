# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

抖音支付 (Douyin Pay) server-side Python SDK. Two phases:

**Phase 1 — Documentation downloader**: COMPLETE. Run `python -m douyinpay.tools.download_docs` to re-download. Extracts `_arcosite_data` JSON from wiki pages, downloads all `.md` files to `docs/`. 315 pages across 5 libraries.

**Phase 2 — Python SDK**: COMPLETE. Sync (`DouyinPayClient`) and async (`AsyncDouyinPayClient`) clients with RSA/SM2 signing, automatic platform certificate management, AES-GCM callback decryption. Both clients share the same API.

## Environment

- **Python**: 3.13.5
- **Virtual env**: `.venv/` (activate with `.venv\Scripts\activate`)
- **Dependencies**: httpx, cryptography, gmssl, pytest, pytest-asyncio (see `requirements.txt`)

## Commands

```powershell
pip install -r requirements.txt
pip install -e .                    # install SDK in dev mode
python -m douyinpay.tools.download_docs   # re-download docs
pytest tests/ -v                    # run all tests (68 tests)
pytest tests/test_auth.py -v        # run specific test file
```

## Architecture

```
douyinpay/
  __init__.py           # exports Config, DouyinPayClient, AsyncDouyinPayClient, NotificationParser
  _config.py            # frozen dataclass: mchid, serial_no, private_key, encrypt_key (raw ASCII), sign_type
  _errors.py            # DouyinPayError → ServiceError, SignatureError, DecryptionError, NetworkError
  _auth.py              # sign_request() + verify_signature(), RSA + SM2 via cryptography + gmssl
  _cipher.py            # AES-GCM encrypt/decrypt, ASCII-safe nonce (matches Go SDK)
  _certificate.py       # CertificateManager: thread-safe, fetcher callback, 6h refresh, cert_type filter
  _client.py            # DouyinPayClient: sync, auto-sign, auto-verify, service accessors
  _async_client.py      # AsyncDouyinPayClient: async, same API, httpx.AsyncClient
  _notification.py      # NotificationParser: verify + decrypt callback body
  api/
    _base.py            # BaseService: holds client ref
    payments.py         # PaymentsService: app/h5/jsapi/native prepay, query, close, client-sign
    refund.py           # RefundService: create, query_by_out_refund_no
    bill.py             # BillService: trade/fund/settlement/profitsharing bill + download
    profit_sharing.py   # ProfitSharingService: create_order, finish, query, return, add_receiver
    transfer.py         # TransferService: create_batch, query_batch
    certificate.py      # CertificateService: get_platform_certificates
  tools/
    download_docs.py    # Phase 1: fetches all wiki docs as .md
```

## SDK Usage

```python
from douyinpay import Config, DouyinPayClient, AsyncDouyinPayClient, NotificationParser

config = Config(
    mchid="8020221008775523",
    serial_no="41A48FEF2A9F04C5",
    private_key="-----BEGIN PRIVATE KEY-----\n...",
    encrypt_key="kLZwhQ9nVE20Guwc1Wog2hh1T1Z93O0H",  # platform-generated ASCII key
    sign_type="RSA",  # or "SM2"
)

# Sync
with DouyinPayClient(config) as client:
    resp = client.payments.app_prepay(...)

# Async
async with AsyncDouyinPayClient(config) as client:
    resp = await client.payments.app_prepay(...)

# Payments
resp = client.payments.app_prepay(
    appid="awz9w2wncdof4ba6",
    description="商品描述",
    out_trade_no="ORD001",
    notify_url="https://example.com/notify",
    amount={"total": 100, "currency": "CNY"},
)

# Query / Refund
order = client.payments.query("TXN001")
client.refunds.create(transaction_id="TXN001", out_refund_no="REF001", amount={"total": 100, "currency": "CNY"})

# Callback parsing
parser = NotificationParser(config, client.cert_manager)
data = parser.parse(
    body=request_body,
    signature=headers["Douyinpay-Signature"],
    timestamp=headers["Douyinpay-Timestamp"],
    nonce=headers["Douyinpay-Nonce"],
    serial=headers["Douyinpay-Serial"],
)
```

## Conventions

- `private_key` is a PEM string, not a file path — caller handles loading
- `encrypt_key` is a platform-generated ASCII string, used directly as AES key bytes (not base64/hex decoded)
- Sign/verify is transparent: Authorization header auto-generated, response signatures auto-verified
- Response timestamp is validated within a 5-minute window (matching Go SDK)
- Certificate manager auto-downloads platform certs on first request, refreshes every 6h, filters by sign_type
- Certificate nonce is used as raw bytes (not base64-decoded), matching Go SDK
- All API response dicts match the documented JSON fields (snake_case keys)
- `mchid` is optional on most service methods — defaults to the value in Config
- Sync and async clients share the same API — async calls just need `await`
