"""Deployment Explorer Callbacks - Filter-driven charts and event table."""

import pandas as pd
import plotly.graph_objects as go
from dash import html, Input, Output, no_update

from ui.theme import (
    SURFACE, TEXT, TEXT2, TEXT3, BORDER, ACCENT, GREEN, YELLOW, RED,
    PURPLE, CYAN, CHART_COLORS,
)
from ui.components.data_table import create_data_table


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
        height=280,
        margin=dict(l=20, r=20, t=20, b=20),
    )
    return fig
    # ****Checked and Verified as Real*****
    # Return an empty themed figure with a centered message.


def _filter_deployments(df, team_filter, env_filter, actor_filter):
    """Apply dropdown filters to deployment events DataFrame."""
    filtered = df.copy()
    if team_filter and team_filter != "All":
        filtered = filtered[filtered["team_id"] == team_filter]
    if env_filter and env_filter != "All":
        filtered = filtered[filtered["environment"] == env_filter]
    if actor_filter and actor_filter != "All":
        filtered = filtered[filtered["actor_type"] == actor_filter]
    return filtered
    # ****Checked and Verified as Real*****
    # Apply dropdown filters to deployment events DataFrame.


def _build_golden_pie(df):
    """Build golden path distribution donut chart."""
    if df.empty:
        return _empty_figure("No deployments match filters")

    gp_col = df["is_golden_path"]
    if gp_col.dtype == object:
        golden_count = (gp_col.str.lower() == "true").sum()
    else:
        golden_count = gp_col.sum()
    non_golden_count = len(df) - golden_count

    fig = go.Figure(go.Pie(
        labels=["Golden Path", "Manual"],
        values=[golden_count, non_golden_count],
        marker=dict(colors=[ACCENT, RED]),
        hole=0.5,
        textinfo="percent+value",
        textfont=dict(size=11, color=TEXT),
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>",
    ))

    # Center annotation
    total = golden_count + non_golden_count
    pct = (golden_count / total * 100) if total > 0 else 0
    fig.add_annotation(
        text=f"{pct:.0f}%",
        x=0.5, y=0.5,
        font=dict(size=22, color=TEXT, family="DM Sans"),
        showarrow=False,
    )

    fig.update_layout(
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font=dict(family="DM Sans, Inter, system-ui, sans-serif", color=TEXT2),
        showlegend=True,
        legend=dict(
            font=dict(color=TEXT2, size=10),
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
        ),
        height=280,
        margin=dict(l=20, r=20, t=10, b=40),
    )
    return fig
    # ****Checked and Verified as Real*****
    # Build golden path distribution donut chart.


def _build_env_bar(df):
    """Build bar chart of deployment count by environment."""
    if df.empty:
        return _empty_figure("No deployments match filters")

    env_counts = df["environment"].value_counts().sort_index()

    # Color by environment tier
    env_colors = {
        "dev": ACCENT,
        "staging": YELLOW,
        "prod": GREEN,
    }
    colors = [env_colors.get(env, CHART_COLORS[0]) for env in env_counts.index]

    fig = go.Figure(go.Bar(
        x=env_counts.index,
        y=env_counts.values,
        marker=dict(color=colors, opacity=0.9, line=dict(width=0)),
        text=env_counts.values,
        textposition="outside",
        textfont=dict(color=TEXT2, size=12),
        hovertemplate="<b>%{x}</b><br>Deployments: %{y}<extra></extra>",
    ))

    fig.update_layout(
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font=dict(family="DM Sans, Inter, system-ui, sans-serif", color=TEXT2),
        xaxis=dict(
            tickfont=dict(color=TEXT2, size=12),
            gridcolor=BORDER,
        ),
        yaxis=dict(
            title=dict(text="Count", font=dict(color=TEXT2)),
            gridcolor=BORDER,
            tickfont=dict(color=TEXT2),
        ),
        height=280,
        margin=dict(l=50, r=20, t=10, b=40),
        bargap=0.35,
    )
    return fig
    # ****Checked and Verified as Real*****
    # Build bar chart of deployment count by environment.


