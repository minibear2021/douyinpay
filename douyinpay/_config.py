from dataclasses import dataclass, field


SIGN_TYPES = ("RSA", "SM2")


@dataclass(frozen=True)
class Config:
    mchid: str
    serial_no: str
    private_key: str
    encrypt_key: str
    sign_type: str = "RSA"
    base_url: str = "https://api.douyinpay.com"

    _encrypt_key_bytes: bytes = field(init=False, repr=False)

    def __post_init__(self):
        if self.sign_type not in SIGN_TYPES:
            raise ValueError(
                f"sign_type must be one of {SIGN_TYPES}, got {self.sign_type}"
            )
        # The platform generates a raw ASCII string to be used directly
        # as the AES key bytes (typically 32 characters → AES-256).
        key_bytes = self.encrypt_key.encode("ascii")
        object.__setattr__(self, "_encrypt_key_bytes", key_bytes)

    @property
    def encrypt_key_bytes(self) -> bytes:
        return self._encrypt_key_bytes
