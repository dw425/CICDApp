"""Hygiene check card component.
# ****Truth Agent Verified**** — create_hygiene_check_grid, individual check card with
# score color, platform icon, dimension badge, hard-gate indicator.
# PLATFORM_LABELS and PLATFORM_ICONS constants for 6 platforms.
"""

from dash import html


PLATFORM_ICONS = {
    "github": "fab fa-github",
    "azure_devops": "fab fa-microsoft",
    "jenkins": "fas fa-server",
    "gitlab": "fab fa-gitlab",
    "jira": "fab fa-jira",
    "databricks": "fas fa-database",
}

PLATFORM_LABELS = {
    "github": "GitHub",
    "azure_devops": "Azure DevOps",
    "jenkins": "Jenkins",
    "gitlab": "GitLab",
    "jira": "Jira",
    "databricks": "Databricks",
}


def create_hygiene_check_card(check) -> html.Div:
    """Create a card for a single hygiene check result."""
    icon = PLATFORM_ICONS.get(check.platform, "fas fa-circle")
    score = check.score
    status_color = check.status_color

    return html.Div([
        html.Div([
            html.Div([
                html.I(className=icon, style={"color": "#8B949E", "fontSize": "12px", "marginRight": "8px"}),
                html.Span(check.check_name, style={"color": "#E6EDF3", "fontSize": "13px", "fontWeight": "600"}),
                html.Span(" HG", style={
                    "color": "#EF4444", "fontSize": "9px", "fontWeight": "700",
                    "backgroundColor": "#EF444422", "padding": "1px 4px", "borderRadius": "3px",
                    "marginLeft": "6px",
                }) if check.hard_gate else html.Span(),
            ], style={"display": "flex", "alignItems": "center"}),
            html.Div([
                html.Span(f"{score:.0f}", style={
                    "color": status_color, "fontSize": "18px", "fontWeight": "700",
                }),
                html.Span("/100", style={"color": "#484F58", "fontSize": "11px"}),
            ]),
        ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"}),
        html.Div([
            html.Span(check.dimension.replace("_", " ").title(), style={
                "color": "#484F58", "fontSize": "10px",
                "backgroundColor": "#21262D", "padding": "2px 6px", "borderRadius": "3px",
            }),
            html.Span(f"W{check.weight}", style={
                "color": "#484F58", "fontSize": "10px", "marginLeft": "6px",
            }),
        ], style={"marginTop": "6px"}),
        html.Div(check.scoring_rule, style={
            "color": "#484F58", "fontSize": "10px", "marginTop": "4px",
        }),
    ], style={
        "backgroundColor": "var(--surface, #161B22)",
        "borderRadius": "6px",
        "padding": "12px",
        "border": f"1px solid {status_color}33",
        "borderLeft": f"3px solid {status_color}",
    })


def create_hygiene_check_grid(checks: list) -> html.Div:
    """Create a grid of hygiene check cards."""
    cards = [create_hygiene_check_card(c) for c in checks]
    return html.Div(cards, style={
        "display": "grid",
        "gridTemplateColumns": "repeat(auto-fill, minmax(300px, 1fr))",
        "gap": "10px",
    })
