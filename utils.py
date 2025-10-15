import os
import json
import logging
from typing import Any, List, Optional, Union
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
            logging.StreamHandler()
        ],
    )

    # Prevent duplicate logs
    logging.getLogger().handlers[0].setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s")
    )

    return logging.getLogger("shiftwatcher")


logger = setup_logging()


def load_json(
    path: str, default: Optional[Any] = None
) -> Union[List[Any], Any]:
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
