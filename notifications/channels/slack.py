"""Slack notification channel — sends alerts via webhook."""

import json
import logging
import urllib.request

logger = logging.getLogger(__name__)


def send_slack_message(webhook_url: str, message: str, severity: str = "info",
                       title: str = "", fields: dict | None = None) -> bool:
    """Send a message to Slack via incoming webhook.

    Args:
        webhook_url: Slack incoming webhook URL
        message: Main message text
        severity: info, warning, critical — determines color
        title: Optional bold title
        fields: Optional key-value pairs to display

    Returns: True if sent successfully
    """
    color_map = {"info": "#3B82F6", "warning": "#FBBF24", "critical": "#EF4444"}
    color = color_map.get(severity, "#3B82F6")

    attachment = {
        "color": color,
        "text": message,
        "fallback": message,
    }
    if title:
        attachment["title"] = title
    if fields:
        attachment["fields"] = [
            {"title": k, "value": str(v), "short": True}
            for k, v in fields.items()
        ]

    payload = json.dumps({"attachments": [attachment]}).encode("utf-8")

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
        logger.error(f"Slack send failed: {e}")
        return False
