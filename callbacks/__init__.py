"""Callback Registration"""


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
