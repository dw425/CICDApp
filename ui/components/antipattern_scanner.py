"""Anti-Pattern Scanner — Card grid showing detected anti-patterns."""

from dash import html

from compass.antipattern_engine import SEVERITY_COLORS, CATEGORY_LABELS


def create_antipattern_card(ap: dict) -> html.Div:
    """Create a card for a single detected anti-pattern."""
    sev_color = ap.get("severity_color", SEVERITY_COLORS.get(ap["severity"], "#888"))
    category = ap.get("category_label", CATEGORY_LABELS.get(ap["category"], ap["category"]))

    return html.Div([
        # Header
        html.Div([
            html.Div([
                html.Span(ap["severity"].upper(), style={
                    "display": "inline-block",
                    "padding": "1px 8px",
                    "borderRadius": "4px",
                    "backgroundColor": sev_color,
                    "color": "#fff",
                    "fontWeight": "700",
                    "fontSize": "10px",
                    "textTransform": "uppercase",
                }),
                html.Span(category, style={
                    "display": "inline-block",
                    "padding": "1px 8px",
                    "borderRadius": "4px",
                    "backgroundColor": "var(--elevated, #21262D)",
                    "color": "#8B949E",
                    "fontSize": "10px",
                }),
            ], style={"display": "flex", "gap": "6px", "alignItems": "center"}),
        ]),
        # Title
        html.Div(ap["name"], style={
            "color": "#E6EDF3",
            "fontSize": "15px",
            "fontWeight": "700",
            "marginTop": "10px",
        }),
        # Description
        html.Div(ap.get("description", ""), style={
            "color": "#8B949E",
            "fontSize": "12px",
            "marginTop": "6px",
            "lineHeight": "1.5",
        }),
        # Affected dimensions
        html.Div([
            html.Span("Affects: ", style={"color": "#484F58", "fontSize": "11px"}),
            html.Span(
                ", ".join(d.replace("_", " ").title() for d in ap.get("impact_dimensions", [])),
                style={"color": "#8B949E", "fontSize": "11px"},
            ),
        ], style={"marginTop": "8px"}),
        # Recommendation
        html.Div([
            html.Div("Recommendation", style={
                "color": "#34D399",
                "fontSize": "11px",
                "fontWeight": "600",
                "marginBottom": "4px",
            }),
            html.Div(ap.get("recommendation", ""), style={
                "color": "#8B949E",
                "fontSize": "12px",
                "lineHeight": "1.5",
                "backgroundColor": "rgba(52,211,153,0.05)",
                "padding": "8px 10px",
                "borderRadius": "6px",
                "borderLeft": "3px solid #34D399",
            }),
        ], style={"marginTop": "10px"}),
        # Effort
        html.Div([
            html.Span(f"Effort: {ap.get('effort', 'N/A')}", style={
                "color": "#484F58",
                "fontSize": "11px",
            }),
            html.Span(f" ({ap.get('effort_days', '?')} days)", style={
                "color": "#484F58",
                "fontSize": "11px",
            }) if ap.get("effort_days") else html.Span(),
        ], style={"marginTop": "8px"}),
    ], style={
        "backgroundColor": "var(--surface, #161B22)",
        "borderRadius": "8px",
        "border": f"1px solid {sev_color}33",
        "padding": "16px",
    })


def create_antipattern_grid(anti_patterns: list) -> html.Div:
    """Create a grid of anti-pattern cards."""
    if not anti_patterns:
        return html.Div(
            "No anti-patterns detected. Your CI/CD practices look clean!",
            style={
                "color": "#34D399",
                "textAlign": "center",
                "padding": "40px",
                "fontSize": "14px",
            },
        )

    cards = [create_antipattern_card(ap) for ap in anti_patterns]

    return html.Div(cards, style={
        "display": "grid",
        "gridTemplateColumns": "repeat(auto-fill, minmax(340px, 1fr))",
        "gap": "12px",
    })


def create_antipattern_summary_bar(summary: dict) -> html.Div:
    """Create a summary bar showing anti-pattern counts by severity."""
    items = []
    for sev in ["critical", "high", "medium", "low"]:
        count = summary.get("by_severity", {}).get(sev, 0)
        if count > 0:
            items.append(html.Div([
                html.Span(f"{count}", style={
                    "fontWeight": "700",
                    "fontSize": "18px",
                    "color": SEVERITY_COLORS.get(sev, "#888"),
                }),
                html.Span(f" {sev}", style={
                    "color": "#8B949E",
                    "fontSize": "12px",
                    "textTransform": "capitalize",
                }),
            ], style={"textAlign": "center"}))

    if not items:
        items.append(html.Div("0 detected", style={"color": "#34D399", "fontSize": "14px"}))

    return html.Div(items, style={
        "display": "flex",
        "gap": "24px",
        "justifyContent": "center",
        "padding": "12px",
    })
