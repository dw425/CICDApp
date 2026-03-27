"""Team Drilldown Callbacks - Team selector, radar, gauge, domain details,
deployment table, and coaching recommendations."""

import pandas as pd
import plotly.graph_objects as go
from dash import html, dcc, Input, Output, no_update

from ui.theme import (
    SURFACE, ELEVATED, TEXT, TEXT2, TEXT3, BORDER, ACCENT, GREEN, YELLOW, RED,
    PURPLE, CYAN, CHART_COLORS, TIER_COLORS, get_tier, get_tier_color,
)
from ui.components.gauge import create_gauge
from ui.components.tier_badge import create_tier_badge
from ui.components.data_table import create_data_table


# Domain display names
DOMAIN_LABELS = {
    "golden_path": "Golden Path",
    "environment_promotion": "Environment Promotion",
    "pipeline_reliability": "Pipeline Reliability",
    "data_quality": "Data Quality",
    "security_governance": "Security & Governance",
    "cost_efficiency": "Cost Efficiency",
}

# Domain icons
DOMAIN_ICONS = {
    "golden_path": "fas fa-road",
    "environment_promotion": "fas fa-layer-group",
    "pipeline_reliability": "fas fa-heartbeat",
    "data_quality": "fas fa-check-double",
    "security_governance": "fas fa-shield-alt",
    "cost_efficiency": "fas fa-coins",
}


