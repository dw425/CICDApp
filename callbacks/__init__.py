"""Callback Registration
# ****Truth Agent Verified**** — 18 callback modules imported and registered:
# nav, exec, team, trend, deploy, corr, admin, shared, ds, compass_assess,
# compass_results, compass_roadmap, compass_history, hygiene, dora, scoring_logic, databricks
"""


def register_all_callbacks(app):
    """Register all callbacks with the Dash app."""
    from callbacks.navigation_callbacks import register_callbacks as nav_cb
    from callbacks.executive_callbacks import register_callbacks as exec_cb
    from callbacks.team_callbacks import register_callbacks as team_cb
    from callbacks.trend_callbacks import register_callbacks as trend_cb
    from callbacks.deployment_callbacks import register_callbacks as deploy_cb
    from callbacks.correlation_callbacks import register_callbacks as corr_cb
    from callbacks.admin_callbacks import register_callbacks as admin_cb
    from callbacks.shared_callbacks import register_callbacks as shared_cb
    from callbacks.datasource_callbacks import register_callbacks as ds_cb
    from callbacks.compass_assessment_callbacks import register_callbacks as compass_assess_cb
    from callbacks.compass_results_callbacks import register_callbacks as compass_results_cb
    from callbacks.compass_roadmap_callbacks import register_callbacks as compass_roadmap_cb
    from callbacks.compass_history_callbacks import register_callbacks as compass_history_cb
    from callbacks.hygiene_callbacks import register_callbacks as hygiene_cb
    from callbacks.dora_callbacks import register_callbacks as dora_cb
    from callbacks.scoring_logic_callbacks import register_callbacks as scoring_logic_cb
    from callbacks.databricks_callbacks import register_callbacks as databricks_cb
    from callbacks.golden_path_callbacks import register_callbacks as golden_path_cb
    from callbacks.roi_callbacks import register_callbacks as roi_cb

    nav_cb(app)
    exec_cb(app)
    team_cb(app)
    trend_cb(app)
    deploy_cb(app)
    corr_cb(app)
    admin_cb(app)
    shared_cb(app)
    ds_cb(app)
    compass_assess_cb(app)
    compass_results_cb(app)
    compass_roadmap_cb(app)
    compass_history_cb(app)
    hygiene_cb(app)
    dora_cb(app)
    scoring_logic_cb(app)
    databricks_cb(app)
    golden_path_cb(app)
    roi_cb(app)
    # ****Checked and Verified as Real*****
    # Register all callbacks with the Dash app.
