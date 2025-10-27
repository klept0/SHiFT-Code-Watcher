import json
import re
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from typing import Dict, List, Optional, Tuple, cast
from urllib.parse import urljoin

import requests

from config import config
from utils import logger


@dataclass
class _RedeemForm:
    attrs: Dict[str, str]
    hidden: Dict[str, str]
    commits: List[str]


class _RedeemFormParser(HTMLParser):
    """Parse redemption forms to capture hidden fields and platform buttons."""

    def __init__(self) -> None:
        super().__init__()
        self.forms: List[_RedeemForm] = []
        self._current: Optional[_RedeemForm] = None

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        attrs_dict = {key: value or "" for key, value in attrs}
        if tag == "form":
            self._current = _RedeemForm(attrs=attrs_dict, hidden={}, commits=[])
            return

        if not self._current:
            return

        if tag == "input":
            name = attrs_dict.get("name")
            value = unescape(attrs_dict.get("value") or "")
            input_type = (attrs_dict.get("type") or "").lower()
            if input_type == "hidden" and name:
                self._current.hidden[name] = value
            elif name == "commit" and value:
                self._current.commits.append(value)
        elif tag == "button" and attrs_dict.get("name") == "commit":
            value = unescape(attrs_dict.get("value") or "")
            if value:
                self._current.commits.append(value)

    def handle_endtag(self, tag: str) -> None:
        if tag == "form" and self._current:
            if self._current.commits:
                self.forms.append(self._current)
            self._current = None


def _select_platform_submission(
    html: str, code: str
) -> Optional[Tuple[str, Dict[str, str], str]]:
    """Return action URL, payload, and chosen commit label if needed."""

    parser = _RedeemFormParser()
    parser.feed(html)
    parser.close()

    if not parser.forms:
        return None

    logger.debug(
        "Found %d redemption forms with commit labels: %s",
        len(parser.forms),
        [form.commits for form in parser.forms],
    )

    preferred_raw = config.PREFERRED_PLATFORM.strip().lower()
    chosen_form = parser.forms[0]
    chosen_commit = chosen_form.commits[0]

    def _normalize(text: str) -> str:
        return re.sub(r"[^a-z0-9]", "", text.lower())

    def _candidate_tokens(form: _RedeemForm) -> List[str]:
        tokens: List[str] = []
        tokens.extend(form.commits)
        tokens.extend(form.hidden.values())
        tokens.extend(form.attrs.values())
        return [_normalize(token) for token in tokens if token]

    platform_aliases: Dict[str, List[str]] = {
        "xbox": ["xbox", "xboxlive", "xboxone", "xboxseries"],
        "playstation": [
            "playstation",
            "playstationnetwork",
            "ps",
            "psn",
            "ps5",
            "ps4",
        ],
        "psn": ["psn", "playstation", "playstationnetwork"],
        "steam": ["steam"],
        "epic": ["epic", "epicgames"],
        "pc": ["pc", "steam", "epic", "gearbox"],
        "switch": ["switch", "nintendo", "nintendoswitch"],
        "nintendo": ["nintendo", "nintendoswitch", "switch"],
        "stadia": ["stadia"],
    }

    preferred_tokens: List[str] = []
    if preferred_raw:
        normalized_pref = _normalize(preferred_raw)
        preferred_tokens = platform_aliases.get(normalized_pref, [])
        if normalized_pref not in preferred_tokens:
            preferred_tokens.append(normalized_pref)

    if preferred_tokens:
        for form in parser.forms:
            candidates = _candidate_tokens(form)
            logger.debug(
                "Evaluating platform form with tokens: %s",
                candidates,
            )
            matches_preference = any(
                pref in candidate
                for candidate in candidates
                for pref in preferred_tokens
            )
            if matches_preference:
                chosen_form = form
                chosen_commit = form.commits[0]
                for commit_value in form.commits:
                    if any(
                        pref in _normalize(commit_value) for pref in preferred_tokens
                    ):
                        chosen_commit = commit_value
                        break
                logger.info(
                    "Selected platform form via preference tokens: %s",
                    chosen_commit,
                )
                break
        else:
            logger.warning(
                (
                    "Preferred platform '%s' not matched; "
                    "using first available option '%s'"
                ),
                preferred_raw,
                chosen_commit,
            )

    hidden_inputs = {key: value for key, value in chosen_form.hidden.items()}
    if "shift_code" not in hidden_inputs:
        hidden_inputs["shift_code"] = code
    if "code" not in hidden_inputs:
        hidden_inputs["code"] = code
    hidden_inputs["commit"] = chosen_commit

    action = chosen_form.attrs.get("action") or config.REDEEM_URL
    action_url = urljoin(config.REDEEM_URL, action)

    return action_url, hidden_inputs, chosen_commit


