"""
PDF Export for Pipeline Compass.

Generates a comprehensive PDF report from assessment results using
HTML/CSS templates rendered to PDF. Falls back to a simple text-based
PDF if WeasyPrint is not available.
"""

import io
from datetime import datetime

from compass.scoring_engine import TIER_COLORS, TIER_LABELS
from compass.antipattern_engine import SEVERITY_COLORS


def generate_pdf_report(assessment: dict, org: dict) -> bytes:
    """
    Generate a PDF report for an assessment.

    Returns PDF as bytes for download.
    """
    composite = assessment.get("composite", {})
    dim_scores = assessment.get("scores", {})
    anti_patterns = assessment.get("anti_patterns", [])
    roadmap = assessment.get("roadmap", {})
    benchmark = assessment.get("benchmark_comparison", {})

    overall_score = composite.get("overall_score", 0)
    overall_level = composite.get("overall_level", 1)
    overall_label = composite.get("overall_label", "Initial")
    breakdown = composite.get("dimension_breakdown", {})

    org_name = org.get("name", "Unknown")
    industry = org.get("industry", "").replace("_", " ").title()
    date_str = datetime.now().strftime("%B %d, %Y")

    # Try WeasyPrint first
    try:
        from weasyprint import HTML
        html_content = _build_html_report(
            org_name, industry, date_str,
            overall_score, overall_level, overall_label,
            breakdown, dim_scores, anti_patterns, roadmap, benchmark,
            assessment,
        )
        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes
    except ImportError:
        pass

    # Fallback: generate a simple text-based PDF using reportlab if available
    try:
        return _generate_reportlab_pdf(
            org_name, industry, date_str,
            overall_score, overall_level, overall_label,
            breakdown, anti_patterns, roadmap,
        )
    except ImportError:
        pass

    # Final fallback: plain text PDF-like bytes
    return _generate_text_report(
        org_name, industry, date_str,
        overall_score, overall_level, overall_label,
        breakdown, anti_patterns, roadmap,
    )


