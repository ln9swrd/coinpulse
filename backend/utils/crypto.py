"""
Cryptography utilities for secure API key storage
Uses Fernet symmetric encryption
"""

import os
from cryptography.fernet import Fernet
from typing import Tuple


def get_encryption_key() -> bytes:
    """
    Get or generate encryption key for API key storage

    The key is stored in environment variable ENCRYPTION_KEY.
    If not found, a new key is generated (for development only).

    IMPORTANT: In production, ENCRYPTION_KEY must be set in .env file
    and kept secret. If the key is lost, all encrypted API keys
    cannot be decrypted!

    Returns:
        bytes: Fernet encryption key
    """
    from dotenv import load_dotenv
    load_dotenv()

    # Try to load from environment
    key_str = os.getenv('ENCRYPTION_KEY')

    if key_str:
        return key_str.encode()

    # Development fallback: generate new key
    # WARNING: This should never be used in production!
    print("[Crypto] WARNING: ENCRYPTION_KEY not found in .env")
    print("[Crypto] Generating new key for development...")
    print("[Crypto] IMPORTANT: Set ENCRYPTION_KEY in .env for production!")

    new_key = Fernet.generate_key()
    print(f"[Crypto] Generated key: {new_key.decode()}")
    print(f"[Crypto] Add to .env: ENCRYPTION_KEY={new_key.decode()}")

    return new_key


def encrypt_api_key(plain_key: str) -> str:
    """
    Encrypt API key using Fernet symmetric encryption

    Args:
        plain_key: Plain text API key

    Returns:
        Encrypted key as string (base64 encoded)
    """
    if not plain_key:
        raise ValueError("API key cannot be empty")

    encryption_key = get_encryption_key()
    fernet = Fernet(encryption_key)

    # Encrypt and return as string
    encrypted = fernet.encrypt(plain_key.encode())
    return encrypted.decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """
    Decrypt API key using Fernet symmetric encryption

    Args:
        encrypted_key: Encrypted key string (base64 encoded)

    Returns:
        Decrypted plain text API key

    Raises:
        ValueError: If decryption fails (wrong key or corrupted data)
    """
    if not encrypted_key:
        raise ValueError("Encrypted key cannot be empty")

    try:
        encryption_key = get_encryption_key()
        fernet = Fernet(encryption_key)

        # Decrypt and return as string
        decrypted = fernet.decrypt(encrypted_key.encode())
        return decrypted.decode()

    except Exception as e:
        raise ValueError(f"Failed to decrypt API key: {str(e)}")


def encrypt_api_credentials(access_key: str, secret_key: str) -> Tuple[str, str]:
    """
    Encrypt both access and secret keys

    Args:
        access_key: Plain text access key
        secret_key: Plain text secret key

    Returns:
        Tuple of (encrypted_access_key, encrypted_secret_key)
    """
    encrypted_access = encrypt_api_key(access_key)
    encrypted_secret = encrypt_api_key(secret_key)

    return encrypted_access, encrypted_secret


def decrypt_api_credentials(encrypted_access: str, encrypted_secret: str) -> Tuple[str, str]:
    """
    Decrypt both access and secret keys

    Args:
        encrypted_access: Encrypted access key
        encrypted_secret: Encrypted secret key

    Returns:
        Tuple of (plain_access_key, plain_secret_key)
    """
    plain_access = decrypt_api_key(encrypted_access)
    plain_secret = decrypt_api_key(encrypted_secret)

    return plain_access, plain_secret


def generate_new_encryption_key() -> str:
    """
    Generate a new Fernet encryption key

    Returns:
        New encryption key as string

    NOTE: This is for administrative use only!
    If you change the encryption key, all existing encrypted API keys
    will become unreadable!
    """
    key = Fernet.generate_key()
    return key.decode()


if __name__ == "__main__":
    # Test encryption/decryption
    print("Testing encryption utilities...")

    test_access = "test_access_key_12345"
    test_secret = "test_secret_key_67890"

    print(f"\nOriginal Access Key: {test_access}")
    print(f"Original Secret Key: {test_secret}")

    # Encrypt
    enc_access, enc_secret = encrypt_api_credentials(test_access, test_secret)
    print(f"\nEncrypted Access Key: {enc_access}")
    print(f"Encrypted Secret Key: {enc_secret}")

    # Decrypt
    dec_access, dec_secret = decrypt_api_credentials(enc_access, enc_secret)
    print(f"\nDecrypted Access Key: {dec_access}")
    print(f"Decrypted Secret Key: {dec_secret}")

    # Verify
    assert dec_access == test_access, "Access key mismatch!"
    assert dec_secret == test_secret, "Secret key mismatch!"

    print("\n✅ Encryption test passed!")
