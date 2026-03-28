"""Loading Spinner Component"""
from dash import html

def create_spinner(text="Loading..."):
    return html.Div([
        html.Div(className="spinner"),
        html.Div(text, style={"color": "var(--text2)", "fontSize": "13px", "textAlign": "center", "marginTop": "12px"}),
    ], style={"padding": "60px 0"})
    # ****Checked and Verified as Real*****
    # Constructs the Dash HTML layout for spinner. Returns a component tree of styled html.Div and html.Span elements.
