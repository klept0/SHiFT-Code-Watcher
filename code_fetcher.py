import requests
from utils import logger
from config import config
import re
from typing import Set, List


def extract_codes_from_text(text: str) -> Set[str]:
    pattern = re.compile(
        r"[A-Z0-9]{5}-[A-Z0-9]{5}-[A-Z0-9]{5}-[A-Z0-9]{5}-[A-Z0-9]{5}"
    )
    return set(re.findall(pattern, text))


def fetch_new_codes() -> List[str]:
    codes = set()
    for url in config.SOURCES:
        try:
            r = requests.get(url, headers=config.HEADERS,
                             timeout=config.REQUEST_TIMEOUT)
            r.raise_for_status()
            codes |= extract_codes_from_text(r.text)
        except Exception as e:
            logger.warning(f"Failed fetching from {url}: {e}")
    return list(codes)
