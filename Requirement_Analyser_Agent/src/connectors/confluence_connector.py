import re
import requests
import urllib3
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ConfluenceConnector:
    """Fetches a Confluence page and its inline comments via the REST API."""

    def __init__(self, base_url: str, email: str, api_token: str):
        self.base_url = base_url.rstrip("/")
        self.auth = HTTPBasicAuth(email, api_token)
        self.headers = {"Accept": "application/json"}

    def fetch_by_id(self, page_id: str) -> str:
        """Return a plain-text block for the given Confluence page ID."""
        page = self._get_page(page_id)
        title = page.get("title", "")
        body_html = page.get("body", {}).get("storage", {}).get("value", "")
        body_text = self._html_to_text(body_html)

        lines = [
            f"=== CONFLUENCE PAGE: {title} (ID: {page_id}) ===",
            "",
            body_text or "(empty page)",
        ]
        return "\n".join(lines)

    def search(self, query: str, space_key: str = "", limit: int = 3) -> str:
        """Search Confluence using CQL and return concatenated plain-text blocks."""
        cql = f'text ~ "{query}" AND type = page'
        if space_key:
            cql += f' AND space = "{space_key}"'
        url = f"{self.base_url}/rest/api/content/search"
        params = {"cql": cql, "limit": limit, "expand": "body.storage"}
        resp = requests.get(url, auth=self.auth, headers=self.headers, params=params, timeout=30, verify=False)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        blocks = []
        for r in results:
            title = r.get("title", "")
            body_html = r.get("body", {}).get("storage", {}).get("value", "")
            blocks.append(f"=== CONFLUENCE: {title} ===\n{self._html_to_text(body_html)}")
        return "\n\n".join(blocks) if blocks else "(no Confluence results)"

    # ------------------------------------------------------------------

    def _get_page(self, page_id: str) -> dict:
        url = f"{self.base_url}/rest/api/content/{page_id}"
        resp = requests.get(
            url,
            auth=self.auth,
            headers=self.headers,
            params={"expand": "body.storage"},
            timeout=30,
            verify=False,
        )
        resp.raise_for_status()
        return resp.json()

    def _html_to_text(self, html: str) -> str:
        """Strip HTML tags; fall back to raw text on failure."""
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"&nbsp;", " ", text)
        text = re.sub(r"&lt;", "<", text)
        text = re.sub(r"&gt;", ">", text)
        text = re.sub(r"&amp;", "&", text)
        text = re.sub(r"\s{2,}", " ", text)
        return text.strip()