def _build_html_report(
    org_name, industry, date_str,
    overall_score, overall_level, overall_label,
    breakdown, dim_scores, anti_patterns, roadmap, benchmark,
    assessment,
):
    """Build HTML string for WeasyPrint PDF generation."""
    # Dimension rows
    dim_rows = ""
    for dim_id, data in sorted(breakdown.items()):
        score = data.get("score", 0)
        level = data.get("level", 1)
        label = data.get("label", "Initial")
        color = TIER_COLORS.get(level, "#888")
        name = data.get("display_name", dim_id.replace("_", " ").title())
        conf = confidence_data.get(dim_id, "") if confidence_data else ""
        conf_badge = ""
        if conf:
            conf_colors = {"high": "#22C55E", "medium": "#EAB308", "low": "#EF4444"}
            cc = conf_colors.get(conf.lower(), "#888")
            conf_badge = f'<span style="background:{cc};color:white;padding:1px 5px;border-radius:3px;font-size:9px;margin-left:6px;">{conf.upper()}</span>'
        dim_rows += f"""
        <tr>
            <td style="padding:8px;border-bottom:1px solid #eee;">{name}</td>
            <td style="padding:8px;border-bottom:1px solid #eee;text-align:center;">
                <span style="background:{color};color:white;padding:2px 8px;border-radius:4px;font-weight:bold;">
                    L{level}
                </span>{conf_badge}
            </td>
            <td style="padding:8px;border-bottom:1px solid #eee;text-align:center;">{score:.0f}/100</td>
            <td style="padding:8px;border-bottom:1px solid #eee;">{label}</td>
        </tr>
        """

    # Anti-pattern rows
    ap_rows = ""
    for ap in anti_patterns:
        sev_color = SEVERITY_COLORS.get(ap["severity"], "#888")
        ap_rows += f"""
        <tr>
            <td style="padding:8px;border-bottom:1px solid #eee;">
                <span style="background:{sev_color};color:white;padding:2px 6px;border-radius:3px;font-size:10px;font-weight:bold;">
                    {ap['severity'].upper()}
                </span>
            </td>
            <td style="padding:8px;border-bottom:1px solid #eee;font-weight:bold;">{ap['name']}</td>
            <td style="padding:8px;border-bottom:1px solid #eee;font-size:12px;">{ap.get('recommendation', '')}</td>
        </tr>
        """

    # Roadmap phases
    roadmap_html = ""
    for phase in roadmap.get("phases", []):
        items = phase.get("items", [])
        if not items:
            continue
        roadmap_html += f"<h3 style='color:#2E75B6;margin-top:16px;'>{phase['name']}</h3>"
        roadmap_html += "<ul>"
        for item in items[:5]:
            roadmap_html += f"<li style='margin-bottom:6px;'><strong>{item.get('title', '')}</strong> — {item.get('description', '')[:120]}... (Effort: {item.get('effort_days', '?')}d, Impact: +{item.get('expected_score_improvement', 0)} pts)</li>"
        if len(items) > 5:
            roadmap_html += f"<li style='color:#888;'>...and {len(items) - 5} more items</li>"
        roadmap_html += "</ul>"

    # DORA metrics section
    dora_data = assessment.get("dora_metrics", {})
    dora_html = ""
    if dora_data:
        dora_rows = ""
        tier_colors_map = {"Elite": "#3B82F6", "High": "#22C55E", "Medium": "#EAB308", "Low": "#EF4444"}
        for metric_name, metric_info in dora_data.items():
            if isinstance(metric_info, dict):
                val = metric_info.get("value", "N/A")
                tier = metric_info.get("tier", "Unknown")
                unit = metric_info.get("unit", "")
                tc = tier_colors_map.get(tier, "#888")
                dora_rows += f"""
                <tr>
                    <td style="padding:8px;border-bottom:1px solid #eee;">{metric_name.replace('_', ' ').title()}</td>
                    <td style="padding:8px;border-bottom:1px solid #eee;text-align:center;">{val} {unit}</td>
                    <td style="padding:8px;border-bottom:1px solid #eee;text-align:center;">
                        <span style="background:{tc};color:white;padding:2px 8px;border-radius:4px;font-weight:bold;">{tier}</span>
                    </td>
                </tr>
                """
        dora_html = f"""
        <h2>DORA Metrics</h2>
        <table>
            <tr><th>Metric</th><th>Value</th><th>Tier</th></tr>
            {dora_rows}
        </table>
        """

    # Hygiene check summary
    hygiene_data = assessment.get("hygiene_scores", [])
    hygiene_html = ""
    if hygiene_data and isinstance(hygiene_data, list):
        platform_stats = {}
        for h in hygiene_data:
            if not isinstance(h, dict):
                continue
            plat = h.get("platform", "unknown")
            if plat not in platform_stats:
                platform_stats[plat] = {"pass": 0, "warn": 0, "fail": 0}
            status = h.get("status", "unknown")
            if status in platform_stats[plat]:
                platform_stats[plat][status] += 1

        hyg_rows = ""
        for plat, stats in sorted(platform_stats.items()):
            total = sum(stats.values())
            hyg_rows += f"""
            <tr>
                <td style="padding:8px;border-bottom:1px solid #eee;">{plat.replace('_', ' ').title()}</td>
                <td style="padding:8px;border-bottom:1px solid #eee;text-align:center;color:#22C55E;">{stats['pass']}</td>
                <td style="padding:8px;border-bottom:1px solid #eee;text-align:center;color:#EAB308;">{stats['warn']}</td>
                <td style="padding:8px;border-bottom:1px solid #eee;text-align:center;color:#EF4444;">{stats['fail']}</td>
                <td style="padding:8px;border-bottom:1px solid #eee;text-align:center;">{total}</td>
            </tr>
            """
        hygiene_html = f"""
        <h2>Hygiene Check Summary</h2>
        <table>
            <tr><th>Platform</th><th>Pass</th><th>Warn</th><th>Fail</th><th>Total</th></tr>
            {hyg_rows}
        </table>
        """

    # Confidence badges for dimension rows
    confidence_data = assessment.get("confidence", {})
    confidence_suffix = ""
    if confidence_data:
        confidence_suffix = " (with confidence indicators)"

    overall_color = TIER_COLORS.get(overall_level, "#4B7BF5")

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page {{ size: letter; margin: 1in; }}
    body {{ font-family: 'Helvetica Neue', Arial, sans-serif; color: #333; font-size: 12px; line-height: 1.5; }}
    h1 {{ color: #2E75B6; font-size: 24px; margin-bottom: 4px; }}
    h2 {{ color: #2E75B6; font-size: 16px; border-bottom: 2px solid #2E75B6; padding-bottom: 4px; margin-top: 24px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
    th {{ background: #f5f5f5; padding: 8px; text-align: left; border-bottom: 2px solid #ddd; font-size: 11px; text-transform: uppercase; }}
    .cover {{ text-align: center; padding: 80px 0 40px; }}
    .score-badge {{ display: inline-block; padding: 8px 20px; border-radius: 8px; color: white; font-size: 28px; font-weight: bold; }}
    .footer {{ text-align: center; color: #888; font-size: 10px; margin-top: 40px; padding-top: 12px; border-top: 1px solid #eee; }}
</style>
</head>
<body>
    <!-- Cover -->
    <div class="cover">
        <h1>Pipeline Compass</h1>
        <p style="color:#888;font-size:14px;">CI/CD Maturity Assessment Report</p>
        <hr style="border:none;border-top:2px solid #2E75B6;width:60%;margin:20px auto;">
        <p style="font-size:18px;font-weight:bold;">{org_name}</p>
        <p style="color:#888;">{industry} | {date_str}</p>
        <div style="margin-top:30px;">
            <div class="score-badge" style="background:{overall_color};">
                {overall_score:.0f}/100 — L{overall_level} {overall_label}
            </div>
        </div>
    </div>

    <div style="page-break-after:always;"></div>

    <!-- Executive Summary -->
    <h2>Executive Summary</h2>
    <p>Overall maturity score: <strong>{overall_score:.0f}/100</strong> — <strong>Level {overall_level}: {overall_label}</strong></p>
    <p>Assessment type: {assessment.get('assessment_type', 'full').title()} | Weight profile: {composite.get('weight_profile', 'balanced').replace('_', ' ').title()}</p>
    <p>Anti-patterns detected: <strong>{len(anti_patterns)}</strong></p>

    <!-- Dimension Scores -->
    <h2>Dimension Scorecard</h2>
    <table>
        <tr><th>Dimension</th><th>Level</th><th>Score</th><th>Maturity</th></tr>
        {dim_rows}
    </table>

    <div style="page-break-after:always;"></div>

    <!-- Anti-Patterns -->
    <h2>Detected Anti-Patterns</h2>
    {"<p>No anti-patterns detected.</p>" if not anti_patterns else f'''
    <table>
        <tr><th>Severity</th><th>Pattern</th><th>Recommendation</th></tr>
        {ap_rows}
    </table>
    '''}

    <div style="page-break-after:always;"></div>

    {dora_html}

    {hygiene_html}

    <div style="page-break-after:always;"></div>

    <!-- Roadmap -->
    <h2>Improvement Roadmap</h2>
    {roadmap_html if roadmap_html else "<p>No improvement items generated.</p>"}

    <!-- Confidence Analysis -->
    <h2>Confidence Analysis</h2>
    <p>Confidence levels indicate how reliable each dimension score is based on the data sources available.</p>
    <table>
        <tr><th>Level</th><th>Description</th></tr>
        <tr><td style="padding:8px;"><span style="background:#22C55E;color:white;padding:2px 8px;border-radius:4px;font-weight:bold;">HIGH</span></td><td style="padding:8px;">Both telemetry and assessment data available with strong agreement</td></tr>
        <tr><td style="padding:8px;"><span style="background:#EAB308;color:white;padding:2px 8px;border-radius:4px;font-weight:bold;">MEDIUM</span></td><td style="padding:8px;">One data source available, or moderate discrepancy between sources</td></tr>
        <tr><td style="padding:8px;"><span style="background:#EF4444;color:white;padding:2px 8px;border-radius:4px;font-weight:bold;">LOW</span></td><td style="padding:8px;">Limited data or significant discrepancy (>20 points) between assessment and telemetry</td></tr>
    </table>

    <!-- Scoring Methodology -->
    <h2>Scoring Methodology</h2>
    <p>Pipeline Compass uses a two-layer scoring system:</p>
    <ul>
        <li><strong>Layer 1 (Raw Score):</strong> 0-100 score per dimension from weighted question responses and telemetry data</li>
        <li><strong>Layer 2 (Maturity Tier):</strong> L1 Initial (0-20) → L2 Managed (21-40) → L3 Defined (41-60) → L4 Optimized (61-80) → L5 Elite (81-100)</li>
    </ul>
    <p>The composite score uses a <strong>weighted geometric mean</strong> to prevent high scores in one dimension from masking critical gaps. Hard-gate checks (e.g., branch protection disabled) cap the dimension score at L2 (40) regardless of other check results.</p>
    <p>Hybrid scoring blends telemetry (70%) with assessment responses (30%) when both data sources are available.</p>

    <!-- Footer -->
    <div class="footer">
        Pipeline Compass — CI/CD Maturity Assessment | Blueprint Technologies | Generated {date_str}
    </div>
</body>
</html>"""


def _generate_reportlab_pdf(org_name, industry, date_str, overall_score, overall_level, overall_label, breakdown, anti_patterns, roadmap):
    """Generate PDF using reportlab."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph("Pipeline Compass", styles["Title"]))
    story.append(Paragraph("CI/CD Maturity Assessment Report", styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>{org_name}</b> | {industry} | {date_str}", styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Overall Score: <b>{overall_score:.0f}/100</b> — Level {overall_level}: {overall_label}", styles["Heading2"]))
    story.append(Spacer(1, 24))

    # Dimension table
    story.append(Paragraph("Dimension Scorecard", styles["Heading2"]))
    table_data = [["Dimension", "Level", "Score", "Maturity"]]
    for dim_id, data in sorted(breakdown.items()):
        table_data.append([
            data.get("display_name", dim_id.replace("_", " ").title()),
            f"L{data.get('level', 1)}",
            f"{data.get('score', 0):.0f}/100",
            data.get("label", "Initial"),
        ])
    t = Table(table_data, colWidths=[2.5 * inch, 0.8 * inch, 1 * inch, 1.2 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.18, 0.46, 0.71)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(t)
    story.append(Spacer(1, 24))

    # Anti-patterns
    story.append(Paragraph(f"Detected Anti-Patterns ({len(anti_patterns)})", styles["Heading2"]))
    for ap in anti_patterns:
        story.append(Paragraph(f"<b>[{ap['severity'].upper()}]</b> {ap['name']} — {ap.get('recommendation', '')[:150]}", styles["Normal"]))
        story.append(Spacer(1, 4))

    doc.build(story)
    return buffer.getvalue()


def _generate_text_report(org_name, industry, date_str, overall_score, overall_level, overall_label, breakdown, anti_patterns, roadmap):
    """Generate a plain text report as bytes (fallback)."""
    lines = [
        "=" * 60,
        "PIPELINE COMPASS — CI/CD Maturity Assessment Report",
        "=" * 60,
        "",
        f"Organization: {org_name}",
        f"Industry: {industry}",
        f"Date: {date_str}",
        "",
        f"Overall Score: {overall_score:.0f}/100 — Level {overall_level}: {overall_label}",
        "",
        "-" * 60,
        "DIMENSION SCORECARD",
        "-" * 60,
    ]

    for dim_id, data in sorted(breakdown.items()):
        name = data.get("display_name", dim_id.replace("_", " ").title())
        score = data.get("score", 0)
        level = data.get("level", 1)
        label = data.get("label", "Initial")
        lines.append(f"  {name:<30} L{level}  {score:>5.0f}/100  {label}")

    lines.extend(["", "-" * 60, f"ANTI-PATTERNS ({len(anti_patterns)})", "-" * 60])
    for ap in anti_patterns:
        lines.append(f"  [{ap['severity'].upper():>8}] {ap['name']}")
        lines.append(f"            {ap.get('recommendation', '')[:100]}")
        lines.append("")

    lines.extend(["", "-" * 60, "ROADMAP", "-" * 60])
    for phase in roadmap.get("phases", []):
        items = phase.get("items", [])
        if items:
            lines.append(f"  {phase['name']} ({len(items)} items)")
            for item in items[:3]:
                lines.append(f"    - {item.get('title', '')} ({item.get('effort_days', '?')}d)")

    lines.extend(["", "=" * 60, "Generated by Pipeline Compass — Blueprint Technologies", "=" * 60])
    return "\n".join(lines).encode("utf-8")
