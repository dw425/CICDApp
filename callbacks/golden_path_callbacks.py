"""Golden Path Adoption Callbacks — Populates all visuals on the adoption page."""

import plotly.graph_objects as go
from dash import html, Input, Output, no_update, dash_table

from ui.theme import SURFACE, ELEVATED, TEXT, TEXT2, TEXT3, BORDER, ACCENT, GREEN, YELLOW, RED


def _empty_figure(message="No data available", height=300):
    fig = go.Figure()
    fig.add_annotation(text=message, xref="paper", yref="paper", x=0.5, y=0.5,
                       showarrow=False, font=dict(size=14, color=TEXT2))
    fig.update_layout(paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
                      xaxis=dict(visible=False), yaxis=dict(visible=False),
                      height=height, margin=dict(l=20, r=20, t=20, b=20))
    return fig


def _kpi_card(title, value, subtitle="", color=TEXT):
    return html.Div([
        html.P(title, style={"color": TEXT2, "fontSize": "12px", "margin": "0 0 4px 0"}),
        html.H3(value, style={"color": color, "margin": "0 0 2px 0", "fontSize": "28px"}),
        html.P(subtitle, style={"color": TEXT3, "fontSize": "11px", "margin": 0}),
    ], style={
        "backgroundColor": ELEVATED,
        "border": f"1px solid {BORDER}",
        "borderRadius": "8px",
        "padding": "16px 20px",
        "flex": "1",
    })


