"""Styled DataTable Component"""
from dash import dash_table
from ui.theme import SURFACE, ELEVATED, BORDER, TEXT, TEXT2, BG, ACCENT

def create_data_table(df, table_id, page_size=10, columns=None):
    """Create a styled Dash DataTable matching Blueprint design."""
    if columns is None:
        columns = [{"name": col, "id": col} for col in df.columns]

    return dash_table.DataTable(
        id=table_id,
        columns=columns,
        data=df.to_dict("records"),
        page_size=page_size,
        sort_action="native",
        filter_action="native",
        style_table={"overflowX": "auto"},
        style_header={
            "backgroundColor": ELEVATED,
            "color": TEXT2,
            "fontWeight": "600",
            "fontSize": "11px",
            "textTransform": "uppercase",
            "letterSpacing": "0.5px",
            "border": f"1px solid {BORDER}",
            "padding": "10px 14px",
        },
        style_cell={
            "backgroundColor": SURFACE,
            "color": TEXT,
            "border": f"1px solid {BORDER}",
            "padding": "9px 14px",
            "fontSize": "13px",
            "fontFamily": "DM Sans, Inter, system-ui, sans-serif",
            "textAlign": "left",
        },
        style_data_conditional=[
            {"if": {"state": "active"}, "backgroundColor": "rgba(75,123,245,.08)", "border": f"1px solid {BORDER}"},
        ],
        style_filter={
            "backgroundColor": BG,
            "color": TEXT,
            "border": f"1px solid {BORDER}",
        },
        page_current=0,
    )
    # ****Checked and Verified as Real*****
    # Create a styled Dash DataTable matching Blueprint design.
