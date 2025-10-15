import time
import random
import argparse

# Global verbose flag
verbose_mode = False


# Check dependencies before importing other modules
def check_dependencies():
    """Check if all required modules are installed."""
    missing_modules: list[str] = []

    try:
        __import__("cryptography")
    except ImportError:
        missing_modules.append("cryptography")

    try:
        __import__("playwright")
    except ImportError:
        missing_modules.append("playwright")

    try:
        __import__("requests")
    except ImportError:
        missing_modules.append("requests")

    try:
        __import__("apprise")
    except ImportError:
        missing_modules.append("apprise")

    try:
        __import__("colorama")
    except ImportError:
        missing_modules.append("colorama")

    try:
        __import__("tqdm")
    except ImportError:
        missing_modules.append("tqdm")

    if missing_modules:
        print("❌ Missing required modules: {}".format(", ".join(missing_modules)))
        print("💡 Please run: pip install -r requirements.txt")
        print(
            "💡 Make sure you're in the virtual environment: "
            "source .venv/bin/activate"
        )
        return False

    return True


# Only import other modules if dependencies are available
if not check_dependencies():
    exit(1)

from colorama import Fore, Style, init
from tqdm import tqdm

from config import config
from session_manager import get_session, refresh_cookies, verify_login
from code_fetcher import fetch_new_codes
from code_redeemer import redeem_code
from rate_limiter import RateLimiter
from utils import load_json, save_json, notify, logger, setup_logging

init(autoreset=True)
rate_limiter = RateLimiter()


