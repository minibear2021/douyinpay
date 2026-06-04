import base64
import secrets
import string
import time

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.exceptions import InvalidSignature
from cryptography import x509

from douyinpay._errors import SignatureError

_SIGN_TYPES = ("RSA", "SM2")


class SignResult:
    """Result of a request signing operation.

    Fields:
        mchid: merchant ID
        serial_no: certificate serial number
        nonce_str: 32-character alphanumeric random string
        timestamp: Unix timestamp in seconds
        signature: Base64-encoded RSA signature
        sign_type: signature type (default "RSA")
    """

    def __init__(
        self,
        mchid: str,
        serial_no: str,
        nonce_str: str,
        timestamp: int,
        signature: str,
        sign_type: str = "RSA",
    ):
        self.mchid = mchid
        self.serial_no = serial_no
        self.nonce_str = nonce_str
        self.timestamp = timestamp
        self.signature = signature
        self.sign_type = sign_type

    def to_header(self) -> str:
        """Return the Authorization header string."""
        scheme = f"DouyinPay-{self.sign_type}"
        return (
            f'{scheme} mchid="{self.mchid}",'
            f'nonce_str="{self.nonce_str}",'
            f'timestamp="{self.timestamp}",'
            f'serial_no="{self.serial_no}",'
            f'signature="{self.signature}"'
        )


def _build_sign_message(
    method: str,
    path: str,
    timestamp: int,
    nonce_str: str,
    body: str,
) -> str:
    """Build the 5-line signing message for request signing.

    Each line is terminated with ``\\n``, including the last line.
    """
    return f"{method}\n{path}\n{timestamp}\n{nonce_str}\n{body}\n"


def _load_public_key(pem: str):
    """Load an RSA public key from a PEM string.

    Accepts both ``-----BEGIN CERTIFICATE-----`` and
    ``-----BEGIN PUBLIC KEY-----`` formats.
    """
    data = pem.encode("utf-8")
    if "BEGIN CERTIFICATE" in pem:
        cert = x509.load_pem_x509_certificate(data)
        return cert.public_key()
    return serialization.load_pem_public_key(data)


def sign_request(
    method: str,
    path: str,
    body: str,
    mchid: str,
    serial_no: str,
    private_key_pem: str,
    sign_type: str = "RSA",
) -> SignResult:
    """Sign an API request using the merchant's RSA private key.

    Args:
        method: HTTP method (e.g. "POST", "GET")
        path: URL path (e.g. "/v1/orders")
        body: request body as a string (empty string for GET)
        mchid: merchant ID
        serial_no: certificate serial number
        private_key_pem: PEM-encoded RSA private key (PKCS#8)
        sign_type: signature type, defaults to "RSA"

    Returns:
        SignResult with all fields populated and the Base64-encoded signature
    """
    nonce_str = "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(32)
    )
    timestamp = int(time.time())

    message = _build_sign_message(method, path, timestamp, nonce_str, body)

    if sign_type == "SM2":
        from gmssl.sm2 import CryptSM2

        k_hex = secrets.token_hex(32)
        sm2 = CryptSM2(private_key=private_key_pem, public_key="")
        raw_signature = sm2.sign(message.encode("utf-8"), k_hex)
        signature_b64 = base64.b64encode(raw_signature.encode("utf-8")).decode("utf-8")
    else:
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode("utf-8"),
            password=None,
        )
        raw_signature = private_key.sign(
            message.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        signature_b64 = base64.b64encode(raw_signature).decode("utf-8")

    return SignResult(
        mchid=mchid,
        serial_no=serial_no,
        nonce_str=nonce_str,
        timestamp=timestamp,
        signature=signature_b64,
        sign_type=sign_type,
    )


def build_verify_message(timestamp: int, nonce: str, body: str) -> str:
    """Build the 3-line verification message for response/callback verification.

    Each line is terminated with ``\\n``, including the last line.
    """
    return f"{timestamp}\n{nonce}\n{body}\n"


def verify_signature(
    message: str,
    signature_b64: str,
    public_key_pem: str,
    sign_type: str = "RSA",
) -> bool:
    """Verify a signature against a message using a public key.

    Args:
        message: the pre-built verification message
        signature_b64: Base64-encoded signature to verify
        public_key_pem: PEM-encoded public key
        sign_type: "RSA" or "SM2"

    Returns:
        True if the signature is valid

    Raises:
        SignatureError: if the signature is invalid or the Base64 data
            cannot be decoded
    """
    try:
        raw_signature = base64.b64decode(signature_b64)
    except Exception:
        raise SignatureError("Failed to decode base64 signature")

    if sign_type == "SM2":
        from gmssl.sm2 import CryptSM2

        sig_hex = base64.b64decode(signature_b64).decode("utf-8")
        sm2 = CryptSM2(private_key="", public_key=public_key_pem)
        try:
            if not sm2.verify(sig_hex, message.encode("utf-8")):
                raise SignatureError("SM2 signature verification failed")
        except (ValueError, Exception):
            raise SignatureError("SM2 signature verification failed")
    else:
        public_key = _load_public_key(public_key_pem)
        try:
            public_key.verify(
                raw_signature,
                message.encode("utf-8"),
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
        except InvalidSignature:
            raise SignatureError("Signature verification failed")

    return True
