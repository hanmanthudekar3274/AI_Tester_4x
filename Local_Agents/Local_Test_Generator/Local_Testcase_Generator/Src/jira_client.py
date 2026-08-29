import urllib3
import requests
from requests.auth import HTTPBasicAuth

# SSL verification disabled to handle corporate proxy / custom CA on Windows
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class JiraClientError(Exception):
    pass


def _extract_adf_text(node) -> str:
    """Recursively extract plain text from an Atlassian Document Format node."""
    if not isinstance(node, dict):
        return ""
    if node.get("type") == "text":
        return node.get("text", "")
    parts = []
    for child in node.get("content", []):
        text = _extract_adf_text(child)
        if text:
            parts.append(text)
    separator = "\n" if node.get("type") in ("paragraph", "heading", "listItem", "bulletList", "orderedList") else " "
    return separator.join(parts)


def fetch_ticket(ticket_key: str, config: dict) -> dict:
    jira_url = config.get("jira_url", "").rstrip("/")
    email = config.get("jira_email", "")
    token = config.get("jira_api_token", "")

    if not jira_url or not email or not token:
        raise JiraClientError("Jira credentials are not configured. Go to Settings.")

    url = f"{jira_url}/rest/api/3/issue/{ticket_key}"
    try:
        resp = requests.get(url, auth=HTTPBasicAuth(email, token), timeout=15, verify=False)
    except requests.exceptions.ConnectionError:
        raise JiraClientError(f"Cannot connect to Jira at {jira_url}. Check the URL in Settings.")
    except requests.exceptions.Timeout:
        raise JiraClientError("Jira request timed out.")

    if resp.status_code == 401:
        raise JiraClientError("Jira authentication failed. Check email and API token in Settings.")
    if resp.status_code == 404:
        raise JiraClientError(f"Ticket '{ticket_key}' not found in Jira.")
    if not resp.ok:
        raise JiraClientError(f"Jira returned {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    fields = data.get("fields", {})

    description_raw = fields.get("description")
    if isinstance(description_raw, dict):
        description = _extract_adf_text(description_raw).strip()
    elif isinstance(description_raw, str):
        description = description_raw.strip()
    else:
        description = ""

    # Check customfield_10016 first, then fall back to any field with "acceptance" in the name
    acceptance_criteria = ""
    cf = fields.get("customfield_10016")
    if cf:
        if isinstance(cf, dict):
            acceptance_criteria = _extract_adf_text(cf).strip()
        elif isinstance(cf, str):
            acceptance_criteria = cf.strip()

    if not acceptance_criteria:
        for key, val in fields.items():
            if "acceptance" in key.lower() and isinstance(val, (str, dict)):
                if isinstance(val, dict):
                    acceptance_criteria = _extract_adf_text(val).strip()
                else:
                    acceptance_criteria = val.strip()
                break

    return {
        "key": ticket_key,
        "summary": fields.get("summary", ""),
        "description": description,
        "acceptance_criteria": acceptance_criteria,
        "priority": (fields.get("priority") or {}).get("name", ""),
        "issue_type": (fields.get("issuetype") or {}).get("name", ""),
    }