def main(verbose: bool = False):
    global verbose_mode
    verbose_mode = verbose

    # Reconfigure logging for verbose mode
    if verbose_mode:
        setup_logging("DEBUG")

    if verbose_mode:
        print(
            f"{Fore.BLUE}[{time.strftime('%H:%M:%S')}] Starting SHiFT Code "
            f"Watcher (verbose mode){Style.RESET_ALL}"
        )

    session = get_session()
    if verbose_mode:
        print(
            f"{Fore.BLUE}[{time.strftime('%H:%M:%S')}] Session loaded, "
            f"verifying login...{Style.RESET_ALL}"
        )

    if not verify_login(session):
        if verbose_mode:
            print(
                f"{Fore.YELLOW}[{time.strftime('%H:%M:%S')}] Session expired, "
                f"refreshing cookies...{Style.RESET_ALL}"
            )
        notify(
            config.APPRISE_URL, "ShiftWatcher", "Session expired — refreshing cookies."
        )
        refresh_cookies(verbose=verbose_mode)
        session = get_session()
        if not verify_login(session):
            if verbose_mode:
                print(
                    f"{Fore.RED}[{time.strftime('%H:%M:%S')}] Login failed "
                    f"after refresh{Style.RESET_ALL}"
                )
            notify(config.APPRISE_URL, "ShiftWatcher", "Login failed after refresh.")
            return

    all_codes = load_json(config.LOG_FILE, [])
    used_codes = load_json(config.USED_FILE, [])
    if verbose_mode:
        timestamp = time.strftime("%H:%M:%S")
        print(
            f"{Fore.BLUE}[{timestamp}] Loaded {len(all_codes)} "
            f"known codes, {len(used_codes)} used{Style.RESET_ALL}"
        )

    new_codes = fetch_new_codes()
    if verbose_mode:
        timestamp = time.strftime("%H:%M:%S")
        print(
            f"{Fore.BLUE}[{timestamp}] Fetched {len(new_codes)} "
            f"codes from sources{Style.RESET_ALL}"
        )

    fresh = [c for c in new_codes if c not in all_codes and c not in used_codes]
    if not fresh:
        print(
            f"{Fore.GREEN}[{time.strftime('%H:%M:%S')}] All current codes "
            f"checked. 🎉{Style.RESET_ALL}"
        )
        return

    if verbose_mode:
        print(
            f"{Fore.BLUE}[{time.strftime('%H:%M:%S')}] Found {len(fresh)} "
            f"new codes to check{Style.RESET_ALL}"
        )

    all_codes.extend(fresh)
    save_json(config.LOG_FILE, all_codes)
    notify(config.APPRISE_URL, "New SHiFT Codes Found", "New Code or Codes Found")
    print(f"{Fore.CYAN}=== Checking {len(fresh)} new codes ==={Style.RESET_ALL}")

    success_count = 0
    fail_count = 0
    check_counter = 0

    with tqdm(
        total=len(fresh), desc="Redeeming Codes", ncols=100, disable=verbose_mode
    ) as pbar:
        for code in fresh:
            result = redeem_code(session, code)
            check_counter += 1
            if result == "redeemed":
                status = f"{Fore.GREEN}GOOD{Style.RESET_ALL}"
                success_count += 1
                notify(config.APPRISE_URL, "Code Redeemed", f"✅ {code}")
                rate_limiter.reset()
                if verbose_mode:
                    timestamp = time.strftime("%H:%M:%S")
                    print(
                        f"{Fore.GREEN}[{timestamp}] Code redeemed "
                        f"successfully: {code}{Style.RESET_ALL}"
                    )
            elif result == "used":
                status = f"{Fore.RED}ALREADY REDEEMED{Style.RESET_ALL}"
                fail_count += 1
                used_codes.append(code)
                save_json(config.USED_FILE, used_codes)
                rate_limiter.increase()
                if verbose_mode:
                    timestamp = time.strftime("%H:%M:%S")
                    print(
                        f"{Fore.RED}[{timestamp}] Code already "
                        f"redeemed: {code}{Style.RESET_ALL}"
                    )
            elif result == "expired":
                status = f"{Fore.YELLOW}EXPIRED{Style.RESET_ALL}"
                fail_count += 1
                used_codes.append(code)
                save_json(config.USED_FILE, used_codes)
                rate_limiter.increase()
                if verbose_mode:
                    timestamp = time.strftime("%H:%M:%S")
                    print(
                        f"{Fore.YELLOW}[{timestamp}] Code expired: "
                        f"{code}{Style.RESET_ALL}"
                    )
            elif result == "invalid":
                status = f"{Fore.RED}INVALID{Style.RESET_ALL}"
                fail_count += 1
                used_codes.append(code)
                save_json(config.USED_FILE, used_codes)
                rate_limiter.increase()
                if verbose_mode:
                    timestamp = time.strftime("%H:%M:%S")
                    print(
                        f"{Fore.RED}[{timestamp}] Invalid code: "
                        f"{code}{Style.RESET_ALL}"
                    )
            else:
                status = f"{Fore.YELLOW}FAILED{Style.RESET_ALL}"
                fail_count += 1
                rate_limiter.increase()
                if verbose_mode:
                    timestamp = time.strftime("%H:%M:%S")
                    print(
                        f"{Fore.YELLOW}[{timestamp}] Failed to "
                        f"redeem code: {code}{Style.RESET_ALL}"
                    )

            if not verbose_mode:
                tqdm.write(f"{Fore.WHITE}{code} → Status: {status}")

            # Human like random delay 3-7 seconds
            delay = random.uniform(3, 7)
            if verbose_mode:
                timestamp = time.strftime("%H:%M:%S")
                print(
                    f"{Fore.BLUE}[{timestamp}] Waiting {delay:.1f}s "
                    f"before next code...{Style.RESET_ALL}"
                )
            time.sleep(delay)
            if not verbose_mode:
                pbar.update(1)

            # Periodic update every 5 codes
            if check_counter % 5 == 0 or check_counter == len(fresh):
                if verbose_mode:
                    print(
                        f"{Fore.BLUE}[{time.strftime('%H:%M:%S')}] Progress: "
                        f"{check_counter}/{len(fresh)} codes processed "
                        f"({success_count} good, {fail_count} failed)"
                        f"{Style.RESET_ALL}"
                    )
                else:
                    pbar.set_description_str(
                        f"Processed {check_counter}/{len(fresh)} | "
                        f"Success: {Fore.GREEN}{success_count}{Style.RESET_ALL} | "
                        f"Failed: {Fore.RED}{fail_count}{Style.RESET_ALL}"
                    )

    if verbose_mode:
        print(
            f"{Fore.CYAN}[{time.strftime('%H:%M:%S')}] All codes processed — "
            f"{success_count} redeemed, {fail_count} not available."
            f"{Style.RESET_ALL}"
        )
    else:
        print(
            f"\n{Fore.CYAN}All codes processed — {success_count} redeemed, "
            f"{fail_count} not available.{Style.RESET_ALL}"
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
    parser = argparse.ArgumentParser(description="SHiFT Code Watcher")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output with detailed logging",
    )
    parser.add_argument(
        "--reddit",
        action="store_true",
        help="Monitor Reddit RSS feed for SHiFT codes instead of configured sources",
    )
    args = parser.parse_args()

    if args.reddit:
        # Import reddit parser only when needed
        from reddit_parser import monitor_reddit_for_codes

        # Get authenticated session for Reddit monitoring
        session = get_session()
        if not verify_login(session):
            print(
                f"{Fore.YELLOW}Session expired, refreshing cookies...{Style.RESET_ALL}"
            )
            refresh_cookies(verbose=args.verbose)
            session = get_session()
            if not verify_login(session):
                print(f"{Fore.RED}Login failed after refresh{Style.RESET_ALL}")
                exit(1)

        # Start Reddit monitoring (runs indefinitely)
        monitor_reddit_for_codes(session, rate_limiter, verbose=args.verbose)
    else:
        # Regular monitoring mode
        while True:
            try:
                main(verbose=args.verbose)
            except Exception as e:
                logger.exception(f"Main loop error: {e}")
            time.sleep(config.SCAN_INTERVAL)