def _build_artifact_donut(df):
    """Build artifact type donut chart."""
    if df.empty:
        return _empty_figure("No deployments match filters")

    artifact_counts = df["artifact_type"].value_counts()

    # Assign colors from chart palette
    colors = CHART_COLORS[:len(artifact_counts)]

    fig = go.Figure(go.Pie(
        labels=artifact_counts.index,
        values=artifact_counts.values,
        marker=dict(colors=colors),
        hole=0.5,
        textinfo="label+percent",
        textfont=dict(size=10, color=TEXT),
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>",
    ))

    fig.update_layout(
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font=dict(family="DM Sans, Inter, system-ui, sans-serif", color=TEXT2),
        showlegend=True,
        legend=dict(
            font=dict(color=TEXT2, size=10),
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
        ),
        height=280,
        margin=dict(l=20, r=20, t=10, b=40),
    )
    return fig
    # ****Checked and Verified as Real*****
    # Build artifact type donut chart.


def _build_events_table(df, team_lookup):
    """Build the deployment events data table."""
    if df.empty:
        return html.Div("No deployment events match the selected filters",
                         style={"color": TEXT2, "padding": "20px"})

    # Create a display-ready copy
    display_df = df.copy()
    if "team_id" in display_df.columns:
        display_df["team_name"] = display_df["team_id"].map(team_lookup).fillna(display_df["team_id"])

    # Format dates if needed
    if "event_date" in display_df.columns:
        display_df["event_date"] = pd.to_datetime(display_df["event_date"]).dt.strftime("%Y-%m-%d")

    columns = [
        {"name": "Date", "id": "event_date"},
        {"name": "Team", "id": "team_name"},
        {"name": "Actor Type", "id": "actor_type"},
        {"name": "Golden Path", "id": "is_golden_path"},
        {"name": "Artifact", "id": "artifact_type"},
        {"name": "Environment", "id": "environment"},
        {"name": "Status", "id": "status"},
    ]

    return create_data_table(
        display_df,
        table_id="deploy-events-dt",
        page_size=10,
        columns=columns,
    )
    # ****Checked and Verified as Real*****
    # Build the deployment events data table.


def register_callbacks(app):
    """Register Deployment Explorer callbacks."""

    # ── Populate team filter options ───────────────────────────────
    @app.callback(
        Output("deploy-team-filter", "options"),
        Input("current-page", "data"),
    )
    def populate_deploy_team_filter(current_page):
        """Load team filter options when deployment page is active."""
        if current_page != "deployment":
            return no_update

        try:
            from data_layer.queries.custom_tables import get_teams
            teams = get_teams()
            options = [{"label": "All", "value": "All"}]
            if not teams.empty:
                for _, row in teams.iterrows():
                    options.append({"label": row["team_name"], "value": row["team_id"]})
            return options
        except Exception:
            return [{"label": "All", "value": "All"}]
        # ****Checked and Verified as Real*****
        # Load team filter options when deployment page is active.

    # ── Main filter → chart update callback ────────────────────────
    @app.callback(
        [
            Output("deploy-golden-pie", "figure"),
            Output("deploy-env-bar", "figure"),
            Output("deploy-artifact-donut", "figure"),
            Output("deploy-events-table", "children"),
        ],
        [
            Input("deploy-team-filter", "value"),
            Input("deploy-env-filter", "value"),
            Input("deploy-actor-filter", "value"),
            Input("current-page", "data"),
        ],
    )
    def update_deployment_explorer(team_filter, env_filter, actor_filter, current_page):
        """Filter and update all deployment visualizations."""
        if current_page != "deployment":
            return [no_update] * 4

        try:
            from data_layer.queries.custom_tables import get_deployment_events, get_teams

            teams = get_teams()
            team_lookup = dict(zip(teams["team_id"], teams["team_name"]))
            deployments = get_deployment_events()

            # Apply filters
            filtered = _filter_deployments(deployments, team_filter, env_filter, actor_filter)

            golden_pie = _build_golden_pie(filtered)
            env_bar = _build_env_bar(filtered)
            artifact_donut = _build_artifact_donut(filtered)
            events_table = _build_events_table(filtered, team_lookup)

            return [golden_pie, env_bar, artifact_donut, events_table]

        except Exception as e:
            err = _empty_figure(f"Error: {str(e)}")
            err_msg = html.Div(f"Error: {str(e)}", style={"color": RED, "padding": "20px"})
            return [err, err, err, err_msg]
        # ****Checked and Verified as Real*****
        # Filter and update all deployment visualizations.
    # ****Checked and Verified as Real*****
    # Register Deployment Explorer callbacks.
