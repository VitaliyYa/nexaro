import base64
import hashlib

from cryptography.fernet import Fernet

from src.config import get_settings


def _get_fernet_instance(key_str: str | None = None) -> Fernet:
    settings = get_settings()
    raw_key = key_str or settings.PIN_ENCRYPTION_KEY
    # If the key is not already a valid 32-byte url-safe base64 string, derive a valid 32-byte key
    try:
        decoded = base64.urlsafe_b64decode(raw_key.encode("utf-8"))
        if len(decoded) == 32:
            return Fernet(raw_key.encode("utf-8"))
    except Exception:
        pass

    # Deterministically derive 32-byte url-safe base64 key using sha256
    derived_32 = hashlib.sha256(raw_key.encode("utf-8")).digest()
    b64_key = base64.urlsafe_b64encode(derived_32)
    return Fernet(b64_key)


def encrypt_pin(plain_pin: str, key_str: str | None = None) -> str:
    """Encrypts plain text PIN code using symmetric encryption (Fernet/AES-CBC/HMAC)."""
    fernet = _get_fernet_instance(key_str)
    encrypted_bytes = fernet.encrypt(plain_pin.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")


def decrypt_pin(encrypted_pin: str, key_str: str | None = None) -> str:
    """Decrypts encrypted PIN code."""
    fernet = _get_fernet_instance(key_str)
    decrypted_bytes = fernet.decrypt(encrypted_pin.encode("utf-8"))
    return decrypted_bytes.decode("utf-8")
