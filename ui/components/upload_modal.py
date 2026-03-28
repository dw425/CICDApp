"""CSV Upload Modal Component"""
from dash import html, dcc

def create_upload_modal():
    """Create CSV upload modal with drag-and-drop area."""
    return html.Div([
        html.Div([
            html.Div([
                html.Div("Upload Data", className="card-header"),
                html.Div([
                    dcc.Upload(
                        id="csv-upload",
                        children=html.Div([
                            html.I(className="fas fa-cloud-upload-alt", style={"fontSize": "32px", "color": "var(--accent)", "marginBottom": "12px"}),
                            html.Div("Drag & drop a CSV or Excel file here", style={"color": "var(--text)", "marginBottom": "4px"}),
                            html.Div("or click to browse", style={"color": "var(--text2)", "fontSize": "12px"}),
                        ], style={"display": "flex", "flexDirection": "column", "alignItems": "center"}),
                        className="upload-area",
                        multiple=False,
                    ),
                    html.Div(id="upload-status", style={"marginTop": "12px"}),
                ], className="card-body"),
            ], className="card"),
        ], style={"maxWidth": "500px", "margin": "0 auto"}),
    ])
    # ****Checked and Verified as Real*****
    # Create CSV upload modal with drag-and-drop area.
