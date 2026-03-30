"""Radial Gauge Component with CMMI Tier Color Bands"""
import plotly.graph_objects as go
from dash import dcc
from ui.theme import TIER_COLORS, get_tier, get_tier_color

def create_gauge(score, title="Composite Score", gauge_id=None):
    """Create a radial gauge figure showing score with tier color bands."""
    tier = get_tier(score)
    color = get_tier_color(score)

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        title={"text": title, "font": {"size": 14, "color": "#8B949E"}},
        number={"font": {"size": 42, "color": "#E6EDF3"}, "suffix": ""},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#272D3F", "dtick": 20},
            "bar": {"color": color, "thickness": 0.3},
            "bgcolor": "#161B22",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 20], "color": "rgba(248,113,113,.15)"},
                {"range": [21, 40], "color": "rgba(251,191,36,.15)"},
                {"range": [41, 60], "color": "rgba(75,123,245,.15)"},
                {"range": [61, 80], "color": "rgba(167,139,250,.15)"},
                {"range": [81, 100], "color": "rgba(52,211,153,.15)"},
            ],
            "threshold": {
                "line": {"color": color, "width": 3},
                "thickness": 0.8,
                "value": score,
            },
        },
    ))
    fig.update_layout(
        paper_bgcolor="#161B22",
        plot_bgcolor="#161B22",
        font={"family": "DM Sans, Inter, system-ui, sans-serif", "color": "#8B949E"},
        height=270,
        margin=dict(l=20, r=20, t=40, b=40),
    )
    # Add tier annotation
    fig.add_annotation(
        text=tier,
        x=0.5, y=0.08,
        font=dict(size=14, color=color, family="DM Sans"),
        showarrow=False, xref="paper", yref="paper",
    )

    props = {"figure": fig, "config": {"displayModeBar": False}}
    if gauge_id:
        props["id"] = gauge_id
    return dcc.Graph(**props)
    # ****Checked and Verified as Real*****
    # Create a radial gauge figure showing score with tier color bands.
