import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


RSA_CERT_SERIAL = "41A48FEF2A9F04C5"


@pytest.fixture(scope="session")
def rsa_private_key_pem() -> str:
    """Generate a 2048-bit RSA private key and return it as a PEM string."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend(),
    )
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")


@pytest.fixture(scope="session")
def rsa_public_key_pem(rsa_private_key_pem: str) -> str:
    """Extract the public key from the private key and return it as a PEM string."""
    private_key = serialization.load_pem_private_key(
        rsa_private_key_pem.encode("utf-8"),
        password=None,
        backend=default_backend(),
    )
    public_key = private_key.public_key()
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")


@pytest.fixture(scope="session")
def sm2_key_hex() -> tuple[str, str]:
    """Generate an SM2 key pair and return (private_key_hex, public_key_hex)."""
    import secrets
    from gmssl.sm2 import default_ecc_table

    n = int(default_ecc_table["n"], 16)
    g = default_ecc_table["g"]

    private_hex = format(secrets.randbelow(n - 1) + 1, "064x")

    tmp = __import__("gmssl.sm2").sm2.CryptSM2(
        private_key=private_hex, public_key="00" * 64
    )
    public_hex = tmp._kg(int(private_hex, 16), g)

    from gmssl.sm2 import CryptSM2 as CSM2
    sm = CSM2(private_key=private_hex, public_key=public_hex)
    k_hex = secrets.token_hex(32)
    sig = sm.sign(b"keygen_test", k_hex)
    assert sm.verify(sig, b"keygen_test"), "SM2 key pair verification failed"

    return private_hex, public_hex


@pytest.fixture(scope="session")
def rsa_cert_serial() -> str:
    return "41A48FEF2A9F04C5"


@pytest.fixture(scope="session")
def test_mchid() -> str:
    return "8020221008775523"


@pytest.fixture(scope="session")
def test_encrypt_key() -> str:
    return "0123456789abcdef0123456789abcdef"  # 32 ASCII chars → 32 bytes