def _extract_csrf_token(html: str) -> Optional[str]:
    match = re.search(
        r'name="csrf-token"\s+content="([^"]+)"',
        html,
        flags=re.IGNORECASE,
    )
    if match:
        return match.group(1)
    return None


def _fetch_csrf_token(session: requests.Session) -> str:
    response = session.get(
        config.REDEEM_URL,
        headers=config.HEADERS,
        timeout=config.REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    token = _extract_csrf_token(response.text)
    if not token:
        raise ValueError("SHiFT CSRF token not found on rewards page")
    return token


def _response_to_html(response: requests.Response) -> str:
    content_type = response.headers.get("content-type", "").lower()
    if "application/json" in content_type:
        try:
            payload = response.json()
        except json.JSONDecodeError:
            return response.text
        if isinstance(payload, dict):
            typed_payload = cast(Dict[str, object], payload)
            for key in ("html", "body", "content"):
                value_obj = typed_payload.get(key)
                if isinstance(value_obj, str):
                    return value_obj
        return response.text
    return response.text


def redeem_code(session: requests.Session, code: str) -> str:
    try:
        csrf_token = _fetch_csrf_token(session)
        headers = dict(config.HEADERS)
        headers.setdefault("Referer", config.REDEEM_URL)
        headers["X-CSRF-Token"] = csrf_token
        headers["X-Requested-With"] = "XMLHttpRequest"
        headers.setdefault(
            "Accept",
            "application/json, text/javascript, */*; q=0.01",
        )
        headers.setdefault(
            "Content-Type",
            "application/x-www-form-urlencoded; charset=UTF-8",
        )
        headers.setdefault("Origin", "https://shift.gearboxsoftware.com")

        lookup_payload = {
            "authenticity_token": csrf_token,
            "shift_code": code,
            "utf8": "✓",
            "commit": "Check",
        }

        logger.debug("Submitting code check via POST to %s", config.ENTITLEMENT_URL)

        r = session.post(
            config.ENTITLEMENT_URL,
            headers=headers,
            data=lookup_payload,
            timeout=config.REQUEST_TIMEOUT,
        )
        logger.debug(
            "Initial platform lookup status=%s len=%s url=%s",
            r.status_code,
            len(r.text),
            r.url,
        )
        if r.status_code == 404 and not config.ENTITLEMENT_URL.endswith(".json"):
            alt_url = f"{config.ENTITLEMENT_URL}.json"
            logger.info("Lookup returned 404; retrying with %s", alt_url)
            r = session.post(
                alt_url,
                headers=headers,
                data=lookup_payload,
                timeout=config.REQUEST_TIMEOUT,
            )
            logger.debug(
                "Retry lookup status=%s len=%s url=%s",
                r.status_code,
                len(r.text),
                r.url,
            )

        if r.status_code >= 400:
            logger.warning(
                "Initial entitlement lookup failed (%s): %s",
                r.status_code,
                r.text[:500],
            )
            r.raise_for_status()

        html = _response_to_html(r)
        platform_submission = _select_platform_submission(html, code)
        if platform_submission:
            action_url, payload, commit_label = platform_submission
            payload.setdefault("authenticity_token", csrf_token)
            payload.setdefault("utf8", "✓")
            payload.setdefault("shift_code", code)
            logger.info(
                "Multiple platforms found; selecting option: %s",
                commit_label,
            )
            follow_headers = dict(headers)
            follow_headers["Referer"] = config.ENTITLEMENT_URL
            r = session.post(
                action_url,
                headers=follow_headers,
                data=payload,
                timeout=config.REQUEST_TIMEOUT,
            )
            logger.debug(
                "Platform redemption status=%s len=%s",
                r.status_code,
                len(r.text),
            )
            if r.status_code >= 400:
                logger.warning("Platform redemption failed: %s", r.text[:500])
                r.raise_for_status()

        text = r.text.lower()
        if "expired" in text:
            return "expired"
        elif "used" in text:
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
