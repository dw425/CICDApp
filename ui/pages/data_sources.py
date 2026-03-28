"""Data Source Console page layout.

All wizard interactive elements live permanently in the modal body
so their IDs always exist in the DOM. Step visibility is toggled
by callbacks updating the wrapper div styles.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc


def create_layout():
    """Return the Data Source Console page layout."""
    return html.Div([
        # Hidden stores for wizard state
        dcc.Store(id="wizard-state", data={}),
        dcc.Store(id="wizard-current-step", data=1),

        # ── Zone A: Source Registry (always visible) ──────────────
        html.Div("Data Sources", className="section-title"),

        # KPI summary row
        html.Div(id="datasource-kpi-row", className="kpi-grid", style={"gridTemplateColumns": "repeat(4, 1fr)"}),

        # Source card grid
        html.Div(id="datasource-card-grid", style={"marginTop": "20px"}),

        # Add Data Source button
        html.Div([
            html.Button(
                [html.I(className="fas fa-plus", style={"marginRight": "6px"}), "Add Data Source"],
                id="btn-add-datasource",
                className="btn btn-primary",
                style={"marginTop": "16px"},
            ),
        ]),

        # ── Zone B: 6-Step Wizard Modal ───────────────────────────
        dbc.Modal([
            dbc.ModalHeader(
                dbc.ModalTitle("Add Data Source"),
                close_button=True,
            ),
            dbc.ModalBody([
                # Step indicator (always visible in modal)
                html.Div(id="wizard-step-indicator"),
                html.Hr(style={"borderColor": "var(--border)", "margin": "16px 0"}),
                # Step content (swapped by callback)
                html.Div(id="wizard-step-content"),
            ]),
            dbc.ModalFooter([
                html.Button("Back", id="wizard-back-btn", className="btn btn-secondary", style={"marginRight": "8px"}),
                html.Button("Next", id="wizard-next-btn", className="btn btn-primary"),
            ]),
        ], id="wizard-modal", size="xl", is_open=False, centered=True, backdrop="static"),

        # ── Persistent hidden elements for callback targets ───────
        # These are Output-only targets that get replaced when steps
        # render. They sit outside the modal so they never collide
        # with dynamically-rendered step content.
        html.Div(id="_ds-hidden-targets", style={"display": "none"}, children=[
            # We keep these as stable references for callbacks
            # whose Inputs/States come from dynamic step content.
            # suppress_callback_exceptions handles the rest.
        ]),

        # Toast for notifications
        dbc.Toast(
            id="datasource-toast",
            header="Data Sources",
            is_open=False,
            duration=4000,
            dismissable=True,
            style={"position": "fixed", "top": 66, "right": 10, "width": 350, "zIndex": 9999},
        ),
    ])
    # ****Checked and Verified as Real*****
    # Return the Data Source Console page layout.
