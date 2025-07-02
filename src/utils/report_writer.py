"""
report_writer.py

HTML report generation utility for Final Engine season reports.
Uses Jinja2 templates to generate formatted HTML reports from KPI data.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader


def generate_season_report(kpi_data: dict[str, Any], output_path: Path) -> None:
    """
    Generate HTML season report from KPI data.

    Parameters:
        kpi_data: Dictionary containing KPI summary data
        output_path: Path where HTML report should be saved
    """
    # Get project root and templates directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    templates_dir = project_root / "templates"

    # Ensure templates directory exists
    if not templates_dir.exists():
        raise FileNotFoundError(f"Templates directory not found: {templates_dir}")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader(str(templates_dir)), autoescape=True)

    # Load template
    template_name = "season_report.html"
    try:
        template = env.get_template(template_name)
    except Exception as e:
        raise FileNotFoundError(
            f"Template '{template_name}' not found in {templates_dir}: {e}"
        ) from e

    # Prepare template context
    context = {
        "kpi_data": kpi_data,
        "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # Render template
    try:
        html_content = template.render(context)
    except Exception as e:
        raise RuntimeError(f"Failed to render template: {e}") from e

    # Write to file
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
    except Exception as e:
        raise RuntimeError(f"Failed to write report to {output_path}: {e}") from e


def validate_kpi_data(kpi_data: dict[str, Any]) -> bool:
    """
    Validate that KPI data contains required fields.

    Parameters:
        kpi_data: Dictionary to validate

    Returns:
        True if valid, False otherwise
    """
    required_fields = [
        "avg_fun",
        "avg_logic",
        "guard_pass_rate",
        "avg_chars",
        "total_episodes",
        "passed_episodes",
        "failed_episodes",
    ]

    return all(field in kpi_data for field in required_fields)


def generate_simple_html_report(kpi_data: dict[str, Any], output_path: Path) -> None:
    """
    Generate a simple HTML report without Jinja2 templates (fallback).

    Parameters:
        kpi_data: Dictionary containing KPI summary data
        output_path: Path where HTML report should be saved
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Simple HTML template as string
    html_template = """<!DOCTYPE html>
<html>
<head>
    <title>Final Engine - Season KPI Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #2c3e50; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #f2f2f2; }
        .metric { background: #f8f9fa; padding: 15px; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>🏆 Final Engine - Season KPI Report</h1>

    <div class="metric">
        <h3>📊 Key Performance Indicators</h3>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Average Fun Score</td><td>{avg_fun}/10</td></tr>
            <tr><td>Average Logic Score</td><td>{avg_logic}/10</td></tr>
            <tr><td>Guard Pass Rate</td><td>{guard_pass_rate}%</td></tr>
            <tr><td>Average Characters</td><td>{avg_chars:,}</td></tr>
            <tr><td>Total Episodes</td><td>{total_episodes}</td></tr>
            <tr><td>Passed Episodes</td><td>{passed_episodes}</td></tr>
            <tr><td>Failed Episodes</td><td>{failed_episodes}</td></tr>
        </table>
    </div>

    <p><em>Generated on {generation_time}</em></p>
</body>
</html>"""

    # Format template with data
    context = {
        "avg_fun": kpi_data.get("avg_fun", 0),
        "avg_logic": kpi_data.get("avg_logic", 0),
        "guard_pass_rate": kpi_data.get("guard_pass_rate", 0),
        "avg_chars": int(kpi_data.get("avg_chars", 0)),
        "total_episodes": kpi_data.get("total_episodes", 0),
        "passed_episodes": kpi_data.get("passed_episodes", 0),
        "failed_episodes": kpi_data.get("failed_episodes", 0),
        "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    html_content = html_template.format(**context)

    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
