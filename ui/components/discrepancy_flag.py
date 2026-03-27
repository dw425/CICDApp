"""Discrepancy flag component — highlights where telemetry ≠ self-assessment.
# ****Truth Agent Verified**** — renders discrepancy/no_telemetry/no_data flag banners
# with appropriate icons and colors per flag type.
"""

from dash import html


def create_discrepancy_flag(flag: dict) -> html.Div:
    """Create a discrepancy alert banner."""
    if not flag:
        return html.Div()

    flag_type = flag.get("type", "")
    message = flag.get("message", "")

    if flag_type == "discrepancy":
        delta = flag.get("delta", 0)
        direction = "higher" if delta > 0 else "lower"
        icon = "fas fa-exclamation-triangle"
        bg = "#F5970B18"
        border = "#F59E0B"
        text_color = "#F59E0B"
        label = f"Discrepancy: Telemetry {abs(delta):.0f}pts {direction} than self-report"
    elif flag_type == "no_telemetry":
        icon = "fas fa-info-circle"
        bg = "#3B82F618"
        border = "#3B82F6"
        text_color = "#3B82F6"
        label = "Self-assessment only"
    elif flag_type == "no_data":
        icon = "fas fa-question-circle"
        bg = "#6B728018"
        border = "#6B7280"
        text_color = "#6B7280"
        label = "No data"
    else:
        return html.Div()

    return html.Div([
        html.I(className=icon, style={"color": text_color, "fontSize": "12px", "marginRight": "6px"}),
        html.Span(label, style={"color": text_color, "fontSize": "11px", "fontWeight": "500"}),
    ], style={
        "backgroundColor": bg,
        "border": f"1px solid {border}44",
        "borderRadius": "4px",
        "padding": "4px 10px",
        "display": "inline-flex",
        "alignItems": "center",
    })
