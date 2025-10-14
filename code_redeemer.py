from typing import Optional
from utils import logger
from config import config
import requests

def redeem_code(session: requests.Session, code: str) -> str:
    data = {"code": code}
    try:
        r = session.post(config.REDEEM_URL, headers=config.HEADERS, data=data, timeout=config.REQUEST_TIMEOUT)
        text = r.text.lower()
        if "used" in text:
            return "used"
        elif "invalid" in text:
            return "invalid"
        elif "success" in text or "redeemed" in text:
            return "redeemed"
        else:
            return "unknown"
    except Exception as e:
        logger.error(f"Error redeeeming code {code}: {e}")
        return "failed"
