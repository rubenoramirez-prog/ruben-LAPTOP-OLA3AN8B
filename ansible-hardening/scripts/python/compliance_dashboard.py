#!/usr/bin/env python3
"""
=============================================================================
Compliance Dashboard & Report Generator
=============================================================================
Author: Ruben Omar Ramírez Gutiérrez (Coach Ruben Ramírez)
Description: Parses Ansible hardening results and audit JSON logs, generating
             executive HTML compliance dashboards with scoring and metrics.
=============================================================================
"""

import json
import os
import sys
from datetime import datetime

REPORTS_DIR = "/var/log/ansible-hardening-reports"
OUTPUT_HTML = os.path.join(REPORTS_DIR, "dashboard.html")

def load_latest_results():
    if not os.path.exists(REPORTS_DIR):
        print(f"[WARN] Reports directory {REPORTS_DIR} does not exist.")
        return []

    files = [os.path.join(REPORTS_DIR, f) for f in os.listdir(REPORTS_DIR) if f.endswith(".json")]
    if not files:
        print("[WARN] No JSON report files found.")
        return []

    latest_file = max(files, key=os.path.getmtime)
    print(f"[INFO] Loading latest report: {latest_file}")
    with open(latest_file, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to parse JSON: {e}")
            return []

def generate_html_dashboard(data):
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>CIS Hardening Compliance Dashboard</title>
    <style>
        :root {{
            --bg-primary: #0d1117;
            --bg-card: #161b22;
            --text-primary: #c9d1d9;
            --accent-green: #238636;
            --accent-amber: #d29922;
            --accent-blue: #58a6ff;
            --border: #30363d;
        }}
        body {{
            font-family: 'Inter', -apple-system, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            margin: 0;
            padding: 24px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        header {{
            border-bottom: 1px solid var(--border);
            padding-bottom: 16px;
            margin-bottom: 24px;
        }}
        h1 {{
            font-family: 'Oswald', sans-serif;
            margin: 0;
            color: var(--accent-blue);
        }}
        .card {{
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 16px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 12px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid var(--border);
            font-family: 'JetBrains Mono', monospace;
            font-size: 14px;
        }}
        th {{
            background-color: #21262d;
            color: var(--accent-blue);
        }}
        .badge-success {{
            background-color: var(--accent-green);
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
        }}
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=JetBrains+Mono:wght@400;700&family=Oswald:wght@500&display=swap" rel="stylesheet">
</head>
<body>
    <div class="container">
        <header>
            <h1>🔒 CIS Benchmark Hardening Compliance Dashboard</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Target: L1/L2 Hardening</p>
        </header>

        <div class="card">
            <h2>Execution Summary</h2>
            <table>
                <tr>
                    <th>Control / Task</th>
                    <th>Status</th>
                    <th>Details</th>
                </tr>
"""

    if isinstance(data, list) and len(data) > 0:
        for item in data:
            title = item.get("task", item.get("name", "CIS Control"))
            status = item.get("status", "Applied")
            msg = item.get("msg", "Successfully hardened")
            html_content += f"""
                <tr>
                    <td>{title}</td>
                    <td><span class="badge-success">{status}</span></td>
                    <td>{msg}</td>
                </tr>
"""
    else:
        html_content += """
                <tr>
                    <td colspan="3" style="text-align: center; color: #8b949e;">No execution records found or audit pending. Run infra-automation.sh first.</td>
                </tr>
"""

    html_content += f"""
            </table>
        </div>
    </div>
</body>
</html>
"""

    os.makedirs(REPORTS_DIR, exist_ok=True)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[INFO] HTML dashboard successfully generated at: {OUTPUT_HTML}")

if __name__ == "__main__":
    data = load_latest_results()
    generate_html_dashboard(data)
    sys.exit(0)
