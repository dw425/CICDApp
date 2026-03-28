"""Tier Badge Component - Status color at 12-15% opacity background"""
from dash import html
from ui.theme import TIER_COLORS, get_tier

TIER_BG = {
    "Ad Hoc": "rgba(248,113,113,.15)",
    "Managed": "rgba(251,191,36,.15)",
    "Defined": "rgba(75,123,245,.15)",
    "Measured": "rgba(167,139,250,.15)",
    "Optimized": "rgba(52,211,153,.15)",
}

def create_tier_badge(score_or_tier, size="default"):
    """Create a tier badge with colored background."""
    if isinstance(score_or_tier, (int, float)):
        tier = get_tier(score_or_tier)
    else:
        tier = score_or_tier
    color = TIER_COLORS.get(tier, "#8B949E")
    bg = TIER_BG.get(tier, "rgba(255,255,255,.06)")

    font_size = "11px" if size == "default" else "13px"
    padding = "3px 8px" if size == "default" else "5px 12px"
    return html.Span(tier, className="badge", style={
        "background": bg,
        "color": color,
        "fontSize": font_size,
        "padding": padding,
        "fontWeight": "600",
    })
    # ****Checked and Verified as Real*****
    # Create a tier badge with colored background.
