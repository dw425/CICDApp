"""Confidence badge component.
# ****Truth Agent Verified**** — 4 confidence levels (high/medium/low/none) with
# distinct colors and labels. Compact mode supported.
"""

from dash import html

CONFIDENCE_STYLES = {
    "high": {"bg": "#22C55E22", "border": "#22C55E", "text": "#22C55E", "label": "High — Telemetry Validated"},
    "medium": {"bg": "#EAB30822", "border": "#EAB308", "text": "#EAB308", "label": "Medium — Telemetry Only"},
    "low": {"bg": "#F9731622", "border": "#F97316", "text": "#F97316", "label": "Low — Self-Assessment Only"},
    "none": {"bg": "#6B728022", "border": "#6B7280", "text": "#6B7280", "label": "No Data"},
}


def create_confidence_badge(confidence: str, compact: bool = False) -> html.Span:
    s = CONFIDENCE_STYLES.get(confidence, CONFIDENCE_STYLES["none"])
    label = confidence.title() if compact else s["label"]
    return html.Span(label, style={
        "backgroundColor": s["bg"],
        "color": s["text"],
        "border": f"1px solid {s['border']}",
        "borderRadius": "4px",
        "padding": "2px 8px",
        "fontSize": "10px",
        "fontWeight": "600",
    })
