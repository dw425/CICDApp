"""Smoke tests for callback registration."""
import os
os.environ["CICD_APP_USE_MOCK"] = "true"

import pytest
import dash


def test_callbacks_register():
    app = dash.Dash(__name__, suppress_callback_exceptions=True)
    from callbacks import register_all_callbacks
    register_all_callbacks(app)
    # If we get here without error, callbacks registered successfully
    assert True
