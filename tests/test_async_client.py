import pytest

from douyinpay._async_client import AsyncDouyinPayClient
from douyinpay._config import Config


@pytest.fixture
def async_config(rsa_private_key_pem):
    return Config(
        mchid="123",
        serial_no="ABC",
        private_key=rsa_private_key_pem,
        encrypt_key="0123456789abcdef0123456789abcdef",
        sign_type="RSA",
    )


@pytest.mark.anyio
async def test_async_client_creation(async_config):
    client = AsyncDouyinPayClient(async_config)
    assert client.config.mchid == "123"
    assert client.payments is not None
    await client.close()


@pytest.mark.anyio
async def test_async_client_context_manager(async_config):
    async with AsyncDouyinPayClient(async_config) as client:
        assert client._http is not None