def register_callbacks(app):
    """Register Golden Path Adoption callbacks."""

    @app.callback(
        [
            Output("gp-kpi-row", "children"),
            Output("gp-adoption-pie", "figure"),
            Output("gp-trend-chart", "figure"),
            Output("gp-artifact-chart", "figure"),
            Output("gp-team-heatmap", "figure"),
            Output("gp-leaderboard", "children"),
            Output("gp-violations-table", "children"),
            Output("gp-coaching-queue", "children"),
        ],
        [Input("current-page", "data"), Input("gp-time-range", "value")],
    )
    def update_golden_path(current_page, time_range):
        if current_page != "golden_path":
            return [no_update] * 8

        try:
            from ingestion.golden_path_classifier import GoldenPathClassifier
            from data_layer.queries.custom_tables import get_deployment_events, get_teams

            teams_df = get_teams()
            team_lookup = dict(zip(teams_df["team_id"], teams_df["team_name"])) if not teams_df.empty else {}
            events_df = get_deployment_events()

            if events_df.empty:
                empty = _empty_figure("No deployment events found")
                return [
                    [_kpi_card("Total Deployments", "0"), _kpi_card("Adoption Rate", "—"),
                     _kpi_card("Standard", "0", color=GREEN), _kpi_card("Non-Standard", "0", color=RED)],
                    empty, empty, empty, empty,
                    html.P("No data", style={"color": TEXT2}),
                    html.P("No data", style={"color": TEXT2}),
                    html.P("No data", style={"color": TEXT2}),
                ]

            # Classify events
            classifier = GoldenPathClassifier(team_registry={
                tid: [] for tid in team_lookup
            })
            events = events_df.to_dict("records")
            classified = classifier.classify_batch(events)
            metrics = classifier.compute_adoption_metrics(classified)

            # KPIs
            kpis = [
                _kpi_card("Total Deployments", str(metrics["total_deployments"])),
                _kpi_card("Adoption Rate", f"{metrics['adoption_pct']:.0f}%",
                           color=GREEN if metrics["adoption_pct"] >= 80 else YELLOW if metrics["adoption_pct"] >= 50 else RED),
                _kpi_card("Standard", str(metrics["standard_count"]), color=GREEN),
                _kpi_card("Non-Standard", str(metrics["non_standard_count"]), color=RED),
            ]

            # Adoption Pie
            pie = go.Figure(go.Pie(
                labels=["Standard", "Non-Standard", "Unknown"],
                values=[metrics["standard_count"], metrics["non_standard_count"], metrics["unknown_count"]],
                marker=dict(colors=[GREEN, RED, TEXT3]),
                hole=0.5,
                textinfo="percent+value",
                textfont=dict(color=TEXT, size=12),
            ))
            pie.update_layout(paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
                              font=dict(color=TEXT2), height=300,
                              margin=dict(l=20, r=20, t=20, b=20),
                              legend=dict(font=dict(color=TEXT2, size=11)))

            # Trend chart
            trend_data = metrics.get("trend", [])
            trend = go.Figure()
            if trend_data:
                trend.add_trace(go.Scatter(
                    x=[t["date"] for t in trend_data],
                    y=[t["adoption_pct"] for t in trend_data],
                    mode="lines+markers",
                    line=dict(color=GREEN, width=2.5),
                    marker=dict(size=6),
                    fill="tozeroy",
                    fillcolor="rgba(34,197,94,0.1)",
                    hovertemplate="Week of %{x}<br>Adoption: %{y:.1f}%<extra></extra>",
                ))
                trend.add_hline(y=80, line_dash="dot", line_color=YELLOW, line_width=1,
                                annotation_text="Target: 80%", annotation_position="top left",
                                annotation_font=dict(color=YELLOW, size=10))
            trend.update_layout(
                paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
                font=dict(color=TEXT2), height=300,
                margin=dict(l=50, r=30, t=20, b=40),
                xaxis=dict(gridcolor=BORDER, tickfont=dict(color=TEXT2)),
                yaxis=dict(gridcolor=BORDER, tickfont=dict(color=TEXT2),
                           title=dict(text="Adoption %"), range=[0, 100]),
            )

            # Artifact type breakdown
            art_data = metrics.get("by_artifact_type", {})
            artifact = go.Figure()
            if art_data:
                types = sorted(art_data.keys())
                std_vals = [art_data[t]["standard"] for t in types]
                nonstd_vals = [art_data[t]["non_standard"] for t in types]
                artifact.add_trace(go.Bar(x=types, y=std_vals, name="Standard", marker_color=GREEN))
                artifact.add_trace(go.Bar(x=types, y=nonstd_vals, name="Non-Standard", marker_color=RED))
            artifact.update_layout(
                paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
                font=dict(color=TEXT2), height=300, barmode="stack",
                margin=dict(l=40, r=20, t=20, b=60),
                legend=dict(font=dict(color=TEXT2, size=11), bgcolor="rgba(0,0,0,0)"),
                xaxis=dict(gridcolor=BORDER, tickfont=dict(color=TEXT2, size=10)),
                yaxis=dict(gridcolor=BORDER, tickfont=dict(color=TEXT2)),
            )

            # Team heatmap
            team_data = metrics.get("by_team", {})
            heatmap = _empty_figure("Configure teams for heatmap", 300)
            if team_data:
                team_names = [team_lookup.get(tid, tid) for tid in sorted(team_data.keys())]
                adoption_vals = [team_data[tid]["adoption_pct"] for tid in sorted(team_data.keys())]
                heatmap = go.Figure(go.Bar(
                    x=team_names, y=adoption_vals,
                    marker=dict(color=[GREEN if v >= 80 else YELLOW if v >= 50 else RED for v in adoption_vals]),
                    text=[f"{v:.0f}%" for v in adoption_vals],
                    textposition="outside", textfont=dict(color=TEXT2, size=11),
                ))
                heatmap.add_hline(y=80, line_dash="dot", line_color=YELLOW, line_width=1)
                heatmap.update_layout(
                    paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
                    font=dict(color=TEXT2), height=300,
                    margin=dict(l=40, r=20, t=20, b=60),
                    yaxis=dict(range=[0, 105], gridcolor=BORDER, tickfont=dict(color=TEXT2)),
                    xaxis=dict(gridcolor=BORDER, tickfont=dict(color=TEXT2, size=10)),
                )

            # Leaderboard
            sorted_teams = sorted(team_data.items(), key=lambda x: x[1]["adoption_pct"], reverse=True)
            lb_rows = []
            for rank, (tid, data) in enumerate(sorted_teams, 1):
                pct = data["adoption_pct"]
                color = GREEN if pct >= 80 else YELLOW if pct >= 50 else RED
                lb_rows.append(html.Tr([
                    html.Td(str(rank), style={"color": TEXT2, "padding": "8px"}),
                    html.Td(team_lookup.get(tid, tid), style={"color": TEXT, "padding": "8px", "fontWeight": "600"}),
                    html.Td(f"{pct:.0f}%", style={"color": color, "padding": "8px", "fontWeight": "600"}),
                    html.Td(str(data["standard"]), style={"color": GREEN, "padding": "8px"}),
                    html.Td(str(data["non_standard"]), style={"color": RED, "padding": "8px"}),
                ]))
            leaderboard = html.Table([
                html.Thead(html.Tr([
                    html.Th(h, style={"color": TEXT2, "padding": "8px", "borderBottom": f"1px solid {BORDER}", "fontSize": "12px"})
                    for h in ["Rank", "Team", "Adoption %", "Standard", "Non-Standard"]
                ])),
                html.Tbody(lb_rows),
            ], style={"width": "100%", "borderCollapse": "collapse"}) if lb_rows else html.P("No teams", style={"color": TEXT2})

            # Violations table
            violations = [e for e in classified if e["classification"] == "non_standard"][:20]
            if violations:
                v_rows = []
                for v in violations:
                    v_rows.append(html.Tr([
                        html.Td(str(v.get("timestamp", ""))[:19], style={"color": TEXT2, "padding": "6px", "fontSize": "12px"}),
                        html.Td(v.get("actor_email", ""), style={"color": TEXT, "padding": "6px", "fontSize": "12px"}),
                        html.Td(v.get("artifact_type", ""), style={"color": TEXT2, "padding": "6px", "fontSize": "12px"}),
                        html.Td(v.get("action_name", ""), style={"color": TEXT2, "padding": "6px", "fontSize": "12px"}),
                        html.Td(f"{v.get('confidence', 0):.0%}", style={"color": YELLOW, "padding": "6px", "fontSize": "12px"}),
                    ]))
                violations_table = html.Table([
                    html.Thead(html.Tr([
                        html.Th(h, style={"color": TEXT2, "padding": "6px", "borderBottom": f"1px solid {BORDER}", "fontSize": "11px"})
                        for h in ["Timestamp", "Actor", "Artifact", "Action", "Confidence"]
                    ])),
                    html.Tbody(v_rows),
                ], style={"width": "100%", "borderCollapse": "collapse"})
            else:
                violations_table = html.P("No non-standard deployments detected", style={"color": GREEN})

            # Coaching queue
            below_threshold = [(tid, d) for tid, d in sorted_teams if d["adoption_pct"] < 80]
            if below_threshold:
                coaching = html.Div([
                    html.Div([
                        html.Span(team_lookup.get(tid, tid), style={"color": TEXT, "fontWeight": "600", "marginRight": "12px"}),
                        html.Span(f"{d['adoption_pct']:.0f}% adoption", style={"color": RED if d["adoption_pct"] < 50 else YELLOW}),
                        html.Span(f" ({d['non_standard']} non-standard)", style={"color": TEXT3, "marginLeft": "8px", "fontSize": "12px"}),
                    ], style={"padding": "10px", "borderBottom": f"1px solid {BORDER}"})
                    for tid, d in below_threshold
                ])
            else:
                coaching = html.P("All teams above 80% adoption threshold!", style={"color": GREEN})

            return [kpis, pie, trend, artifact, heatmap, leaderboard, violations_table, coaching]

        except Exception:
            err = _empty_figure("No data available yet")
            empty = html.P("No data available. Connect a data source to get started.",
                           style={"color": "#8B949E"})
            return [
                [_kpi_card("Adoption", "--")],
                err, err, err, err, empty, empty, empty,
            ]
