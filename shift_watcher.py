import time
import random
from colorama import Fore, Style, init
from tqdm import tqdm

from config import config
from session_manager import get_session, refresh_cookies, verify_login
from code_fetcher import fetch_new_codes
from code_redeemer import redeem_code
from rate_limiter import RateLimiter
from utils import load_json, save_json, notify, logger

init(autoreset=True)
rate_limiter = RateLimiter()


def main():
    session = get_session()
    if not verify_login(session):
        notify(
            config.APPRISE_URL, "ShiftWatcher", "Session expired — refreshing cookies."
        )
        refresh_cookies()
        session = get_session()
        if not verify_login(session):
            notify(config.APPRISE_URL, "ShiftWatcher", "Login failed after refresh.")
            return

    all_codes = load_json(config.LOG_FILE, [])
    used_codes = load_json(config.USED_FILE, [])
    new_codes = fetch_new_codes()
    fresh = [c for c in new_codes if c not in all_codes and c not in used_codes]
    if not fresh:
        print(f"{Fore.YELLOW}[{time.strftime('%H:%M:%S')}] No new codes found.")
        return

    all_codes.extend(fresh)
    save_json(config.LOG_FILE, all_codes)
    notify(config.APPRISE_URL, "New SHiFT Codes Found", "New Code or Codes Found")
    print(f"{Fore.CYAN}=== Checking {len(fresh)} new codes ==={Style.RESET_ALL}")

    success_count = 0
    fail_count = 0
    check_counter = 0

    with tqdm(total=len(fresh), desc="Redeeming Codes", ncols=100) as pbar:
        for code in fresh:
            result = redeem_code(session, code)
            check_counter += 1
            if result == "redeemed":
                status = f"{Fore.GREEN}GOOD{Style.RESET_ALL}"
                success_count += 1
                notify(config.APPRISE_URL, "Code Redeemed", f"✅ {code}")
                rate_limiter.reset()
            elif result in ("used", "invalid"):
                status = f"{Fore.RED}{result.upper()}{Style.RESET_ALL}"
                fail_count += 1
                used_codes.append(code)
                save_json(config.USED_FILE, used_codes)
                rate_limiter.increase()
            else:
                status = f"{Fore.YELLOW}FAILED{Style.RESET_ALL}"
                fail_count += 1
                rate_limiter.increase()

            tqdm.write(f"{Fore.WHITE}{code} → Status: {status}")

            # Human like random delay 3-7 seconds
            time.sleep(random.uniform(3, 7))
            pbar.update(1)

            # Periodic update every 5 codes
            if check_counter % 5 == 0 or check_counter == len(fresh):
                pbar.set_description_str(
                    f"Processed {check_counter}/{len(fresh)} | "
                    f"Success: {Fore.GREEN}{success_count}{Style.RESET_ALL} | "
                    f"Failed: {Fore.RED}{fail_count}{Style.RESET_ALL}"
                )

    print(
        f"\n{Fore.CYAN}All codes processed — {success_count} good, "
        f"{fail_count} used/invalid.{Style.RESET_ALL}"
    )

    # Status message: waiting for next check
    hours = config.SCAN_INTERVAL // 3600
    minutes = (config.SCAN_INTERVAL % 3600) // 60
    time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
    print(
        f"{Fore.YELLOW}[{time.strftime('%H:%M:%S')}] Waiting for new codes... "
        f"Next check in {time_str}{Style.RESET_ALL}"
    )


if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            logger.exception(f"Main loop error: {e}")
        time.sleep(config.SCAN_INTERVAL)
