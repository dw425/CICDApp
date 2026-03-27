"""Executive Summary Callbacks - KPI cards, charts, and alerts table."""

import pandas as pd
import plotly.graph_objects as go
from dash import html, Input, Output, no_update

from ui.theme import (
    SURFACE, TEXT, TEXT2, BORDER, ACCENT, GREEN, YELLOW, RED, PURPLE, CYAN,
    CHART_COLORS, get_tier, get_tier_color,
)
from ui.components.kpi_card import create_kpi_card
from ui.components.tier_badge import create_tier_badge


def _empty_figure(message="No data available"):
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


def _build_golden_pie(deployment_events):
    """Build golden path distribution pie chart."""
    if deployment_events.empty:
        return _empty_figure("No deployment data")

    # Handle both string and boolean is_golden_path column
    gp_col = deployment_events["is_golden_path"]
    if gp_col.dtype == object:
        golden_count = (gp_col.str.lower() == "true").sum()
    else:
        golden_count = gp_col.sum()
    non_golden_count = len(deployment_events) - golden_count

    fig = go.Figure(go.Pie(
        labels=["Golden Path", "Non-Golden Path"],
        values=[golden_count, non_golden_count],
        marker=dict(colors=[ACCENT, RED]),
        hole=0.45,
        textinfo="label+percent",
        textfont=dict(size=12, color=TEXT),
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font=dict(family="DM Sans, Inter, system-ui, sans-serif", color=TEXT2),
        showlegend=True,
        legend=dict(
            font=dict(color=TEXT2, size=11),
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5,
        ),
        height=300,
        margin=dict(l=20, r=20, t=20, b=40),
    )
    return fig


def _build_heatmap(maturity_scores, teams):
    """Build team maturity heatmap: teams (y) x domains (x) with score colors."""
    if maturity_scores.empty:
        return _empty_figure("No maturity score data")

    # Create team_id → team_name lookup
    team_lookup = dict(zip(teams["team_id"], teams["team_name"]))

    # Pivot: rows = teams, columns = domains, values = raw_score
    pivot = maturity_scores.pivot_table(
        index="team_id",
        columns="domain",
        values="raw_score",
        aggfunc="mean",
    )

    # Map team_id to team_name for display
    team_names = [team_lookup.get(tid, tid) for tid in pivot.index]
    domain_names = [d.replace("_", " ").title() for d in pivot.columns]

    # Custom colorscale: RED → YELLOW → GREEN
    colorscale = [
        [0.0, RED],
        [0.5, YELLOW],
        [1.0, GREEN],
    ]

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=domain_names,
        y=team_names,
        colorscale=colorscale,
        zmin=0,
        zmax=100,
        text=[[f"{v:.0f}" for v in row] for row in pivot.values],
        texttemplate="%{text}",
        textfont=dict(size=12, color=TEXT),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Domain: %{x}<br>"
            "Score: %{z:.1f}<extra></extra>"
        ),
        colorbar=dict(
            title=dict(text="Score", font=dict(color=TEXT2)),
            tickfont=dict(color=TEXT2),
            bordercolor=BORDER,
        ),
    ))
    fig.update_layout(
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font=dict(family="DM Sans, Inter, system-ui, sans-serif", color=TEXT2),
        xaxis=dict(
            tickfont=dict(color=TEXT2, size=10),
            tickangle=45,
            side="bottom",
        ),
        yaxis=dict(
            tickfont=dict(color=TEXT2, size=11),
            autorange="reversed",
        ),
        height=320,
        margin=dict(l=140, r=20, t=20, b=80),
    )
    return fig


