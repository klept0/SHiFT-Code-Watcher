import pytest
import tempfile
import os
from utils import (
    generate_encryption_key,
    encrypt_data,
    decrypt_data,
    save_encrypted_json,
    load_encrypted_json,
)


def test_encryption_decryption():
    """Test basic encryption and decryption functionality."""
    test_data = "Hello, World!"
    password = "test_password_123"

    # Generate key
    key = generate_encryption_key(password)

    # Encrypt data
    encrypted = encrypt_data(test_data, key)
    assert encrypted != test_data

    # Decrypt data
    decrypted = decrypt_data(encrypted, key)
    assert decrypted == test_data


def test_encryption_wrong_key():
    """Test that wrong key fails decryption."""
    test_data = "Secret data"
    password1 = "correct_password"
    password2 = "wrong_password"

    key1 = generate_encryption_key(password1)
    key2 = generate_encryption_key(password2)

    encrypted = encrypt_data(test_data, key1)

    # Should fail with wrong key
    with pytest.raises(ValueError):
        decrypt_data(encrypted, key2)


def test_encrypted_json_storage():
    """Test saving and loading encrypted JSON data."""
    test_data = {"cookies": [{"name": "session", "value": "abc123"}]}
    password = "secure_password"

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        temp_file = f.name

    try:
        key = generate_encryption_key(password)

        # Save encrypted data
        save_encrypted_json(temp_file, test_data, key)

        # Load encrypted data
        loaded_data = load_encrypted_json(temp_file, key)

        assert loaded_data == test_data

    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def test_dummy():
    """Placeholder test that was here before."""
    assert True
