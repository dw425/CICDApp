"""Roadmap Timeline — Phased improvement timeline visualization."""

from dash import html


PHASE_COLORS = {
    "30d": "#34D399",
    "90d": "#4B7BF5",
    "6mo": "#FBBF24",
    "12mo": "#8B949E",
}

PHASE_ICONS = {
    "30d": "fas fa-bolt",
    "90d": "fas fa-chess",
    "6mo": "fas fa-layer-group",
    "12mo": "fas fa-road",
}


def create_roadmap_timeline(phases: list) -> html.Div:
    """
    Create a visual timeline of improvement phases.

    Args:
        phases: List of phase dicts from roadmap_engine.assign_phases.
    """
    if not phases:
        return html.Div("No roadmap items generated.", style={
            "color": "#8B949E", "textAlign": "center", "padding": "40px",
        })

    phase_sections = []
    for phase in phases:
        horizon = phase.get("horizon", "30d")
        color = PHASE_COLORS.get(horizon, "#8B949E")
        icon = PHASE_ICONS.get(horizon, "fas fa-circle")
        items = phase.get("items", [])

        if not items:
            continue

        item_cards = []
        for item in items:
            boosted = item.get("boosted_by_antipattern", False)
            item_cards.append(html.Div([
                html.Div([
                    html.Span(item.get("title", ""), style={
                        "color": "#E6EDF3",
                        "fontSize": "13px",
                        "fontWeight": "600",
                    }),
                    html.Span(
                        "AP" if boosted else "",
                        style={
                            "display": "inline-block" if boosted else "none",
                            "padding": "0 5px",
                            "borderRadius": "3px",
                            "backgroundColor": "#EF444433",
                            "color": "#EF4444",
                            "fontSize": "9px",
                            "fontWeight": "700",
                            "marginLeft": "6px",
                        },
                    ),
                ], style={"display": "flex", "alignItems": "center"}),
                html.Div(item.get("description", ""), style={
                    "color": "#8B949E",
                    "fontSize": "11px",
                    "marginTop": "4px",
                    "lineHeight": "1.4",
                }),
                html.Div([
                    html.Span(
                        f"Impact: {item.get('impact', 'N/A')}",
                        style={"color": "#484F58", "fontSize": "10px"},
                    ),
                    html.Span(" | ", style={"color": "#272D3F"}),
                    html.Span(
                        f"Effort: {item.get('effort_days', '?')}d",
                        style={"color": "#484F58", "fontSize": "10px"},
                    ),
                    html.Span(" | ", style={"color": "#272D3F"}),
                    html.Span(
                        f"+{item.get('expected_score_improvement', 0)} pts",
                        style={"color": "#34D399", "fontSize": "10px"},
                    ),
                ], style={"marginTop": "6px"}),
                # Tools
                html.Div([
                    html.Span(tool, style={
                        "display": "inline-block",
                        "padding": "1px 6px",
                        "borderRadius": "3px",
                        "backgroundColor": "var(--elevated, #21262D)",
                        "color": "#8B949E",
                        "fontSize": "10px",
                        "marginRight": "4px",
                    })
                    for tool in item.get("tools", [])[:3]
                ], style={"marginTop": "6px"}) if item.get("tools") else html.Div(),
            ], style={
                "backgroundColor": "var(--elevated, #21262D)",
                "borderRadius": "6px",
                "padding": "12px",
                "borderLeft": f"3px solid {color}",
            }))

        phase_sections.append(html.Div([
            # Phase header
            html.Div([
                html.Div(style={
                    "width": "32px",
                    "height": "32px",
                    "borderRadius": "50%",
                    "backgroundColor": f"{color}22",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                }, children=[
                    html.I(className=icon, style={"color": color, "fontSize": "14px"}),
                ]),
                html.Div([
                    html.Div(phase["name"], style={
                        "color": "#E6EDF3",
                        "fontSize": "15px",
                        "fontWeight": "700",
                    }),
                    html.Div(phase.get("description", ""), style={
                        "color": "#8B949E",
                        "fontSize": "11px",
                    }),
                ]),
                html.Span(f"{len(items)} items", style={
                    "color": "#484F58",
                    "fontSize": "11px",
                    "marginLeft": "auto",
                }),
            ], style={
                "display": "flex",
                "alignItems": "center",
                "gap": "12px",
                "marginBottom": "12px",
            }),
            # Items
            html.Div(item_cards, style={
                "display": "flex",
                "flexDirection": "column",
                "gap": "8px",
                "marginLeft": "16px",
                "borderLeft": f"2px solid {color}33",
                "paddingLeft": "16px",
            }),
        ], style={"marginBottom": "24px"}))

    return html.Div(phase_sections)
