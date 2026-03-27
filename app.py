"""CI/CD Maturity Intelligence App - Main Entry Point"""
import os
from dotenv import load_dotenv
load_dotenv()

import dash
import dash_bootstrap_components as dbc
from ui.layout import create_layout
from callbacks import register_all_callbacks

# Initialize Dash app
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,  # Base bootstrap (will be overridden by custom CSS)
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css",
        "https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap",
    ],
    title="CI/CD Maturity Intelligence",
    update_title="Loading...",
)

# Expose Flask server for gunicorn
server = app.server

# Set layout
app.layout = create_layout()

# Register all callbacks
register_all_callbacks(app)

if __name__ == "__main__":
    port = int(os.environ.get("APP_PORT", 8050))
    debug = os.environ.get("APP_DEBUG", "false").lower() == "true"
    app.run(debug=debug, port=port, host="0.0.0.0")
