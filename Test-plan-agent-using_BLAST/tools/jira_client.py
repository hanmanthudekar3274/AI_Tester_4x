"""Jira Cloud fetch tool.

Implements architecture/jira_fetch_sop.md. Read-only: every request is a GET
and the API token needs read scope only.

This tool never calls an LLM and never interprets content. It returns raw Jira
JSON; flattening and reshaping belong to normalize_issue.py.
"""

from __future__ import annotations

import json
import re
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from requests.auth import HTTPBasicAuth

from . import config_store

CACHE_DIR = config_store.PROJECT_ROOT / ".tmp" / "cache"
FIELD_MAP_CACHE = CACHE_DIR / "field_map.json"

ISSUE_KEY_RE = re.compile(r"^[A-Z][A-Z0-9]+-\d+$")
TIMEOUT = 20
COMMENT_LIMIT = 50

# The thirteen fields mapped in findings.md section 4. The discovered
# acceptance-criteria field is appended at request time.
BASE_FIELDS = [
    "summary",
    "description",
    "issuetype",
    "priority",
    "status",
    "assignee",
    "reporter",
    "labels",
    "components",
    "subtasks",
    "issuelinks",
    "attachment",
    "parent",
]


class JiraClientError(Exception):
    """Any failure reaching or reading Jira. No untyped exception escapes."""


# --------------------------------------------------------------------------
# Key resolution
# --------------------------------------------------------------------------

def resolve_issue_key(raw: str, config: dict[str, str] | None = None) -> str:
    """Normalize user input into a Jira issue key.

    Accepts 'qa-123', 'QA-123', or a bare '123' when a default project key is
    configured.
    """
    config = config if config is not None else config_store.load_config()
    candidate = (raw or "").strip().upper()

    if ISSUE_KEY_RE.match(candidate):
        return candidate

    if candidate.isdigit():
        default_key = str(config.get("JIRA_DEFAULT_PROJECT_KEY", "")).strip().upper()
        if default_key:
            return f"{default_key}-{candidate}"
        raise JiraClientError(
            f"'{raw}' is a bare number and no default project key is set. "
            "Either type the full key like QA-123, or set a Default Project Key in Settings."
        )

    raise JiraClientError(
        f"'{raw}' is not a valid Jira issue key. Expected a form like QA-123."
    )


# --------------------------------------------------------------------------
# HTTP plumbing
# --------------------------------------------------------------------------

def _base_url(config: dict[str, str]) -> str:
    url = str(config.get("JIRA_BASE_URL", "")).strip().rstrip("/")
    if not url:
        raise JiraClientError("Jira base URL is not set. Add it in Settings.")
    return url


def _auth(config: dict[str, str]) -> HTTPBasicAuth:
    email = str(config.get("JIRA_EMAIL", "")).strip()
    token = str(config.get("JIRA_API_TOKEN", "")).strip()
    if not email or not token:
        raise JiraClientError("Jira email or API token is not set. Add them in Settings.")
    return HTTPBasicAuth(email, token)


def _verify(config: dict[str, str]) -> bool:
    raw = str(config.get("JIRA_VERIFY_SSL", "true")).strip().lower()
    verify = raw not in ("0", "false", "no", "off")
    if not verify:
        warnings.warn(
            "JIRA_VERIFY_SSL is false. TLS certificates are not being checked, "
            "which exposes the API token to interception. Use only on a trusted "
            "corporate network with a proxy that rewrites certificates.",
            stacklevel=2,
        )
    return verify


