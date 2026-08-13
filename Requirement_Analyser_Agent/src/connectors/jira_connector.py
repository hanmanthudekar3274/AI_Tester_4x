import re
import warnings
import requests
import urllib3
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class JiraConnector:
    """Fetches a Jira issue and its comments via the REST API v3."""

    def __init__(self, base_url: str, email: str, api_token: str):
        self.base_url = base_url.rstrip("/")
        self.auth = HTTPBasicAuth(email, api_token)
        self.headers = {"Accept": "application/json"}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch(self, issue_key: str) -> str:
        """Return a plain-text block for the given issue key (e.g. AAA-50)."""
        issue = self._get_issue(issue_key)
        fields = issue.get("fields", {})

        title = fields.get("summary", "")
        status = fields.get("status", {}).get("name", "")
        issue_type = fields.get("issuetype", {}).get("name", "")
        description = self._adf_to_text(fields.get("description") or {})
        acceptance = self._extract_acceptance_criteria(fields)
        comments = self._fetch_comments(issue_key)

        lines = [
            f"=== JIRA ISSUE: {issue_key} ===",
            f"Title: {title}",
            f"Type: {issue_type}  |  Status: {status}",
            "",
            "--- Description ---",
            description or "(no description)",
            "",
            "--- Acceptance Criteria ---",
            acceptance or "(none found)",
            "",
            "--- Comments ---",
        ]
        if comments:
            for c in comments:
                lines.append(f"[{c['author']}]: {c['body']}")
        else:
            lines.append("(no comments)")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_issue(self, issue_key: str) -> dict:
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
        resp = requests.get(url, auth=self.auth, headers=self.headers, timeout=30, verify=False)
        resp.raise_for_status()
        return resp.json()

    def _fetch_comments(self, issue_key: str) -> list[dict]:
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/comment"
        resp = requests.get(url, auth=self.auth, headers=self.headers, timeout=30, verify=False)
        resp.raise_for_status()
        data = resp.json()
        results = []
        for c in data.get("comments", []):
            author = c.get("author", {}).get("displayName", "Unknown")
            body = self._adf_to_text(c.get("body") or {})
            results.append({"author": author, "body": body})
        return results

    def _adf_to_text(self, node: dict) -> str:
        """Recursively extract plain text from Atlassian Document Format."""
        if not node:
            return ""
        if node.get("type") == "text":
            return node.get("text", "")
        parts = []
        for child in node.get("content", []):
            text = self._adf_to_text(child)
            if text:
                parts.append(text)
            if child.get("type") in ("paragraph", "listItem", "heading"):
                parts.append("\n")
        return "".join(parts).strip()

    def _extract_acceptance_criteria(self, fields: dict) -> str:
        """Try common custom field names for acceptance criteria."""
        for key, val in fields.items():
            if "acceptance" in key.lower() or "criteria" in key.lower():
                if isinstance(val, dict):
                    return self._adf_to_text(val)
                if isinstance(val, str):
                    return val
        description = self._adf_to_text(fields.get("description") or {})
        match = re.search(
            r"acceptance criteria[:\n]+(.*?)(?:\n\n|\Z)", description, re.IGNORECASE | re.DOTALL
        )
        return match.group(1).strip() if match else ""
