from playwright.sync_api import sync_playwright
import requests
import os
from utils import logger, save_json, load_json
from config import config
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def get_session_with_retry() -> requests.Session:
    session = requests.Session()
    retry = Retry(total=5, backoff_factor=1,
                  status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(config.HEADERS)
    return session


def refresh_cookies():
    logger.info("Launching Playwright for manual login...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(config.LOGIN_URL)
        page.wait_for_timeout(config.PLAYWRIGHT_TIMEOUT)
        cookies = context.cookies()
        save_json(config.COOKIES_FILE, cookies)
        browser.close()
    logger.info("Cookies refreshed.")


def get_session() -> requests.Session:
    if not os.path.exists(config.COOKIES_FILE):
        refresh_cookies()
    cookies = load_json(config.COOKIES_FILE)
    session = get_session_with_retry()
    for c in cookies:
        session.cookies.set(
            c["name"], c["value"],
            domain=c.get("domain", "shift.gearboxsoftware.com")
        )
    return session


def verify_login(session: requests.Session) -> bool:
    try:
        resp = session.get(config.REDEEM_URL, timeout=10)
        resp.raise_for_status()
        return "Sign In" not in resp.text
    except Exception as e:
        logger.warning(f"Login verification failed: {e}")
        return False
