import pytest
from cryptography.fernet import InvalidToken

from src.services.pin_crypto import decrypt_pin, encrypt_pin


def test_pin_encryption_and_decryption():
    raw_pin = "481516"
    encrypted = encrypt_pin(raw_pin)

    assert encrypted != raw_pin
    assert len(encrypted) > 20

    decrypted = decrypt_pin(encrypted)
    assert decrypted == raw_pin


def test_pin_encryption_with_custom_key():
    custom_key = "custom_secret_key_for_smartrent_test"
    pin = "998877"
    enc = encrypt_pin(pin, key_str=custom_key)
    dec = decrypt_pin(enc, key_str=custom_key)
    assert dec == pin


def test_pin_decryption_with_wrong_key_fails():
    pin = "123456"
    enc = encrypt_pin(pin, key_str="key_alpha_123")
    with pytest.raises(InvalidToken):
        decrypt_pin(enc, key_str="key_beta_456")
