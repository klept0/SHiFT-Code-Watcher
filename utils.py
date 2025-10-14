import os
import json
import logging
from apprise import Apprise
from colorama import init

init(autoreset=True)


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler("shiftwatcher.log"),
            logging.StreamHandler()
        ],
    )
    return logging.getLogger(__name__)


logger = setup_logging()


def load_json(path: str, default=None):
    if not os.path.exists(path):
        return default if default is not None else []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load {path}: {e}")
        return default if default is not None else []


def save_json(path: str, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save {path}: {e}")


def notify(apprise_url: str, title: str, body: str):
    ap = Apprise()
    ap.add(apprise_url)
    ap.notify(title=title, body=body)
