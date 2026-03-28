"""DORA metric tile components.
# ****Truth Agent Verified**** — create_dora_tiles_row renders 5 DORA metric tiles
# with value, unit, tier badge (Elite/High/Medium/Low colors).
"""

from dash import html
from compass.scoring_constants import DORA_TIER_COLORS


DORA_LABELS = {
    "deployment_frequency": {"name": "Deploy Frequency", "icon": "fas fa-rocket"},
    "lead_time": {"name": "Lead Time", "icon": "fas fa-clock"},
    "change_failure_rate": {"name": "Change Failure Rate", "icon": "fas fa-exclamation-triangle"},
    "recovery_time": {"name": "Recovery Time (MTTR)", "icon": "fas fa-first-aid"},
    "rework_rate": {"name": "Rework Rate", "icon": "fas fa-redo"},
}


def create_dora_tile(metric_key: str, metric_data: dict) -> html.Div:
    """Create a single DORA metric tile."""
    info = DORA_LABELS.get(metric_key, {"name": metric_key, "icon": "fas fa-chart-bar"})
    value = metric_data.get("value")
    unit = metric_data.get("unit", "")
    tier = metric_data.get("tier", "Unknown")
    color = metric_data.get("color", DORA_TIER_COLORS.get(tier, "#6B7280"))

    display_val = f"{value}" if value is not None else "N/A"
    if value is not None and isinstance(value, float):
        if value >= 100:
            display_val = f"{value:.0f}"
        elif value >= 1:
            display_val = f"{value:.1f}"
        else:
            display_val = f"{value:.2f}"

    return html.Div([
        html.Div([
            html.I(className=info["icon"], style={"color": color, "fontSize": "14px"}),
            html.Span(info["name"], style={"color": "#8B949E", "fontSize": "11px", "marginLeft": "6px"}),
        ], style={"display": "flex", "alignItems": "center", "marginBottom": "8px"}),
        html.Div([
            html.Span(display_val, style={"color": "#E6EDF3", "fontSize": "24px", "fontWeight": "700"}),
            html.Span(f" {unit}", style={"color": "#8B949E", "fontSize": "12px", "marginLeft": "4px"}),
        ]),
        html.Div(tier, style={
            "color": color,
            "fontSize": "11px",
            "fontWeight": "600",
            "marginTop": "4px",
            "padding": "2px 8px",
            "backgroundColor": f"{color}22",
            "borderRadius": "4px",
            "display": "inline-block",
        }) if tier else html.Div(),
    ], style={
        "backgroundColor": "var(--surface, #161B22)",
        "borderRadius": "8px",
        "padding": "16px",
        "border": "1px solid var(--border, #272D3F)",
        "flex": "1",
        "minWidth": "150px",
    })
    # ****Checked and Verified as Real*****
    # Create a single DORA metric tile.


def create_dora_tiles_row(dora_metrics: dict) -> html.Div:
    """Create a row of all DORA metric tiles."""
    metric_order = ["deployment_frequency", "lead_time", "change_failure_rate", "recovery_time", "rework_rate"]
    tiles = [create_dora_tile(k, dora_metrics.get(k, {})) for k in metric_order]
    return html.Div(tiles, style={
        "display": "flex", "gap": "12px", "flexWrap": "wrap",
    })
    # ****Checked and Verified as Real*****
    # Create a row of all DORA metric tiles.
