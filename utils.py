import os
import json
import logging
import base64
from typing import Any, List, Optional, Union
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from apprise import Apprise
from colorama import init

init(autoreset=True)


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Setup logging with proper formatting and file rotation."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler("logs/shiftwatcher.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    # Prevent duplicate logs
    logging.getLogger().handlers[0].setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s")
    )

    return logging.getLogger("shiftwatcher")


logger = setup_logging()


def load_json(path: str, default: Optional[Any] = None) -> Union[List[Any], Any]:
    """Load JSON data from file with error handling."""
    if not os.path.exists(path):
        return default if default is not None else []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load {path}: {e}")
        return default if default is not None else []


def save_json(path: str, data: Any) -> None:
    """Save data to JSON file with error handling."""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save {path}: {e}")


def notify(apprise_url: str, title: str, body: str) -> bool:
    """Send notification via Apprise with error handling."""
    if not apprise_url:
        logger.warning("No Apprise URL configured, skipping notification")
        return False

    try:
        ap = Apprise()
        result = ap.add(apprise_url)
        if result:
            notify_result = ap.notify(title=title, body=body)
            return notify_result if notify_result is not None else False
        else:
            logger.error("Failed to add Apprise URL")
            return False
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        return False


def generate_encryption_key(
    password: str, salt: Optional[bytes] = None
) -> bytes:
    """Generate encryption key from password using PBKDF2."""
    if salt is None:
        salt = os.urandom(16)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key


def encrypt_data(data: str, key: bytes) -> str:
    """Encrypt data using Fernet symmetric encryption."""
    f = Fernet(key)
    encrypted = f.encrypt(data.encode())
    return base64.urlsafe_b64encode(encrypted).decode()


def decrypt_data(encrypted_data: str, key: bytes) -> str:
    """Decrypt data using Fernet symmetric encryption."""
    try:
        f = Fernet(key)
        decoded = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted = f.decrypt(decoded)
        return decrypted.decode()
    except InvalidToken:
        raise ValueError("Invalid encryption key or corrupted data")


def save_encrypted_json(path: str, data: Any, encryption_key: bytes) -> None:
    """Save data as encrypted JSON."""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        encrypted = encrypt_data(json_str, encryption_key)
        with open(path, "w", encoding="utf-8") as f:
            f.write(encrypted)
    except Exception as e:
        logger.error(f"Failed to save encrypted data to {path}: {e}")


def load_encrypted_json(
    path: str, encryption_key: bytes, default: Any = None
) -> Any:
    """Load and decrypt JSON data."""
    if not os.path.exists(path):
        return default if default is not None else []

    try:
        with open(path, "r", encoding="utf-8") as f:
            encrypted_data = f.read().strip()

        if not encrypted_data:
            return default if default is not None else []

        decrypted_str = decrypt_data(encrypted_data, encryption_key)
        return json.loads(decrypted_str)
    except Exception as e:
        logger.error(f"Failed to load encrypted data from {path}: {e}")
        return default if default is not None else []