def _empty_figure(message="Select a team to view details"):
    """Return an empty themed figure with a centered message."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=14, color=TEXT2),
    )
    fig.update_layout(
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=300,
        margin=dict(l=20, r=20, t=20, b=20),
    )
    return fig


def _build_radar(scores, team_name):
    """Build a 6-axis radar chart for domain scores."""
    if scores.empty:
        return _empty_figure("No score data for this team")

    # Get the domains and scores
    domains = []
    values = []
    for _, row in scores.iterrows():
        domain = row.get("domain", "")
        label = DOMAIN_LABELS.get(domain, domain.replace("_", " ").title())
        domains.append(label)
        values.append(row.get("raw_score", 0))

    # Close the radar polygon
    domains_closed = domains + [domains[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=domains_closed,
        fill="toself",
        fillcolor=f"rgba(75,123,245,0.15)",
        line=dict(color=ACCENT, width=2),
        marker=dict(color=ACCENT, size=6),
        name=team_name,
        hovertemplate="<b>%{theta}</b><br>Score: %{r:.0f}<extra></extra>",
    ))

    fig.update_layout(
        polar=dict(
            bgcolor=SURFACE,
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(color=TEXT3, size=10),
                gridcolor=BORDER,
                linecolor=BORDER,
            ),
            angularaxis=dict(
                tickfont=dict(color=TEXT2, size=11),
                gridcolor=BORDER,
                linecolor=BORDER,
            ),
        ),
        paper_bgcolor=SURFACE,
        font=dict(family="DM Sans, Inter, system-ui, sans-serif", color=TEXT2),
        showlegend=False,
        height=320,
        margin=dict(l=60, r=60, t=40, b=40),
    )
    return fig


def _build_domain_detail_cards(scores):
    """Build detailed cards for each domain showing score, tier, and bar."""
    if scores.empty:
        return html.Div("No domain data available", style={"color": TEXT2, "padding": "20px"})

    cards = []
    for _, row in scores.iterrows():
        domain = row.get("domain", "")
        raw_score = row.get("raw_score", 0)
        weighted_score = row.get("weighted_score", 0)
        tier = get_tier(raw_score)
        color = get_tier_color(raw_score)
        label = DOMAIN_LABELS.get(domain, domain.replace("_", " ").title())
        icon = DOMAIN_ICONS.get(domain, "fas fa-chart-bar")

        # Progress bar fill
        bar = html.Div([
            html.Div(
                style={
                    "width": f"{raw_score}%",
                    "height": "6px",
                    "backgroundColor": color,
                    "borderRadius": "3px",
                    "transition": "width 0.5s ease",
                },
            ),
        ], style={
            "width": "100%",
            "height": "6px",
            "backgroundColor": BORDER,
            "borderRadius": "3px",
        })

        card = html.Div([
            html.Div([
                html.Div([
                    html.I(className=icon, style={"color": color, "marginRight": "8px", "fontSize": "14px"}),
                    html.Span(label, style={"color": TEXT, "fontWeight": "600", "fontSize": "14px"}),
                ], style={"display": "flex", "alignItems": "center"}),
                create_tier_badge(raw_score),
            ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "12px"}),

            html.Div([
                html.Span(f"{raw_score:.0f}", style={"color": TEXT, "fontSize": "28px", "fontWeight": "700"}),
                html.Span(f" / 100", style={"color": TEXT3, "fontSize": "14px"}),
            ], style={"marginBottom": "8px"}),

            bar,

            html.Div(
                f"Weighted: {weighted_score:.1f}",
                style={"color": TEXT2, "fontSize": "12px", "marginTop": "8px"},
            ),
        ], style={
            "backgroundColor": ELEVATED,
            "border": f"1px solid {BORDER}",
            "borderRadius": "8px",
            "padding": "16px",
            "flex": "1",
            "minWidth": "200px",
        })
        cards.append(card)

    return html.Div(
        cards,
        style={
            "display": "flex",
            "flexWrap": "wrap",
            "gap": "12px",
        },
    )


def _build_recommendation_cards(alerts, team_lookup):
    """Build coaching recommendation cards from alerts."""
    if alerts.empty:
        return html.Div(
            "No coaching recommendations for this team",
            style={"color": TEXT2, "padding": "20px"},
        )

    severity_colors = {
        "critical": RED,
        "warning": YELLOW,
        "info": ACCENT,
    }
    severity_bg = {
        "critical": "rgba(248,113,113,.10)",
        "warning": "rgba(251,191,36,.10)",
        "info": "rgba(75,123,245,.10)",
    }
    severity_icons = {
        "critical": "fas fa-exclamation-circle",
        "warning": "fas fa-exclamation-triangle",
        "info": "fas fa-info-circle",
    }

    # Sort by severity
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    alerts_sorted = alerts.copy()
    alerts_sorted["_order"] = alerts_sorted["severity"].map(severity_order).fillna(3)
    alerts_sorted = alerts_sorted.sort_values("_order")

    cards = []
    for _, row in alerts_sorted.iterrows():
        sev = str(row.get("severity", "info")).lower()
        color = severity_colors.get(sev, TEXT2)
        bg = severity_bg.get(sev, "rgba(255,255,255,.04)")
        icon = severity_icons.get(sev, "fas fa-info-circle")
        domain = str(row.get("domain", "")).replace("_", " ").title()
        message = str(row.get("message", ""))
        recommendation = str(row.get("recommendation", ""))

        card = html.Div([
            html.Div([
                html.I(className=icon, style={"color": color, "marginRight": "8px"}),
                html.Span(sev.upper(), style={
                    "color": color,
                    "fontWeight": "700",
                    "fontSize": "11px",
                    "letterSpacing": "0.5px",
                }),
                html.Span(f" \u2014 {domain}", style={"color": TEXT2, "fontSize": "12px", "marginLeft": "8px"}),
            ], style={"display": "flex", "alignItems": "center", "marginBottom": "8px"}),

            html.Div(message, style={"color": TEXT, "fontSize": "14px", "fontWeight": "500", "marginBottom": "8px"}),

            html.Div([
                html.I(className="fas fa-lightbulb", style={"color": YELLOW, "marginRight": "6px", "fontSize": "12px"}),
                html.Span(recommendation, style={"color": TEXT2, "fontSize": "13px"}),
            ], style={"display": "flex", "alignItems": "flex-start"}),
        ], style={
            "backgroundColor": bg,
            "border": f"1px solid {BORDER}",
            "borderLeft": f"3px solid {color}",
            "borderRadius": "6px",
            "padding": "16px",
            "marginBottom": "10px",
        })
        cards.append(card)

    return html.Div(cards)


def register_callbacks(app):
    """Register Team Drilldown callbacks."""

    # ── Callback 1: Populate team selector ─────────────────────────
    @app.callback(
        Output("team-selector", "options"),
        Input("current-page", "data"),
    )
    def populate_team_selector(current_page):
        """Load team options when the team page is active."""
        if current_page != "team":
            return no_update

        try:
            from data_layer.queries.custom_tables import get_teams
            teams = get_teams()
            if teams.empty:
                return []
            return [
                {"label": row["team_name"], "value": row["team_id"]}
                for _, row in teams.iterrows()
            ]
        except Exception:
            return []

    # ── Callback 2: Update team details ────────────────────────────
    @app.callback(
        [
            Output("team-radar", "figure"),
            Output("team-gauge-container", "children"),
            Output("team-domain-details", "children"),
            Output("team-deployment-table", "children"),
            Output("team-recommendations", "children"),
        ],
        [
            Input("team-selector", "value"),
        ],
    )
    def update_team_details(team_id):
        """Update all team drilldown visuals when a team is selected."""
        if not team_id:
            return [
                _empty_figure("Select a team to view details"),
                html.Div("Select a team", style={"color": TEXT2, "padding": "40px", "textAlign": "center"}),
                html.Div("Select a team to view domain details", style={"color": TEXT2, "padding": "20px"}),
                html.Div("Select a team to view deployments", style={"color": TEXT2, "padding": "20px"}),
                html.Div("Select a team to view recommendations", style={"color": TEXT2, "padding": "20px"}),
            ]

        try:
            from data_layer.queries.custom_tables import (
                get_teams,
                get_maturity_scores,
                get_deployment_events,
                get_coaching_alerts,
            )

            teams = get_teams()
            team_lookup = dict(zip(teams["team_id"], teams["team_name"]))
            team_name = team_lookup.get(team_id, team_id)

            # Load team-specific data
            scores = get_maturity_scores(team_id=team_id, latest=True)
            deployments = get_deployment_events(team_id=team_id)
            alerts = get_coaching_alerts(team_id=team_id)

            # ── Radar chart ────────────────────────────────────
            radar_fig = _build_radar(scores, team_name)

            # ── Gauge ──────────────────────────────────────────
            if not scores.empty and "composite_score" in scores.columns:
                composite = scores["composite_score"].iloc[0]
                gauge = create_gauge(
                    score=composite,
                    title=f"{team_name} Composite",
                    gauge_id="team-gauge",
                )
            else:
                gauge = html.Div("No composite score", style={"color": TEXT2, "padding": "40px", "textAlign": "center"})

            # ── Domain details ─────────────────────────────────
            domain_details = _build_domain_detail_cards(scores)

            # ── Deployment table ───────────────────────────────
            if not deployments.empty:
                display_cols = [
                    {"name": "Date", "id": "event_date"},
                    {"name": "Actor", "id": "actor_type"},
                    {"name": "Golden Path", "id": "is_golden_path"},
                    {"name": "Artifact", "id": "artifact_type"},
                    {"name": "Environment", "id": "environment"},
                    {"name": "Status", "id": "status"},
                ]
                deploy_table = create_data_table(
                    deployments,
                    table_id="team-deploy-dt",
                    page_size=8,
                    columns=display_cols,
                )
            else:
                deploy_table = html.Div("No deployment events", style={"color": TEXT2, "padding": "20px"})

            # ── Recommendations ────────────────────────────────
            recommendations = _build_recommendation_cards(alerts, team_lookup)

            return [radar_fig, gauge, domain_details, deploy_table, recommendations]

        except Exception as e:
            error_msg = html.Div(
                f"Error loading team data: {str(e)}",
                style={"color": RED, "padding": "20px"},
            )
            return [
                _empty_figure(f"Error: {str(e)}"),
                error_msg,
                error_msg,
                error_msg,
                error_msg,
            ]
