import os
from dataclasses import dataclass, field
from typing import List
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    COOKIES_FILE: str = "cookies.json"
    LOG_FILE: str = "codes_log.json"
    USED_FILE: str = "codes_used.json"
    REDEEM_URL: str = "https://shift.gearboxsoftware.com/rewards"
    LOGIN_URL: str = "https://shift.gearboxsoftware.com/home"
    SCAN_INTERVAL: int = 3600
    PLAYWRIGHT_TIMEOUT: int = 30000
    REQUEST_TIMEOUT: int = 15

    SOURCES: List[str] = field(
        default_factory=lambda: [
            "https://www.ign.com/wikis/borderlands-4/Borderlands_4_SHiFT_Codes",
            "https://x.com/GearboxOfficial",
            "https://twitter.com/DuvalMagic",
            "https://www.facebook.com/GearboxSoftware",
            "https://game8.co/games/Borderlands-4/archives/548406",
        ]
    )

    HEADERS: dict = field(
        default_factory=lambda: {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
    )

    # Security settings
    ENCRYPT_COOKIES: bool = (
        os.getenv("ENCRYPT_COOKIES", "true").lower() == "true"
    )
    SECRET_KEY: str = os.getenv("SHIFT_SECRET_KEY", "")

    APPRISE_URL: str = os.getenv("APPRISE_URL", "")


config = Config()
# Only require APPRISE_URL if we're actually running the main script
# Allow imports for testing/CI without requiring environment variables
if __name__ == "__main__" and not config.APPRISE_URL:
    raise ValueError("Missing APPRISE_URL environment variable")
