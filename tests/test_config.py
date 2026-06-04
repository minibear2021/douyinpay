import pytest
from douyinpay._config import Config, SIGN_TYPES


VALID_PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJFb5l2AXz0c
GqgqGqgqGqgqGqgqGqgqGqgqGqgqGqgqGqgqGqgqGqgqGqgqGqgqGqgqGqgqGqgq
GqgqGqgqGqgqGqgqGqgqGqgqGqgqGqgqGqgqGqgqGqgqGqgqGqgqGqgqGqgqGqgq
-----END PRIVATE KEY-----"""
VALID_KEY = "0123456789abcdef0123456789abcdef"  # 32 ASCII chars


class TestConfig:
    def test_config_creation(self):
        cfg = Config(
            mchid="8020221008775523",
            serial_no="41A48FEF2A9F04C5",
            private_key=VALID_PRIVATE_KEY,
            encrypt_key=VALID_KEY,
        )
        assert cfg.encrypt_key_bytes == b"0123456789abcdef0123456789abcdef"

    def test_sm2_config(self):
        cfg = Config(
            mchid="8020221008775523",
            serial_no="41A48FEF2A9F04C5",
            private_key=VALID_PRIVATE_KEY,
            encrypt_key=VALID_KEY,
            sign_type="SM2",
        )
        assert cfg.sign_type == "SM2"

    def test_invalid_sign_type(self):
        with pytest.raises(ValueError, match="sign_type must be one of"):
            Config(mchid="x", serial_no="x", private_key="x", encrypt_key=VALID_KEY, sign_type="INVALID")

    def test_base_url_defaults(self):
        cfg = Config(mchid="x", serial_no="x", private_key="x", encrypt_key=VALID_KEY)
        assert cfg.base_url == "https://api.douyinpay.com"

    def test_base_url_custom(self):
        cfg = Config(mchid="x", serial_no="x", private_key="x", encrypt_key=VALID_KEY, base_url="https://x.com")
        assert cfg.base_url == "https://x.com"

    def test_config_is_frozen(self):
        cfg = Config(mchid="x", serial_no="x", private_key="x", encrypt_key=VALID_KEY)
        with pytest.raises(Exception):
            cfg.mchid = "changed"

    def test_sign_types_tuple(self):
        assert "RSA" in SIGN_TYPES
        assert "SM2" in SIGN_TYPES

