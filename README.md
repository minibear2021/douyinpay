# 抖音支付 Python SDK

抖音支付服务端 Python SDK，支持同步和异步接口调用、RSA/SM2 双算法签名、平台证书自动管理、回调通知解析。适用于后端开发者快速集成抖音支付能力。

## 环境要求

- Python 3.10+

## 安装

```bash
pip install douyinpay
```

## 依赖

- [httpx](https://www.python-httpx.org/) — HTTP 客户端（同步 + 异步）
- [cryptography](https://cryptography.io/) — RSA 签名/验签、AES 加解密
- [gmssl](https://github.com/duanhongyi/gmssl) — SM2 国密算法

## 快速开始

### 1. 初始化客户端

**同步客户端：**

```python
from douyinpay import Config, DouyinPayClient

config = Config(
    mchid="8020221008775523",           # 商户号
    serial_no="41A48FEF2A9F04C5",       # 商户API证书序列号
    private_key="""-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQ...
-----END PRIVATE KEY-----""",          # 商户私钥（PEM 字符串，非文件路径）
    encrypt_key="0123456789abcdef0123456789abcdef",  # 平台生成的密钥字符串
    sign_type="RSA",                    # 签名算法："RSA" 或 "SM2"
)

client = DouyinPayClient(config)
```

**异步客户端：**

```python
from douyinpay import Config, AsyncDouyinPayClient

config = Config(...)

async def main():
    async with AsyncDouyinPayClient(config) as client:
        resp = await client.payments.app_prepay(...)
```

> **密钥获取方式**：登录[抖音支付商家平台](https://pay.douyinpay.com/) → 产品中心 → 密钥管理，生成商户API证书并设置接口加密密钥。

### 2. 调用 API

同步和异步客户端共用相同的 API 方法名和参数，区别仅在于异步调用需要 `await`：

```python
# 同步
resp = client.payments.app_prepay(
    appid="awz9w2wncdof4ba6",
    description="测试商品",
    out_trade_no="ORD20240601001",
    notify_url="https://example.com/notify",
    amount={"total": 100, "currency": "CNY"},
)

# 异步（在 async def 中）
resp = await client.payments.app_prepay(
    appid="awz9w2wncdof4ba6",
    description="测试商品",
    out_trade_no="ORD20240601001",
    notify_url="https://example.com/notify",
    amount={"total": 100, "currency": "CNY"},
)
```

常用接口示例：

```python
# 查询订单
order = client.payments.query("TXN001")
order = client.payments.query_by_out_trade_no("ORD20240601001")

# 关闭订单（使用商户订单号关单）
client.payments.close("ORD20240601001")

# 退款
refund = client.refunds.create(
    transaction_id="TXN001", out_refund_no="REF001",
    amount={"refund": 100, "total": 100, "currency": "CNY"},
)
refund_info = client.refunds.query_by_out_refund_no("REF001")

# 账单
bill = client.bills.trade("2024-06-01")
bill_content = client.bills.download(bill["download_url"])

# 商户转账（单笔转账到用户抖音零钱）
client.transfers.create_batch(
    appid="awz9w2wncdof4ba6",
    out_bill_no="BILL001",
    transfer_scene_id="SCENE_001",
    openid="oUpF8uMEB4jR",
    transfer_amount=100,
    transfer_remark="商户转账",
)

# 分账
client.profit_sharing.create_order(
    appid="awz9w2wncdof4ba6",
    transaction_id="TXN001", out_order_no="PS001",
    receivers=[{"type": "MERCHANT_ID", "account": "6000000000000002", "amount": 30, "description": "分账给子商户"}],
)
```

### 3. 客户端调起支付签名

```python
# App/JSAPI 调起支付参数
params = client.payments.sign_for_client(
    appid="awz9w2wncdof4ba6", prepay_id="dy11ys5s7sxyv43x...",
)
# 返回: {appid, partnerid, prepayid, package, noncestr, timestamp, sign}
```

### 4. 处理回调通知

```python
from douyinpay import NotificationParser

parser = NotificationParser(config, client.cert_manager)

# 在 Web 框架中（以 FastAPI 为例）
@app.post("/notify")
async def payment_notify(request: Request):
    body = await request.body()
    try:
        data = parser.parse(
            body=body.decode(),
            signature=request.headers["Douyinpay-Signature"],
            timestamp=request.headers["Douyinpay-Timestamp"],
            nonce=request.headers["Douyinpay-Nonce"],
            serial=request.headers["Douyinpay-Serial"],
        )
        print(f"订单 {data['out_trade_no']} 支付状态: {data['trade_state']}")
    except SignatureError:
        # 验签失败：返回 4XX + 应答报文
        return Response(status_code=401, content='{"code":"FAIL","message":"signature error"}')
    except DecryptionError:
        # 解密失败：返回 5XX + 应答报文
        return Response(status_code=500, content='{"code":"FAIL","message":"decryption error"}')
    # 处理成功：返回 200 或 204，无需应答报文
    return Response(status_code=200)
```

### 5. 上下文管理器

```python
# 同步
with DouyinPayClient(config) as client:
    resp = client.payments.app_prepay(...)

# 异步
async with AsyncDouyinPayClient(config) as client:
    resp = await client.payments.app_prepay(...)
```

## 支持的 API

| 类别 | 方法 | 说明 |
|------|------|------|
| **支付** | `client.payments.app_prepay()` | App 支付下单 |
| | `client.payments.h5_prepay()` | H5 支付下单 |
| | `client.payments.jsapi_prepay()` | JSAPI 支付下单 |
| | `client.payments.native_prepay()` | Native 支付下单 |
| | `client.payments.query()` | 按交易号查询 |
| | `client.payments.query_by_out_trade_no()` | 按商户订单号查询 |
| | `client.payments.close()` | 关闭订单 |
| | `client.payments.sign_for_client()` | App/JSAPI 调起支付签名 |
| **退款** | `client.refunds.create()` | 申请退款 |
| | `client.refunds.query_by_out_refund_no()` | 查询退款 |
| **账单** | `client.bills.trade()` | 申请交易账单 |
| | `client.bills.fund()` | 申请资金账单 |
| | `client.bills.settlement()` | 申请结算账单 |
| | `client.bills.profit_sharing()` | 申请分账账单 |
| | `client.bills.download()` | 下载账单文件 |
| **分账** | `client.profit_sharing.create_order()` | 请求分账 |
| | `client.profit_sharing.finish_order()` | 完结分账 |
| | `client.profit_sharing.query()` | 查询分账结果 |
| | `client.profit_sharing.create_return()` | 分账回退 |
| | `client.profit_sharing.add_receiver()` | 添加分账接收方 |
| **转账** | `client.transfers.create_batch()` | 商家转账 |
| | `client.transfers.query_batch()` | 查询转账 |
| **证书** | `client.certificates.get_platform_certificates()` | 下载平台证书 |

异步客户端将 `client` 替换为 `await client.xxx(...)` 即可，方法签名相同。

## 异常处理

```python
from douyinpay import (
    DouyinPayError,     # 所有异常的基类
    ServiceError,       # API 业务错误（含 code / message / detail）
    SignatureError,     # 签名/验签失败
    DecryptionError,    # AES 解密失败
    NetworkError,       # 网络异常
)

try:
    resp = client.payments.app_prepay(...)
except ServiceError as e:
    print(f"业务错误: [{e.code}] {e.message}")
except NetworkError as e:
    print(f"网络错误: {e}")
```

## SM2 国密算法

```python
config = Config(
    mchid="8020221008775523",
    serial_no="...",
    private_key="...",     # SM2 私钥
    encrypt_key="...",     # 平台生成的密钥字符串
    sign_type="SM2",
)
client = DouyinPayClient(config)
# 后续调用与 RSA 模式完全相同，同样支持 AsyncDouyinPayClient
```

## 架构

```
douyinpay/
  __init__.py           # 导出 Config, DouyinPayClient, AsyncDouyinPayClient, NotificationParser
  _config.py            # 配置 dataclass
  _errors.py            # 异常体系
  _auth.py              # RSA / SM2 签名与验签
  _cipher.py            # AES-GCM 加解密
  _certificate.py       # 平台证书管理器（自动下载、解密、缓存、定时刷新）
  _client.py            # 同步 HTTP 客户端
  _async_client.py      # 异步 HTTP 客户端
  _notification.py      # 回调通知解析器（验签 + 解密）
  api/
    payments.py         # 支付服务
    refund.py           # 退款服务
    bill.py             # 账单服务
    profit_sharing.py   # 分账服务
    transfer.py         # 转账服务
    certificate.py      # 证书 API
```

## 开发

```bash
pip install -r requirements.txt
pip install pytest pytest-asyncio
pip install -e .
pytest tests/ -v        # 运行全部 68 个测试
```
