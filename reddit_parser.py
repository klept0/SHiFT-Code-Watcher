import requests
import xml.etree.ElementTree as ET
from typing import List, Set
import re
import time
import random
from utils import logger
from config import config


def extract_codes_from_text(text: str) -> Set[str]:
    """Extract SHiFT codes from text using regex pattern."""
    pattern = re.compile(r"[A-Z0-9]{5}-[A-Z0-9]{5}-[A-Z0-9]{5}-[A-Z0-9]{5}-[A-Z0-9]{5}")
    return set(re.findall(pattern, text))


def parse_reddit_rss() -> List[str]:
    """
    Parse Reddit RSS feed for Borderlands and extract SHiFT codes.

    Returns:
        List of unique SHiFT codes found in recent Reddit posts
    """
    reddit_rss_url = "https://www.reddit.com/r/Borderlands/new/.rss?limit=5"
    codes = set()

    try:
        logger.info("Fetching Reddit RSS feed...")
        response = requests.get(
            reddit_rss_url,
            headers={
                "User-Agent": "SHiFT-Code-Watcher/1.0 (https://github.com/klept0/SHiFT-Code-Watcher)"
            },
            timeout=config.REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        # Parse XML
        root = ET.fromstring(response.content)

        # Find all entry/item elements (RSS/Atom format)
        entries = root.findall(".//{http://www.w3.org/2005/Atom}entry") or root.findall(
            ".//item"
        )

        logger.info(f"Found {len(entries)} Reddit posts to check")

        for entry in entries[:20]:  # Check last 20 posts to avoid rate limiting
            try:
                # Get post content (try different XML structures)
                content = ""

                # Try Atom format first
                content_elem = entry.find(".//{http://www.w3.org/2005/Atom}content")
                if content_elem is not None and content_elem.text:
                    content = content_elem.text
                else:
                    # Try RSS format
                    description = entry.find("description")
                    if description is not None and description.text:
                        content = description.text

                    # Also check title
                    title = entry.find(
                        ".//{http://www.w3.org/2005/Atom}title"
                    ) or entry.find("title")
                    if title is not None and title.text:
                        content += " " + title.text

                if content:
                    post_codes = extract_codes_from_text(content)
                    if post_codes:
                        logger.info(f"Found {len(post_codes)} code(s) in Reddit post")
                        codes.update(post_codes)

            except Exception as e:
                logger.warning(f"Error parsing Reddit post: {e}")
                continue

        logger.info(f"Total unique codes found in Reddit: {len(codes)}")
        return list(codes)

    except requests.RequestException as e:
        logger.error(f"Failed to fetch Reddit RSS: {e}")
        return []
    except ET.ParseError as e:
        logger.error(f"Failed to parse Reddit RSS XML: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error parsing Reddit RSS: {e}")
        return []


def monitor_reddit_for_codes(session, rate_limiter, verbose: bool = False) -> None:
    """
    Monitor Reddit RSS feed for new SHiFT codes and redeem them.

    Args:
        session: Authenticated requests session
        rate_limiter: Rate limiter instance
        verbose: Whether to show verbose output
    """
    from code_redeemer import redeem_code
    from utils import load_json, save_json, notify
    from colorama import Fore, Style

    logger.info("Starting Reddit monitoring mode...")

    # Load existing codes
    all_codes = load_json(config.LOG_FILE, [])
    used_codes = load_json(config.USED_FILE, [])

    if verbose:
        print(
            f"{Fore.BLUE}[{time.strftime('%H:%M:%S')}] Reddit monitoring started{Style.RESET_ALL}"
        )
        print(
            f"{Fore.BLUE}[{time.strftime('%H:%M:%S')}] Checking Reddit every 3-5 minutes{Style.RESET_ALL}"
        )

    while True:
        try:
            # Check Reddit RSS
            reddit_codes = parse_reddit_rss()

            if reddit_codes:
                # Filter out already known codes
                new_codes = [
                    code
                    for code in reddit_codes
                    if code not in all_codes and code not in used_codes
                ]

                if new_codes:
                    if verbose:
                        print(
                            f"{Fore.GREEN}[{time.strftime('%H:%M:%S')}] Found {len(new_codes)} new code(s) from Reddit!{Style.RESET_ALL}"
                        )

                    # Add to known codes
                    all_codes.extend(new_codes)
                    save_json(config.LOG_FILE, all_codes)

                    # Notify about new codes
                    notify(
                        config.APPRISE_URL,
                        "New SHiFT Codes from Reddit",
                        f"Found {len(new_codes)} new code(s)",
                    )

                    # Redeem the codes
                    success_count = 0
                    for code in new_codes:
                        result = redeem_code(session, code)

                        if result == "redeemed":
                            success_count += 1
                            used_codes.append(code)
                            save_json(config.USED_FILE, used_codes)
                            notify(
                                config.APPRISE_URL,
                                "Code Redeemed from Reddit",
                                f"✅ {code}",
                            )
                            rate_limiter.reset()

                            if verbose:
                                print(
                                    f"{Fore.GREEN}[{time.strftime('%H:%M:%S')}] ✅ Redeemed: {code}{Style.RESET_ALL}"
                                )
                        else:
                            if verbose:
                                status_color = {
                                    "used": Fore.RED,
                                    "expired": Fore.YELLOW,
                                    "invalid": Fore.RED,
                                }.get(result, Fore.YELLOW)

                                print(
                                    f"{status_color}[{time.strftime('%H:%M:%S')}] {result.upper()}: {code}{Style.RESET_ALL}"
                                )

                        # Rate limiting
                        delay = random.uniform(3, 7)
                        time.sleep(delay)

                    if verbose and success_count > 0:
                        print(
                            f"{Fore.CYAN}[{time.strftime('%H:%M:%S')}] Successfully redeemed {success_count}/{len(new_codes)} codes from Reddit{Style.RESET_ALL}"
                        )
                else:
                    if verbose:
                        print(
                            f"{Fore.BLUE}[{time.strftime('%H:%M:%S')}] No new codes found in Reddit{Style.RESET_ALL}"
                        )
            else:
                if verbose:
                    print(
                        f"{Fore.BLUE}[{time.strftime('%H:%M:%S')}] No codes found in Reddit RSS{Style.RESET_ALL}"
                    )

        except Exception as e:
            logger.error(f"Error in Reddit monitoring: {e}")
            if verbose:
                print(
                    f"{Fore.RED}[{time.strftime('%H:%M:%S')}] Error monitoring Reddit: {e}{Style.RESET_ALL}"
                )

        # Wait 3-5 minutes before next check
        wait_time = random.randint(180, 300)  # 3-5 minutes in seconds
        if verbose:
            print(
                f"{Fore.BLUE}[{time.strftime('%H:%M:%S')}] Waiting {wait_time//60} minutes before next Reddit check...{Style.RESET_ALL}"
            )

        time.sleep(wait_time)
