"""Microsoft Teams notification channel — sends alerts via webhook."""

import json
import logging
import urllib.request

logger = logging.getLogger(__name__)


def send_teams_message(webhook_url: str, message: str, severity: str = "info",
                       title: str = "", facts: dict | None = None) -> bool:
    """Send a message to Microsoft Teams via incoming webhook.

    Uses the MessageCard format.

    Args:
        webhook_url: Teams incoming webhook URL
        message: Main message text
        severity: info, warning, critical — determines theme color
        title: Optional card title
        facts: Optional key-value pairs to display

    Returns: True if sent successfully
    """
    color_map = {"info": "0076D7", "warning": "FFC107", "critical": "FF0000"}
    color = color_map.get(severity, "0076D7")

    card = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": color,
        "summary": title or message[:100],
        "sections": [{
            "activityTitle": title or "CI/CD Maturity Alert",
            "text": message,
        }],
    }

    if facts:
        card["sections"][0]["facts"] = [
            {"name": k, "value": str(v)} for k, v in facts.items()
        ]

    payload = json.dumps(card).encode("utf-8")

    try:
        req = urllib.request.Request(
            webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        logger.error(f"Teams send failed: {e}")
        return False
