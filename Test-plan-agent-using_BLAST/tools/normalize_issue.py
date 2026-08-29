"""Normalize a raw Jira payload into the LLM.md section 2 input schema.

Implements architecture/normalization_sop.md.

Pure function of its input. No LLM call, no network. Never raises on malformed
content: it degrades to an empty value and records a quality flag instead.
"""

from __future__ import annotations

import re
from typing import Any

MAX_ADF_DEPTH = 50

_BULLET_RE = re.compile(r"^\s*(?:[-*•●]|\d+[.)])\s+")
_AC_HEADING_RE = re.compile(
    r"^\s*(?:\**\s*)?(?:acceptance\s+criteri(?:a|on)|\bac\b)\s*:?\s*(?:\**)?\s*$",
    re.IGNORECASE,
)
_GHERKIN_RE = re.compile(r"^\s*(given|when|then|and|but)\b", re.IGNORECASE)
_GHERKIN_START_RE = re.compile(r"^\s*given\b", re.IGNORECASE)

# Node types whose children are joined with a newline rather than a space.
_BLOCK_TYPES = {"paragraph", "heading", "bulletList", "orderedList", "listItem",
                "blockquote", "panel", "tableRow"}


# --------------------------------------------------------------------------
# ADF flattening
# --------------------------------------------------------------------------

def adf_to_text(node: Any, depth: int = 0) -> str:
    """Flatten an Atlassian Document Format tree to plain text.

    Accepts a plain string (Server-style payload) and returns it unchanged.
    Unknown node types recurse generically rather than crashing.
    """
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if depth > MAX_ADF_DEPTH:
        return ""
    if isinstance(node, list):
        return "\n".join(part for part in (adf_to_text(n, depth + 1) for n in node) if part)
    if not isinstance(node, dict):
        return str(node)

    node_type = node.get("type", "")
    attrs = node.get("attrs") or {}
    children = node.get("content") or []

    if node_type == "text":
        return node.get("text", "")
    if node_type == "hardBreak":
        return "\n"
    if node_type in ("mediaSingle", "media"):
        filename = attrs.get("alt") or attrs.get("id") or "file"
        return f"[attachment: {filename}]"
    if node_type == "inlineCard":
        return attrs.get("url", "")
    if node_type == "rule":
        return "---"
    if node_type == "emoji":
        return attrs.get("text", "")
    if node_type == "mention":
        return f"@{attrs.get('text', 'user')}"

    if node_type == "codeBlock":
        body = "".join(adf_to_text(c, depth + 1) for c in children)
        return f"```\n{body}\n```"

    if node_type == "listItem":
        body = " ".join(
            part for part in (adf_to_text(c, depth + 1) for c in children) if part
        )
        return f"- {body.strip()}"

    if node_type == "tableRow":
        cells = [adf_to_text(c, depth + 1).strip() for c in children]
        return " | ".join(cells)

    if node_type in ("tableCell", "tableHeader"):
        return " ".join(
            part for part in (adf_to_text(c, depth + 1) for c in children) if part
        ).strip()

    parts = [adf_to_text(child, depth + 1) for child in children]
    parts = [p for p in parts if p]

    if node_type in _BLOCK_TYPES or node_type in ("doc", "table"):
        if node_type in ("paragraph", "heading"):
            return " ".join(parts).strip()
        return "\n".join(parts)

    return " ".join(parts).strip()


def _doc_to_text(node: Any) -> str:
    """Flatten a top-level document, keeping blank lines between blocks."""
    if node is None:
        return ""
    if isinstance(node, str):
        return node.strip()
    if isinstance(node, dict) and node.get("type") == "doc":
        blocks = [adf_to_text(child) for child in (node.get("content") or [])]
        return "\n\n".join(b.strip() for b in blocks if b.strip())
    return adf_to_text(node).strip()


# --------------------------------------------------------------------------
# Acceptance criteria extraction
# --------------------------------------------------------------------------

def split_criteria(text: str) -> list[str]:
    """Split a criteria blob into individual criteria per the SOP rules."""
    if not text or not text.strip():
        return []

    lines = text.splitlines()
    bulleted = [ln for ln in lines if _BULLET_RE.match(ln)]

    if bulleted:
        items = [_BULLET_RE.sub("", ln).strip() for ln in bulleted]
    else:
        blocks = re.split(r"\n\s*\n", text)
        items = [b.strip().replace("\n", " ") for b in blocks]
        if len(items) <= 1:
            items = [ln.strip() for ln in lines]

    return [item for item in (i.strip(" -*•\t") for i in items) if len(item) >= 3]


def _criteria_from_heading(description: str) -> list[str]:
    """Pull the block that follows an 'Acceptance Criteria' heading."""
    lines = description.splitlines()
    collected: list[str] = []
    capturing = False

    for line in lines:
        if _AC_HEADING_RE.match(line):
            capturing = True
            continue
        if capturing:
            stripped = line.strip()
            # A new heading ends the block. Bullets do not.
            is_heading = (
                stripped.startswith("#")
                or (stripped.endswith(":") and len(stripped) < 60 and not _BULLET_RE.match(line))
            )
            if is_heading:
                break
            collected.append(line)

    return split_criteria("\n".join(collected)) if collected else []


def _criteria_from_gherkin(description: str) -> list[str]:
    """Group consecutive Given/When/Then lines into criteria."""
    criteria: list[str] = []
    current: list[str] = []

    for line in description.splitlines():
        stripped = _BULLET_RE.sub("", line).strip()
        if not stripped:
            # Blank lines separate ADF blocks and must not break a
            # Given/When/Then group that spans several paragraphs.
            continue
        if _GHERKIN_RE.match(stripped):
            if _GHERKIN_START_RE.match(stripped) and current:
                criteria.append(" ".join(current))
                current = []
            current.append(stripped)
        elif current:
            criteria.append(" ".join(current))
            current = []

    if current:
        criteria.append(" ".join(current))

    return [c for c in criteria if len(c) >= 3]


def extract_acceptance_criteria(
    fields: dict[str, Any],
    ac_field_id: str | None,
    description: str,
) -> tuple[list[str], str]:
    """Return (criteria, source). Source is one of: custom_field,
    description_heading, gherkin, none."""
    if ac_field_id:
        raw = fields.get(ac_field_id)
        criteria = split_criteria(_doc_to_text(raw))
        if criteria:
            return criteria, "custom_field"

    criteria = _criteria_from_heading(description)
    if criteria:
        return criteria, "description_heading"

    criteria = _criteria_from_gherkin(description)
    if criteria:
        return criteria, "gherkin"

    return [], "none"


# --------------------------------------------------------------------------
# Field mapping
# --------------------------------------------------------------------------

def _named(value: Any, key: str = "name") -> Any:
    return value.get(key) if isinstance(value, dict) else None


def normalize(payload: dict[str, Any]) -> dict[str, Any]:
    """Turn a jira_client.fetch_issue payload into the input schema."""
    issue = payload.get("issue") or {}
    fields = issue.get("fields") or {}
    field_map = payload.get("field_map") or {}
    ac_field_id = field_map.get("acceptance_criteria")

    issue_key = issue.get("key", "UNKNOWN")
    description = _doc_to_text(fields.get("description"))
    criteria, ac_source = extract_acceptance_criteria(fields, ac_field_id, description)

    issue_type = _named(fields.get("issuetype")) or "Task"

    subtasks = [
        {
            "key": st.get("key"),
            "summary": (st.get("fields") or {}).get("summary"),
            "status": _named(((st.get("fields") or {}).get("status"))),
        }
        for st in (fields.get("subtasks") or [])
    ]

    linked: list[dict[str, Any]] = []
    for link in fields.get("issuelinks") or []:
        link_type = link.get("type") or {}
        for direction, label_key in (("outwardIssue", "outward"), ("inwardIssue", "inward")):
            target = link.get(direction)
            if target:
                linked.append({
                    "key": target.get("key"),
                    "summary": (target.get("fields") or {}).get("summary"),
                    "link_type": link_type.get(label_key) or link_type.get("name") or "relates to",
                })

    comments = [
        {
            "author": _named(c.get("author"), "displayName"),
            "created": c.get("created"),
            "body": _doc_to_text(c.get("body")),
        }
        for c in (payload.get("comments") or [])
    ]
    comments = [c for c in comments if (c["body"] or "").strip()]

    attachments = [
        {
            "filename": a.get("filename"),
            "mime_type": a.get("mimeType"),
            "url": a.get("content"),
        }
        for a in (fields.get("attachment") or [])
    ]

    parent = fields.get("parent") or {}

    normalized = {
        "issue_key": issue_key,
        "url": f"{(issue.get('self') or '').split('/rest/')[0]}/browse/{issue_key}"
               if issue.get("self") else None,
        "summary": fields.get("summary") or "",
        "description": description,
        "issue_type": issue_type,
        "priority": _named(fields.get("priority")),
        "status": _named(fields.get("status")),
        "assignee": _named(fields.get("assignee"), "displayName"),
        "reporter": _named(fields.get("reporter"), "displayName"),
        "parent_key": parent.get("key"),
        "labels": list(fields.get("labels") or []),
        "components": [c.get("name") for c in (fields.get("components") or []) if c.get("name")],
        "acceptance_criteria": criteria,
        "subtasks": subtasks,
        "linked_issues": linked,
        "comments": comments,
        "attachments": attachments,
        "fetched_at": payload.get("fetched_at"),
    }

    quality = {
        "has_description": bool(description.strip()),
        "has_acceptance_criteria": bool(criteria),
        "acceptance_criteria_source": ac_source,
        "comments_truncated": bool(payload.get("comments_truncated")),
        "is_epic": str(issue_type).lower() == "epic",
        "subtask_count": len(subtasks),
        "comment_count": len(comments),
    }

    return {"issue": normalized, "quality": quality}
