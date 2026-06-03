import secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from douyinpay._errors import DecryptionError


def aes_decrypt(key: bytes, ciphertext: bytes, nonce: bytes, associated_data: bytes) -> bytes:
    """Decrypt data using AES-GCM.

    Args:
        key: symmetric key (16/24/32 bytes for AES-128/192/256)
        ciphertext: encrypted data (includes authentication tag)
        nonce: initialization vector (raw bytes)
        associated_data: additional authenticated data (may be empty)

    Returns:
        Decrypted plaintext bytes.

    Raises:
        DecryptionError: if decryption fails.
    """
    aesgcm = AESGCM(key)
    try:
        return aesgcm.decrypt(nonce, ciphertext, associated_data)
    except Exception as e:
        raise DecryptionError(f"AES-GCM decryption failed: {e}")


def aes_encrypt(key: bytes, plaintext: bytes, associated_data: bytes) -> tuple[bytes, bytes]:
    """Encrypt data using AES-GCM.

    Generates a 12-byte ASCII-safe (hex) nonce suitable for storing
    directly in JSON, matching the platform's behaviour.

    Args:
        key: symmetric key (16/24/32 bytes)
        plaintext: data to encrypt
        associated_data: additional authenticated data (may be empty)

    Returns:
        Tuple of (nonce, ciphertext). nonce is 12 ASCII bytes.
    """
    nonce = secrets.token_hex(6).encode("ascii")  # 12 hex chars → 12 bytes
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data)
    return nonce, ciphertext
