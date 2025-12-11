"""Report generation module for test results."""

import io
from datetime import datetime
from typing import Any

# HTML Report Template
HTML_REPORT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IoTix Test Report - {run_id}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 0;
            margin-bottom: 30px;
        }}
        header h1 {{
            font-size: 2rem;
            margin-bottom: 10px;
        }}
        header .meta {{
            opacity: 0.9;
            font-size: 0.9rem;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .card h3 {{
            font-size: 0.85rem;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
        }}
        .card .value {{
            font-size: 2rem;
            font-weight: bold;
        }}
        .card.passed .value {{ color: #10b981; }}
        .card.failed .value {{ color: #ef4444; }}
        .card.total .value {{ color: #3b82f6; }}
        .card.duration .value {{ color: #8b5cf6; }}
        .results-table {{
            width: 100%;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .results-table th,
        .results-table td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        .results-table th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #555;
        }}
        .results-table tr:last-child td {{
            border-bottom: none;
        }}
        .status {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
            text-transform: uppercase;
        }}
        .status.passed {{
            background: #d1fae5;
            color: #065f46;
        }}
        .status.failed {{
            background: #fee2e2;
            color: #991b1b;
        }}
        .status.error {{
            background: #fef3c7;
            color: #92400e;
        }}
        .status.skipped {{
            background: #e5e7eb;
            color: #4b5563;
        }}
        footer {{
            margin-top: 40px;
            text-align: center;
            color: #666;
            font-size: 0.85rem;
        }}
        .progress-bar {{
            height: 8px;
            background: #e5e7eb;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 15px;
        }}
        .progress-bar .fill {{
            height: 100%;
            transition: width 0.3s ease;
        }}
        .progress-bar .fill.passed {{ background: #10b981; }}
        .progress-bar .fill.failed {{ background: #ef4444; }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>IoTix Test Report</h1>
            <div class="meta">
                <strong>Run ID:</strong> {run_id} |
                <strong>Started:</strong> {started_at} |
                <strong>Status:</strong> {status}
            </div>
        </div>
    </header>

    <div class="container">
        <section class="summary">
            <div class="card total">
                <h3>Total Tests</h3>
                <div class="value">{total_tests}</div>
            </div>
            <div class="card passed">
                <h3>Passed</h3>
                <div class="value">{passed}</div>
            </div>
            <div class="card failed">
                <h3>Failed</h3>
                <div class="value">{failed}</div>
            </div>
            <div class="card duration">
                <h3>Duration</h3>
                <div class="value">{duration}s</div>
            </div>
        </section>

        <section class="card">
            <h3>Pass Rate</h3>
            <div class="value">{pass_rate}%</div>
            <div class="progress-bar">
                <div class="fill passed" style="width: {pass_rate}%"></div>
            </div>
        </section>

        <section style="margin-top: 30px;">
            <h2 style="margin-bottom: 15px;">Test Results</h2>
            <table class="results-table">
                <thead>
                    <tr>
                        <th>Test Name</th>
                        <th>Status</th>
                        <th>Duration</th>
                        <th>Message</th>
                    </tr>
                </thead>
                <tbody>
                    {test_rows}
                </tbody>
            </table>
        </section>

        <footer>
            <p>Generated by IoTix Test Engine on {generated_at}</p>
        </footer>
    </div>
</body>
</html>
"""

JUNIT_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="{run_id}" tests="{total_tests}" failures="{failed}" errors="{errors}" time="{duration}" timestamp="{started_at}">
{test_cases}
</testsuite>
"""

JUNIT_TESTCASE_PASSED = '    <testcase name="{name}" classname="iotix" time="{duration}"/>'
JUNIT_TESTCASE_FAILED = '''    <testcase name="{name}" classname="iotix" time="{duration}">
        <failure message="{message}" type="AssertionError">{message}</failure>
    </testcase>'''
JUNIT_TESTCASE_ERROR = '''    <testcase name="{name}" classname="iotix" time="{duration}">
        <error message="{message}" type="Error">{message}</error>
    </testcase>'''
JUNIT_TESTCASE_SKIPPED = '''    <testcase name="{name}" classname="iotix" time="{duration}">
        <skipped message="{message}"/>
    </testcase>'''


def generate_html_report(run: dict[str, Any]) -> str:
    """Generate HTML report for a test run.

    Args:
        run: Test run data dictionary

    Returns:
        HTML report string
    """
    run_id = run.get("runId", "unknown")
    started_at = run.get("startedAt", "")
    status = run.get("status", "unknown")
    total_tests = run.get("totalTests", 0)
    passed = run.get("passed", 0)
    failed = run.get("failed", 0)
    errors = run.get("errors", 0)
    duration = run.get("durationSeconds", 0) or 0
    results = run.get("results", [])

    # Calculate pass rate
    pass_rate = round((passed / total_tests * 100) if total_tests > 0 else 0, 1)

    # Generate test rows
    test_rows = []
    for result in results:
        name = result.get("name", "")
        test_status = result.get("status", "unknown")
        test_duration = result.get("duration", 0)
        message = result.get("message", "")

        row = f"""
                    <tr>
                        <td>{name}</td>
                        <td><span class="status {test_status}">{test_status}</span></td>
                        <td>{test_duration}s</td>
                        <td>{message}</td>
                    </tr>"""
        test_rows.append(row)

    return HTML_REPORT_TEMPLATE.format(
        run_id=run_id,
        started_at=started_at,
        status=status,
        total_tests=total_tests,
        passed=passed,
        failed=failed + errors,
        duration=round(duration, 2),
        pass_rate=pass_rate,
        test_rows="\n".join(test_rows),
        generated_at=datetime.now().isoformat(),
    )


def generate_junit_report(run: dict[str, Any]) -> str:
    """Generate JUnit XML report for a test run.

    Args:
        run: Test run data dictionary

    Returns:
        JUnit XML string
    """
    run_id = run.get("runId", "unknown")
    started_at = run.get("startedAt", "")
    total_tests = run.get("totalTests", 0)
    failed = run.get("failed", 0)
    errors = run.get("errors", 0)
    duration = run.get("durationSeconds", 0) or 0
    results = run.get("results", [])

    # Generate test cases
    test_cases = []
    for result in results:
        name = result.get("name", "")
        status = result.get("status", "unknown")
        test_duration = result.get("duration", 0)
        message = result.get("message", "")

        if status == "passed":
            test_cases.append(
                JUNIT_TESTCASE_PASSED.format(name=name, duration=test_duration)
            )
        elif status == "failed":
            test_cases.append(
                JUNIT_TESTCASE_FAILED.format(
                    name=name, duration=test_duration, message=_escape_xml(message)
                )
            )
        elif status == "error":
            test_cases.append(
                JUNIT_TESTCASE_ERROR.format(
                    name=name, duration=test_duration, message=_escape_xml(message)
                )
            )
        else:  # skipped
            test_cases.append(
                JUNIT_TESTCASE_SKIPPED.format(
                    name=name, duration=test_duration, message=_escape_xml(message)
                )
            )

    return JUNIT_TEMPLATE.format(
        run_id=run_id,
        started_at=started_at,
        total_tests=total_tests,
        failed=failed,
        errors=errors,
        duration=round(duration, 2),
        test_cases="\n".join(test_cases),
    )


def generate_csv_report(run: dict[str, Any]) -> str:
    """Generate CSV report for a test run.

    Args:
        run: Test run data dictionary

    Returns:
        CSV string
    """
    lines = ["test_name,status,duration,message"]
    results = run.get("results", [])

    for result in results:
        name = result.get("name", "").replace(",", ";")
        status = result.get("status", "unknown")
        duration = result.get("duration", 0)
        message = result.get("message", "").replace(",", ";").replace("\n", " ")
        lines.append(f'"{name}","{status}",{duration},"{message}"')

    return "\n".join(lines)


def generate_markdown_report(run: dict[str, Any]) -> str:
    """Generate Markdown report for a test run.

    Args:
        run: Test run data dictionary

    Returns:
        Markdown string
    """
    run_id = run.get("runId", "unknown")
    started_at = run.get("startedAt", "")
    status = run.get("status", "unknown")
    total_tests = run.get("totalTests", 0)
    passed = run.get("passed", 0)
    failed = run.get("failed", 0)
    errors = run.get("errors", 0)
    duration = run.get("durationSeconds", 0) or 0
    results = run.get("results", [])

    # Calculate pass rate
    pass_rate = round((passed / total_tests * 100) if total_tests > 0 else 0, 1)

    # Status emoji
    status_emoji = {
        "passed": "✅",
        "failed": "❌",
        "error": "⚠️",
        "running": "🔄",
    }.get(status, "❓")

    lines = [
        f"# IoTix Test Report",
        "",
        f"**Run ID:** `{run_id}`",
        f"**Status:** {status_emoji} {status}",
        f"**Started:** {started_at}",
        f"**Duration:** {round(duration, 2)}s",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total Tests | {total_tests} |",
        f"| Passed | {passed} |",
        f"| Failed | {failed} |",
        f"| Errors | {errors} |",
        f"| Pass Rate | {pass_rate}% |",
        "",
        "## Test Results",
        "",
        "| Test | Status | Duration |",
        "|------|--------|----------|",
    ]

    for result in results:
        name = result.get("name", "")
        test_status = result.get("status", "unknown")
        test_duration = result.get("duration", 0)

        emoji = {"passed": "✅", "failed": "❌", "error": "⚠️", "skipped": "⏭️"}.get(
            test_status, "❓"
        )

        lines.append(f"| {name} | {emoji} {test_status} | {test_duration}s |")

    lines.extend(
        [
            "",
            "---",
            f"*Generated by IoTix Test Engine on {datetime.now().isoformat()}*",
        ]
    )

    return "\n".join(lines)


def _escape_xml(text: str) -> str:
    """Escape special XML characters.

    Args:
        text: Text to escape

    Returns:
        Escaped text
    """
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )
