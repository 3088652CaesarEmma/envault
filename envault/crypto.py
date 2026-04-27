"""Cryptographic utilities for envault.

Handles encryption and decryption of .env file contents
using AES-GCM with a key derived from the master passphrase.
"""

import os
import base64
import hashlib

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32
ITERATIONS = 390_000


def derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derive a 256-bit encryption key from a passphrase and salt."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=ITERATIONS,
    )
    return kdf.derive(passphrase.encode("utf-8"))


def encrypt(plaintext: str, passphrase: str) -> str:
    """Encrypt plaintext using AES-GCM.

    Returns a base64-encoded string containing:
        salt (16 bytes) + nonce (12 bytes) + ciphertext
    """
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = derive_key(passphrase, salt)

    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)

    payload = salt + nonce + ciphertext
    return base64.b64encode(payload).decode("utf-8")


def decrypt(encoded_payload: str, passphrase: str) -> str:
    """Decrypt a base64-encoded payload produced by :func:`encrypt`.

    Raises:
        ValueError: If decryption fails (wrong passphrase or corrupted data).
    """
    try:
        payload = base64.b64decode(encoded_payload.encode("utf-8"))
    except Exception as exc:
        raise ValueError("Invalid payload encoding.") from exc

    if len(payload) < SALT_SIZE + NONCE_SIZE:
        raise ValueError("Payload is too short to be valid.")

    salt = payload[:SALT_SIZE]
    nonce = payload[SALT_SIZE:SALT_SIZE + NONCE_SIZE]
    ciphertext = payload[SALT_SIZE + NONCE_SIZE:]

    key = derive_key(passphrase, salt)
    aesgcm = AESGCM(key)

    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    except Exception as exc:
        raise ValueError(
            "Decryption failed. Wrong passphrase or corrupted data."
        ) from exc

    return plaintext.decode("utf-8")