def _build_trend_line(maturity_trends, teams):
    """Build composite score trend line chart per team."""
    if maturity_trends.empty:
        return _empty_figure("No trend data")

    team_lookup = dict(zip(teams["team_id"], teams["team_name"]))

    fig = go.Figure()
    team_ids = maturity_trends["team_id"].unique()
    for i, team_id in enumerate(sorted(team_ids)):
        team_data = maturity_trends[maturity_trends["team_id"] == team_id].sort_values("period_start")
        team_name = team_lookup.get(team_id, team_id)
        color = CHART_COLORS[i % len(CHART_COLORS)]

        fig.add_trace(go.Scatter(
            x=team_data["period_start"],
            y=team_data["avg_score"],
            mode="lines+markers",
            name=team_name,
            line=dict(color=color, width=2),
            marker=dict(color=color, size=6),
            hovertemplate=(
                f"<b>{team_name}</b><br>"
                "Period: %{x}<br>"
                "Score: %{y:.1f}<extra></extra>"
            ),
        ))

    fig.update_layout(
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font=dict(family="DM Sans, Inter, system-ui, sans-serif", color=TEXT2),
        xaxis=dict(
            title=dict(text="Week", font=dict(color=TEXT2)),
            gridcolor=BORDER,
            tickfont=dict(color=TEXT2),
        ),
        yaxis=dict(
            title=dict(text="Composite Score", font=dict(color=TEXT2)),
            gridcolor=BORDER,
            tickfont=dict(color=TEXT2),
            range=[0, 100],
        ),
        legend=dict(
            font=dict(color=TEXT2, size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        height=300,
        margin=dict(l=50, r=20, t=20, b=50),
        hovermode="x unified",
    )
    return fig


def _build_alerts_table(coaching_alerts, teams):
    """Build an HTML alerts table with severity badges."""
    if coaching_alerts.empty:
        return html.Div("No active alerts", style={"color": TEXT2, "padding": "20px"})

    team_lookup = dict(zip(teams["team_id"], teams["team_name"]))

    # Severity color mapping
    severity_colors = {
        "critical": RED,
        "warning": YELLOW,
        "info": ACCENT,
    }
    severity_bg = {
        "critical": "rgba(248,113,113,.15)",
        "warning": "rgba(251,191,36,.15)",
        "info": "rgba(75,123,245,.15)",
    }

    # Sort by severity (critical first) and date (newest first)
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    alerts_sorted = coaching_alerts.copy()
    alerts_sorted["_order"] = alerts_sorted["severity"].map(severity_order).fillna(3)
    alerts_sorted = alerts_sorted.sort_values(["_order", "created_date"], ascending=[True, False])

    # Limit to most recent 10
    alerts_sorted = alerts_sorted.head(10)

    # Build table rows
    rows = []
    for _, row in alerts_sorted.iterrows():
        sev = str(row.get("severity", "info")).lower()
        team_name = team_lookup.get(row.get("team_id", ""), row.get("team_id", ""))
        message = str(row.get("message", ""))
        recommendation = str(row.get("recommendation", ""))
        domain = str(row.get("domain", "")).replace("_", " ").title()

        severity_badge = html.Span(
            sev.upper(),
            style={
                "background": severity_bg.get(sev, "rgba(255,255,255,.06)"),
                "color": severity_colors.get(sev, TEXT2),
                "padding": "3px 8px",
                "borderRadius": "4px",
                "fontSize": "10px",
                "fontWeight": "600",
                "letterSpacing": "0.5px",
            },
        )

        rows.append(html.Tr([
            html.Td(severity_badge, style={"padding": "10px 14px", "borderBottom": f"1px solid {BORDER}"}),
            html.Td(team_name, style={"padding": "10px 14px", "borderBottom": f"1px solid {BORDER}", "color": TEXT, "fontSize": "13px"}),
            html.Td(domain, style={"padding": "10px 14px", "borderBottom": f"1px solid {BORDER}", "color": TEXT2, "fontSize": "13px"}),
            html.Td(message, style={"padding": "10px 14px", "borderBottom": f"1px solid {BORDER}", "color": TEXT, "fontSize": "13px"}),
        ]))

    header = html.Thead(html.Tr([
        html.Th(col, style={
            "padding": "10px 14px",
            "color": TEXT2,
            "fontSize": "11px",
            "fontWeight": "600",
            "textTransform": "uppercase",
            "letterSpacing": "0.5px",
            "borderBottom": f"2px solid {BORDER}",
            "textAlign": "left",
        })
        for col in ["Severity", "Team", "Domain", "Message"]
    ]))

    return html.Table(
        [header, html.Tbody(rows)],
        style={
            "width": "100%",
            "borderCollapse": "collapse",
            "backgroundColor": SURFACE,
        },
    )


def register_callbacks(app):
    """Register Executive Summary callbacks."""

    @app.callback(
        [
            Output("kpi-composite", "children"),
            Output("kpi-golden-path", "children"),
            Output("kpi-pipeline", "children"),
            Output("kpi-teams", "children"),
            Output("exec-golden-pie", "figure"),
            Output("exec-heatmap", "figure"),
            Output("exec-trend-line", "figure"),
            Output("exec-alerts-table", "children"),
        ],
        [
            Input("current-page", "data"),
            Input("refresh-btn", "n_clicks"),
        ],
    )
    def update_executive_dashboard(current_page, n_clicks):
        """Populate all Executive Summary visuals."""
        if current_page != "executive":
            return [no_update] * 8

        try:
            from data_layer.queries.custom_tables import (
                get_teams,
                get_maturity_scores,
                get_deployment_events,
                get_maturity_trends,
                get_coaching_alerts,
            )

            teams = get_teams()
            scores = get_maturity_scores(latest=True)
            deployments = get_deployment_events()
            trends = get_maturity_trends()
            alerts = get_coaching_alerts()

            # ── KPI 1: Composite Score ─────────────────────────────
            if not scores.empty and "composite_score" in scores.columns:
                # Get the average composite score (one per team)
                composite_avg = scores.groupby("team_id")["composite_score"].first().mean()
                composite_val = f"{composite_avg:.1f}"
                # Compute delta from trends if available
                composite_delta = None
                delta_dir = "neutral"
                if not trends.empty:
                    latest_deltas = trends.sort_values("period_start").groupby("team_id").last()
                    if "delta" in latest_deltas.columns:
                        avg_delta = latest_deltas["delta"].mean()
                        composite_delta = f"{avg_delta:+.1f}"
                        delta_dir = "positive" if avg_delta > 0 else "negative" if avg_delta < 0 else "neutral"
            else:
                composite_val = "--"
                composite_delta = None
                delta_dir = "neutral"

            kpi_composite = create_kpi_card(
                label="Composite Score",
                value=composite_val,
                delta=composite_delta,
                delta_direction=delta_dir,
                color="blue",
            )

            # ── KPI 2: Golden Path % ──────────────────────────────
            if not deployments.empty and "is_golden_path" in deployments.columns:
                gp_col = deployments["is_golden_path"]
                if gp_col.dtype == object:
                    golden_count = (gp_col.str.lower() == "true").sum()
                else:
                    golden_count = gp_col.sum()
                gp_pct = (golden_count / len(deployments)) * 100
                gp_val = f"{gp_pct:.0f}%"
            else:
                gp_val = "--"

            kpi_golden = create_kpi_card(
                label="Golden Path %",
                value=gp_val,
                color="green",
            )

            # ── KPI 3: Pipeline Success % ─────────────────────────
            if not scores.empty and "domain" in scores.columns:
                pipeline_scores = scores[scores["domain"] == "pipeline_reliability"]
                if not pipeline_scores.empty:
                    pipeline_avg = pipeline_scores["raw_score"].mean()
                    pipeline_val = f"{pipeline_avg:.0f}%"
                else:
                    pipeline_val = "--"
            else:
                pipeline_val = "--"

            kpi_pipeline = create_kpi_card(
                label="Pipeline Success %",
                value=pipeline_val,
                color="purple",
            )

            # ── KPI 4: Active Teams ───────────────────────────────
            team_count = len(teams) if not teams.empty else 0
            kpi_teams = create_kpi_card(
                label="Active Teams",
                value=str(team_count),
                color="cyan",
            )

            # ── Charts ────────────────────────────────────────────
            golden_pie = _build_golden_pie(deployments)
            heatmap = _build_heatmap(scores, teams)
            trend_line = _build_trend_line(trends, teams)
            alerts_table = _build_alerts_table(alerts, teams)

            return [
                kpi_composite,
                kpi_golden,
                kpi_pipeline,
                kpi_teams,
                golden_pie,
                heatmap,
                trend_line,
                alerts_table,
            ]

        except Exception as e:
            # Return safe fallbacks on error
            error_kpi = create_kpi_card(label="Error", value="--", color="red")
            error_msg = html.Div(
                f"Error loading data: {str(e)}",
                style={"color": RED, "padding": "20px"},
            )
            return [
                error_kpi,
                error_kpi,
                error_kpi,
                error_kpi,
                _empty_figure(f"Error: {str(e)}"),
                _empty_figure(f"Error: {str(e)}"),
                _empty_figure(f"Error: {str(e)}"),
                error_msg,
            ]
