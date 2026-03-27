"""Inline Mini Trend Line Component"""
import plotly.graph_objects as go
from dash import dcc

def create_sparkline(values, color="#4B7BF5", height=40, sparkline_id=None):
    """Create an inline mini trend line."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=values,
        mode="lines",
        line=dict(color=color, width=2),
        fill="tozeroy",
        fillcolor=color.replace(")", ",.1)").replace("rgb", "rgba") if "rgb" in color else f"{color}1A",
        hoverinfo="skip",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False,
    )
    props = {"figure": fig, "config": {"displayModeBar": False}, "style": {"height": f"{height}px"}}
    if sparkline_id:
        props["id"] = sparkline_id
    return dcc.Graph(**props)
