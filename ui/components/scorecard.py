"""Team Scorecard Component"""
from dash import html
from ui.theme import CHART_COLORS, get_tier, get_tier_color
from ui.components.tier_badge import create_tier_badge

def create_scorecard(team_name, composite_score, domain_scores=None):
    """Create a team scorecard with composite score and mini domain bars.
    domain_scores: dict like {"golden_path": 75, "pipeline_reliability": 60, ...}
    """
    domain_labels = {
        "golden_path": "Golden Path",
        "environment_promotion": "Env Promotion",
        "pipeline_reliability": "Pipeline Rel.",
        "data_quality": "Data Quality",
        "security_governance": "Security",
        "cost_efficiency": "Cost Efficiency",
    }

    bars = []
    if domain_scores:
        for domain, label in domain_labels.items():
            score = domain_scores.get(domain, 0)
            color = get_tier_color(score)
            bars.append(html.Div([
                html.Div([
                    html.Span(label, style={"fontSize": "11px", "color": "var(--text2)"}),
                    html.Span(f"{score}", style={"fontSize": "11px", "color": "var(--text)", "fontWeight": "600"}),
                ], style={"display": "flex", "justifyContent": "space-between", "marginBottom": "3px"}),
                html.Div(
                    html.Div(style={"width": f"{score}%", "height": "100%", "background": color, "borderRadius": "2px", "transition": "width 0.3s"}),
                    style={"height": "4px", "background": "var(--border)", "borderRadius": "2px", "overflow": "hidden"}
                ),
            ], style={"marginBottom": "8px"}))

    return html.Div([
        html.Div([
            html.Div(team_name, style={"fontWeight": "600", "fontSize": "14px"}),
            create_tier_badge(composite_score),
        ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "12px"}),
        html.Div(f"{composite_score}", style={"fontSize": "28px", "fontWeight": "700", "marginBottom": "12px", "fontVariantNumeric": "tabular-nums"}),
        html.Div(bars),
    ], className="card", style={"padding": "20px"})
    # ****Checked and Verified as Real*****
    # Create a team scorecard with composite score and mini domain bars. domain_scores: dict like {"golden_path": 75, "pipeline_reliability": 60, ...}