def _request(path: str, config: dict[str, str], params: dict | None = None) -> Any:
    """GET a Jira endpoint and return parsed JSON, or raise JiraClientError.

    The API token is never included in any raised message.
    """
    url = f"{_base_url(config)}{path}"
    try:
        response = requests.get(
            url,
            auth=_auth(config),
            headers={"Accept": "application/json"},
            params=params or {},
            timeout=TIMEOUT,
            verify=_verify(config),
        )
    except requests.exceptions.SSLError as exc:
        raise JiraClientError(
            "TLS verification failed reaching Jira. If you are behind a corporate "
            "proxy, turn off Verify SSL in Settings, or install the proxy's CA "
            f"certificate. Detail: {exc.__class__.__name__}"
        ) from exc
    except requests.exceptions.ConnectionError as exc:
        raise JiraClientError(
            f"Cannot reach {_base_url(config)}. Check the Jira base URL and your "
            "network connection."
        ) from exc
    except requests.exceptions.Timeout as exc:
        raise JiraClientError(
            f"Jira did not respond within {TIMEOUT} seconds. Try again shortly."
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise JiraClientError(f"Jira request failed: {exc.__class__.__name__}") from exc

    return _handle_response(response, path)


def _handle_response(response: requests.Response, path: str) -> Any:
    if response.status_code == 200:
        try:
            return response.json()
        except ValueError as exc:
            raise JiraClientError(
                "Jira returned a non-JSON response. The base URL may point at a "
                "login page rather than the API."
            ) from exc

    if response.status_code == 401:
        raise JiraClientError(
            "Authentication failed (401). Check the Jira email and API token in Settings."
        )
    if response.status_code == 403:
        raise JiraClientError(
            "Access denied (403). The credentials are valid but this account "
            "cannot view that resource. Check project permissions."
        )
    if response.status_code == 404:
        raise JiraClientError(
            f"Not found (404) at {path}. Check the issue key and the Jira base URL."
        )
    if response.status_code == 429:
        retry_after = response.headers.get("Retry-After", "a few")
        raise JiraClientError(
            f"Jira rate limit reached (429). Retry after {retry_after} seconds."
        )
    if response.status_code >= 500:
        raise JiraClientError(
            f"Jira server error ({response.status_code}). Retry shortly."
        )

    raise JiraClientError(
        f"Jira returned {response.status_code}: {response.text[:200]}"
    )


# --------------------------------------------------------------------------
# Acceptance Criteria field discovery
# --------------------------------------------------------------------------

def discover_field_map(config: dict[str, str], force: bool = False) -> dict[str, str | None]:
    """Find the instance-specific Acceptance Criteria custom field ID.

    Matches on the field NAME, not the field ID. Field IDs are always of the
    form customfield_NNNNN, so matching 'acceptance' against the ID can never
    succeed -- that is the dead-code bug in the sibling project.

    Result is cached per instance. A miss is not fatal.
    """
    if not force and FIELD_MAP_CACHE.exists():
        try:
            return json.loads(FIELD_MAP_CACHE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    fields = _request("/rest/api/3/field", config)

    ac_field: str | None = None
    for field in fields if isinstance(fields, list) else []:
        name = str(field.get("name", "")).lower()
        if "acceptance" in name:
            ac_field = field.get("id")
            break

    field_map = {"acceptance_criteria": ac_field}

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    FIELD_MAP_CACHE.write_text(json.dumps(field_map, indent=2), encoding="utf-8")
    return field_map


# --------------------------------------------------------------------------
# Fetch
# --------------------------------------------------------------------------

def fetch_issue(
    issue_key: str,
    config: dict[str, str] | None = None,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Fetch one issue plus its comments. Returns the raw payload described in
    the SOP, and writes it to .tmp/cache/{issue_key}.json."""
    config = config if config is not None else config_store.load_config()
    issue_key = resolve_issue_key(issue_key, config)

    cache_file = CACHE_DIR / f"{issue_key}.json"
    if not force_refresh and cache_file.exists():
        try:
            return json.loads(cache_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass  # Corrupt cache is not an error; refetch.

    field_map = discover_field_map(config)

    fields = list(BASE_FIELDS)
    if field_map.get("acceptance_criteria"):
        fields.append(field_map["acceptance_criteria"])

    issue = _request(
        f"/rest/api/3/issue/{issue_key}",
        config,
        params={"fields": ",".join(fields)},
    )

    comments_payload = _request(
        f"/rest/api/3/issue/{issue_key}/comment",
        config,
        params={"maxResults": COMMENT_LIMIT, "orderBy": "-created"},
    )
    comments = comments_payload.get("comments", []) if isinstance(comments_payload, dict) else []
    total_comments = comments_payload.get("total", len(comments)) if isinstance(comments_payload, dict) else len(comments)

    payload = {
        "issue": issue,
        "comments": comments,
        "comments_truncated": total_comments > len(comments),
        "comments_total": total_comments,
        "field_map": field_map,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


# --------------------------------------------------------------------------
# Test Connection (used by the Settings screen)
# --------------------------------------------------------------------------

def test_connection(config: dict[str, str]) -> dict[str, Any]:
    """Validate URL, email, and token in one call, then report whether the
    Acceptance Criteria field was found.

    Returns a result dict rather than raising, because the Settings screen
    renders every outcome as a status pill.
    """
    try:
        me = _request("/rest/api/3/myself", config)
    except JiraClientError as exc:
        return {"ok": False, "message": str(exc), "display_name": None, "ac_field": None}

    display_name = me.get("displayName") or me.get("emailAddress") or "unknown user"

    ac_field: str | None = None
    ac_note = ""
    try:
        ac_field = discover_field_map(config, force=True).get("acceptance_criteria")
        if ac_field:
            ac_note = f" Acceptance Criteria field found: {ac_field}."
        else:
            ac_note = (
                " No Acceptance Criteria field found on this instance. "
                "Criteria will be parsed from the description instead."
            )
    except JiraClientError as exc:
        ac_note = f" Could not read the field list: {exc}"

    return {
        "ok": True,
        "message": f"Connected as {display_name}.{ac_note}",
        "display_name": display_name,
        "ac_field": ac_field,
    }


def clear_cache() -> int:
    """Delete cached issue payloads. Returns the number of files removed."""
    if not CACHE_DIR.exists():
        return 0
    removed = 0
    for path in CACHE_DIR.glob("*.json"):
        path.unlink(missing_ok=True)
        removed += 1
    return removed
