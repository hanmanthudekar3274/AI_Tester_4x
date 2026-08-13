import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class SlackConnector:
    """Reads Slack channel messages and thread replies via the Web API."""

    BASE_URL = "https://slack.com/api"

    def __init__(self, bot_token: str):
        self.headers = {
            "Authorization": f"Bearer {bot_token}",
            "Content-Type": "application/json",
        }

    def fetch_channel(self, channel_id: str, limit: int = 50) -> str:
        """Return a plain-text block of the most recent messages in a channel."""
        messages = self._get_history(channel_id, limit)
        lines = [f"=== SLACK CHANNEL: {channel_id} ==="]
        for m in messages:
            user = m.get("user", "unknown")
            text = m.get("text", "")
            lines.append(f"[{user}]: {text}")
            # Fetch thread replies if present
            if m.get("reply_count", 0) > 0:
                ts = m.get("ts", "")
                replies = self._get_thread(channel_id, ts)
                for r in replies[1:]:  # skip the parent
                    ru = r.get("user", "unknown")
                    rt = r.get("text", "")
                    lines.append(f"  ↳ [{ru}]: {rt}")
        return "\n".join(lines) if len(lines) > 1 else "(no messages found)"

    # ------------------------------------------------------------------

    def _get_history(self, channel_id: str, limit: int) -> list[dict]:
        resp = requests.get(
            f"{self.BASE_URL}/conversations.history",
            headers=self.headers,
            params={"channel": channel_id, "limit": limit},
            timeout=30,
            verify=False,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"Slack error: {data.get('error', 'unknown')}")
        return list(reversed(data.get("messages", [])))

    def _get_thread(self, channel_id: str, thread_ts: str) -> list[dict]:
        resp = requests.get(
            f"{self.BASE_URL}/conversations.replies",
            headers=self.headers,
            params={"channel": channel_id, "ts": thread_ts},
            timeout=30,
            verify=False,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            return []
        return data.get("messages", [])
