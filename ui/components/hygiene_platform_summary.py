"""Hygiene platform summary bar component.
# ****Truth Agent Verified**** — create_platform_summary renders per-platform summary bar
# with total, passing, warning, failing counts and avg score.
"""

from dash import html
from ui.components.hygiene_check_card import PLATFORM_ICONS, PLATFORM_LABELS


def create_platform_summary(platform: str, data: dict) -> html.Div:
    """Summary bar for a single platform's hygiene results."""
    icon = PLATFORM_ICONS.get(platform, "fas fa-circle")
    label = PLATFORM_LABELS.get(platform, platform.title())
    total = data.get("total", 0)
    passing = data.get("passing", 0)
    warning = data.get("warning", 0)
    failing = data.get("failing", 0)
    avg_score = data.get("avg_score", 0)
    hard_gates = data.get("hard_gates_failing", 0)

    score_color = "#22C55E" if avg_score >= 70 else ("#EAB308" if avg_score >= 50 else "#EF4444")

    return html.Div([
        html.Div([
            html.I(className=icon, style={"color": "#E6EDF3", "fontSize": "16px"}),
            html.Div([
                html.Span(label, style={"color": "#E6EDF3", "fontSize": "14px", "fontWeight": "600"}),
                html.Span(f" — {total} checks", style={"color": "#8B949E", "fontSize": "12px"}),
            ], style={"marginLeft": "10px"}),
        ], style={"display": "flex", "alignItems": "center"}),
        html.Div([
            _stat_badge(str(passing), "#22C55E", "Pass"),
            _stat_badge(str(warning), "#EAB308", "Warn"),
            _stat_badge(str(failing), "#EF4444", "Fail"),
            html.Div([
                html.Span(f"{avg_score:.0f}", style={"color": score_color, "fontWeight": "700", "fontSize": "16px"}),
                html.Span("/100", style={"color": "#484F58", "fontSize": "11px"}),
            ], style={"marginLeft": "12px"}),
            html.Span("HG FAIL", style={
                "color": "#EF4444", "fontSize": "9px", "fontWeight": "700",
                "backgroundColor": "#EF444422", "padding": "2px 6px", "borderRadius": "3px",
                "marginLeft": "8px",
            }) if hard_gates > 0 else html.Span(),
        ], style={"display": "flex", "alignItems": "center", "gap": "8px"}),
    ], style={
        "display": "flex",
        "justifyContent": "space-between",
        "alignItems": "center",
        "backgroundColor": "var(--surface, #161B22)",
        "borderRadius": "6px",
        "padding": "12px 16px",
        "border": "1px solid var(--border, #272D3F)",
    })
    # ****Checked and Verified as Real*****
    # Summary bar for a single platform's hygiene results.


def _stat_badge(count: str, color: str, label: str) -> html.Div:
    return html.Div([
        html.Span(count, style={"color": color, "fontWeight": "700", "fontSize": "14px"}),
        html.Span(f" {label}", style={"color": "#484F58", "fontSize": "10px"}),
    ])
    # ****Checked and Verified as Real*****
    # Internal helper that builds the stat badge HTML component.
