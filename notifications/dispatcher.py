"""Alert Dispatcher — Routes coaching alerts to configured notification channels."""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AlertDispatcher:
    """Routes alerts to configured notification channels (Slack, Teams, Email, Jira)."""

    def __init__(self, channel_configs: list[dict] = None):
        self.channels = channel_configs or []
        self._handlers = {
            "slack": self._send_slack,
            "teams": self._send_teams,
            "email": self._send_email,
            "jira": self._create_jira_ticket,
        }

    def dispatch(self, alert: dict) -> list[dict]:
        """
        Send an alert to all configured channels for the alert's team.

        Args:
            alert: {
                "team_id": str,
                "alert_type": str (score_drop, non_standard_deploy, hard_gate_failure, stale_data),
                "severity": str (info, warning, critical),
                "title": str,
                "description": str,
                "data": dict (optional extra data),
            }

        Returns: List of dispatch results [{channel, status, error}]
        """
        results = []
        team_id = alert.get("team_id", "")

        for channel in self._get_channels(team_id, alert.get("severity", "info")):
            channel_type = channel.get("type", "")
            handler = self._handlers.get(channel_type)
            if not handler:
                logger.warning("Unknown channel type: %s", channel_type)
                continue

            try:
                handler(channel, alert)
                results.append({"channel": channel_type, "status": "sent"})
                logger.info("Alert dispatched: type=%s channel=%s team=%s",
                            alert.get("alert_type"), channel_type, team_id)
            except Exception as e:
                logger.error("Failed to dispatch to %s: %s", channel_type, e)
                results.append({"channel": channel_type, "status": "error", "error": str(e)})

        return results

    def dispatch_batch(self, alerts: list[dict]) -> list[dict]:
        """Dispatch multiple alerts."""
        all_results = []
        for alert in alerts:
            all_results.extend(self.dispatch(alert))
        return all_results

    def _get_channels(self, team_id: str, severity: str) -> list[dict]:
        """Get notification channels for a team and severity level."""
        severity_order = {"info": 0, "warning": 1, "critical": 2}
        alert_level = severity_order.get(severity, 0)

        applicable = []
        for ch in self.channels:
            # Check team scope
            teams = ch.get("teams", [])
            if teams and team_id not in teams and "*" not in teams:
                continue

            # Check severity threshold
            min_severity = ch.get("min_severity", "info")
            if severity_order.get(min_severity, 0) > alert_level:
                continue

            applicable.append(ch)

        return applicable

    def _send_slack(self, channel: dict, alert: dict):
        """Send alert to Slack via webhook."""
        import json
        import urllib.request

        webhook_url = channel.get("webhook_url", "")
        if not webhook_url:
            raise ValueError("Slack webhook_url not configured")

        severity_emoji = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨"}
        emoji = severity_emoji.get(alert.get("severity", "info"), "📋")

        payload = {
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": f"{emoji} {alert.get('title', 'Alert')}"},
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": alert.get("description", "")},
                },
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": f"*Team:* {alert.get('team_id', 'N/A')}"},
                        {"type": "mrkdwn", "text": f"*Severity:* {alert.get('severity', 'info')}"},
                        {"type": "mrkdwn", "text": f"*Type:* {alert.get('alert_type', 'unknown')}"},
                    ],
                },
            ],
        }

        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=10)

    def _send_teams(self, channel: dict, alert: dict):
        """Send alert to Microsoft Teams via webhook."""
        import json
        import urllib.request

        webhook_url = channel.get("webhook_url", "")
        if not webhook_url:
            raise ValueError("Teams webhook_url not configured")

        color_map = {"info": "0078D7", "warning": "FFC107", "critical": "DC3545"}

        payload = {
            "@type": "MessageCard",
            "themeColor": color_map.get(alert.get("severity", "info"), "0078D7"),
            "summary": alert.get("title", "Alert"),
            "sections": [{
                "activityTitle": alert.get("title", "Alert"),
                "activitySubtitle": f"Team: {alert.get('team_id', 'N/A')}",
                "text": alert.get("description", ""),
                "facts": [
                    {"name": "Severity", "value": alert.get("severity", "info")},
                    {"name": "Type", "value": alert.get("alert_type", "unknown")},
                    {"name": "Time", "value": datetime.utcnow().isoformat()},
                ],
            }],
        }

        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=10)

    def _send_email(self, channel: dict, alert: dict):
        """Send alert via email (SMTP or SendGrid)."""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        smtp_host = channel.get("smtp_host", "localhost")
        smtp_port = channel.get("smtp_port", 587)
        smtp_user = channel.get("smtp_user", "")
        smtp_pass = channel.get("smtp_pass", "")
        from_addr = channel.get("from_address", "compass@pipeline-compass.io")
        to_addrs = channel.get("to_addresses", [])

        if not to_addrs:
            raise ValueError("No email recipients configured")

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[Pipeline Compass] {alert.get('severity', 'info').upper()}: {alert.get('title', 'Alert')}"
        msg["From"] = from_addr
        msg["To"] = ", ".join(to_addrs)

        body = f"""
        <h2>{alert.get('title', 'Alert')}</h2>
        <p>{alert.get('description', '')}</p>
        <hr>
        <p><strong>Team:</strong> {alert.get('team_id', 'N/A')}</p>
        <p><strong>Severity:</strong> {alert.get('severity', 'info')}</p>
        <p><strong>Type:</strong> {alert.get('alert_type', 'unknown')}</p>
        <p><em>Generated by Pipeline Compass at {datetime.utcnow().isoformat()}</em></p>
        """
        msg.attach(MIMEText(body, "html"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if smtp_user:
                server.starttls()
                server.login(smtp_user, smtp_pass)
            server.sendmail(from_addr, to_addrs, msg.as_string())

    def _create_jira_ticket(self, channel: dict, alert: dict):
        """Create a Jira ticket for the alert."""
        import json
        import urllib.request
        import base64

        jira_url = channel.get("jira_url", "").rstrip("/")
        email = channel.get("jira_email", "")
        token = channel.get("jira_token", "")
        project_key = channel.get("jira_project", "CICD")

        if not jira_url or not email or not token:
            raise ValueError("Jira connection not fully configured")

        severity_priority = {"info": "Low", "warning": "Medium", "critical": "High"}

        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": f"[Compass] {alert.get('title', 'Alert')}",
                "description": (
                    f"{alert.get('description', '')}\n\n"
                    f"Team: {alert.get('team_id', 'N/A')}\n"
                    f"Alert Type: {alert.get('alert_type', 'unknown')}\n"
                    f"Severity: {alert.get('severity', 'info')}\n"
                    f"Generated: {datetime.utcnow().isoformat()}"
                ),
                "issuetype": {"name": "Task"},
                "priority": {"name": severity_priority.get(alert.get("severity", "info"), "Medium")},
                "labels": ["pipeline-compass", "auto-generated"],
            },
        }

        auth = base64.b64encode(f"{email}:{token}".encode()).decode()
        req = urllib.request.Request(
            f"{jira_url}/rest/api/2/issue",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Basic {auth}",
            },
        )
        urllib.request.urlopen(req, timeout=15)
