"""ROI Calculator Callbacks — Computes and displays ROI projections."""

import plotly.graph_objects as go
from dash import html, Input, Output, State, no_update

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
    """Register ROI Calculator callbacks."""

    @app.callback(
        [
            Output("roi-kpi-row", "children"),
            Output("roi-breakdown-chart", "figure"),
            Output("roi-cumulative-chart", "figure"),
            Output("roi-detail-table", "children"),
            Output("roi-benchmarks", "children"),
        ],
        [Input("roi-calculate-btn", "n_clicks")],
        [
            State("roi-num-devs", "value"),
            State("roi-avg-salary", "value"),
            State("roi-deploys-week", "value"),
            State("roi-incidents-month", "value"),
            State("roi-build-time", "value"),
            State("roi-mttr", "value"),
            State("roi-current-tier", "value"),
            State("roi-target-tier", "value"),
            State("current-page", "data"),
        ],
        prevent_initial_call=True,
    )
    def calculate_roi(n_clicks, num_devs, avg_salary, deploys_week, incidents_month,
                      build_time, mttr, current_tier, target_tier, current_page):
        if current_page != "roi" or not n_clicks:
            return [no_update] * 5

        try:
            from analytics.roi_calculator import compute_roi

            # Map tier to approximate scores
            tier_scores = {
                "Ad Hoc": 15, "Managed": 35, "Defined": 55,
                "Measured": 75, "Optimized": 90,
            }
            curr_score = tier_scores.get(current_tier or "Managed", 35)
            tgt_score = tier_scores.get(target_tier or "Defined", 55)
            dimensions = ["build_integration", "pipeline_reliability", "observability",
                          "deployment_release", "security_compliance", "developer_experience"]
            before_scores = {d: curr_score for d in dimensions}
            after_scores = {d: tgt_score for d in dimensions}
            org_context = {
                "engineer_count": num_devs or 50,
                "avg_salary": avg_salary or 150000,
                "deploy_frequency_per_week": deploys_week or 20,
                "incidents_per_month": incidents_month or 5,
                "avg_build_time_minutes": build_time or 15,
                "avg_mttr_hours": mttr or 4,
                "builds_per_day": (deploys_week or 20) // 5,
            }
            result = compute_roi(before_scores, after_scores, org_context)
        except Exception as e:
            err = _empty_figure(f"Error: {str(e)}")
            return [
                [_kpi_card("Error", str(e)[:50])],
                err, err,
                html.P(f"Error: {e}", style={"color": RED}),
                html.P(f"Error: {e}", style={"color": RED}),
            ]

        total = result.get("total_annual_value", 0)
        breakdown = result.get("breakdown", [])

        # KPIs
        kpis = [
            _kpi_card("Annual Savings", f"${total:,.0f}", color=GREEN),
            _kpi_card("Monthly Savings", f"${total / 12:,.0f}", color=GREEN),
            _kpi_card("Per Developer", f"${total / max(num_devs, 1):,.0f}/yr", color=ACCENT),
            _kpi_card("Improvement", f"{result.get('improvement_pct', 0):.0f}%",
                       subtitle="score gain", color=YELLOW),
        ]

        # Breakdown bar chart
        display_names = [b["category"] for b in breakdown]
        cat_values = [b["annual_value"] for b in breakdown]

        breakdown_chart = go.Figure(go.Bar(
            x=cat_values, y=display_names, orientation="h",
            marker_color=[GREEN, ACCENT, YELLOW, "#8B5CF6", "#EC4899", "#06B6D4"][:len(display_names)],
            text=[f"${v:,.0f}" for v in cat_values],
            textposition="outside", textfont=dict(color=TEXT2, size=11),
        ))
        breakdown_chart.update_layout(
            paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
            font=dict(color=TEXT2), height=350,
            margin=dict(l=150, r=80, t=20, b=40),
            xaxis=dict(gridcolor=BORDER, tickfont=dict(color=TEXT2),
                       tickprefix="$", tickformat=","),
            yaxis=dict(tickfont=dict(color=TEXT2, size=11)),
        )

        # Cumulative chart (12 months)
        monthly = total / 12
        months = list(range(1, 13))
        cumulative_vals = [monthly * m for m in months]
        cumulative = go.Figure()
        cumulative.add_trace(go.Scatter(
            x=months, y=cumulative_vals,
            mode="lines+markers", line=dict(color=GREEN, width=2.5),
            marker=dict(size=6), fill="tozeroy",
            fillcolor="rgba(34,197,94,0.1)",
            hovertemplate="Month %{x}<br>Cumulative: $%{y:,.0f}<extra></extra>",
        ))
        cumulative.update_layout(
            paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
            font=dict(color=TEXT2), height=350,
            margin=dict(l=70, r=20, t=20, b=40),
            xaxis=dict(gridcolor=BORDER, tickfont=dict(color=TEXT2),
                       title=dict(text="Month"), dtick=1),
            yaxis=dict(gridcolor=BORDER, tickfont=dict(color=TEXT2),
                       title=dict(text="Cumulative Savings ($)"),
                       tickprefix="$", tickformat=","),
        )

        # Detail table
        rows = []
        for item in breakdown:
            rows.append(html.Tr([
                html.Td(item.get("category", ""),
                         style={"color": TEXT, "padding": "8px", "fontWeight": "600"}),
                html.Td(f"${item.get('annual_value', 0):,.0f}",
                         style={"color": GREEN, "padding": "8px"}),
                html.Td(item.get("description", ""),
                         style={"color": TEXT2, "padding": "8px", "fontSize": "12px"}),
            ]))

        detail_table = html.Table([
            html.Thead(html.Tr([
                html.Th(h, style={"color": TEXT2, "padding": "8px",
                                   "borderBottom": f"1px solid {BORDER}", "fontSize": "12px"})
                for h in ["Category", "Annual Value", "Description"]
            ])),
            html.Tbody(rows),
        ], style={"width": "100%", "borderCollapse": "collapse"})

        # Benchmarks
        benchmarks = html.Div([
            _benchmark_row("DORA 2024", "Elite performers deploy 973x more frequently than low performers"),
            _benchmark_row("McKinsey DVI", "Top-quartile dev velocity teams deliver 4-5x more value"),
            _benchmark_row("Forrester TEI", "Mature CI/CD practices yield 300-400% ROI over 3 years"),
            _benchmark_row("CodeScene", "Technical debt costs $3.61 per line of code annually"),
        ])

        return [kpis, breakdown_chart, cumulative, detail_table, benchmarks]


def _benchmark_row(source, text):
    return html.Div([
        html.Span(source, style={"color": ACCENT, "fontWeight": "600", "marginRight": "12px",
                                  "minWidth": "120px", "display": "inline-block"}),
        html.Span(text, style={"color": TEXT2, "fontSize": "13px"}),
    ], style={"padding": "8px 0", "borderBottom": f"1px solid {BORDER}"})
