"""KPI Card Component - 3px colored top stripe with hover lift"""
from dash import html

def create_kpi_card(label, value, delta=None, delta_direction="neutral", color="blue", card_id=None):
    """Create a KPI card.
    Args:
        label: Card label text (uppercase)
        value: Main value to display
        delta: Optional delta text (e.g., "+5.2%")
        delta_direction: "positive", "negative", or "neutral"
        color: Top stripe color class (blue, green, purple, red, yellow, cyan)
        card_id: Optional HTML id
    """
    children = [
        html.Div(label, className="kpi-label"),
        html.Div(str(value), className="kpi-value"),
    ]
    if delta is not None:
        children.append(html.Div(str(delta), className=f"kpi-delta {delta_direction}"))

    props = {"className": f"kpi-card {color}"}
    if card_id:
        props["id"] = card_id
    return html.Div(children, **props)
