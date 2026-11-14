#!/usr/bin/env python3
"""
Enterprise CIS Benchmark Security Scanner (RHEL 8/9)
Author: Ruben Omar Ramírez Gutiérrez
Standard: Enterprise L3 Infrastructure / Zero external dependencies (Agentless)
"""

import sys
import os
import subprocess
import argparse
import json
import datetime
from typing import Dict, Any, List

def run_cmd(cmd: List[str]) -> str:
    """Safely runs a system command and returns stdout stripped."""
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        return res.stdout.strip()
    except Exception:
        return ""

def check_sysctl(param: str, expected_val: str) -> Dict[str, Any]:
    actual = run_cmd(["sysctl", "-n", param])
    passed = (actual == expected_val)
    return {
        "parameter": param,
        "expected": expected_val,
        "actual": actual or "unset",
        "passed": passed
    }

def check_service_disabled(service: str) -> Dict[str, Any]:
    status = run_cmd(["systemctl", "is-active", service])
    passed = (status != "active")
    return {
        "service": service,
        "status": status if status else "not-running",
        "passed": passed
    }

def run_all_checks() -> Dict[str, Any]:
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    hostname = run_cmd(["hostname"]) or "unknown-host"

    checks = []

    # 1. Sysctl security parameters
    sysctl_tests = [
        ("kernel.randomize_va_space", "2", "1.5.1 ASLR Enabled"),
        ("fs.suid_dumpable", "0", "1.5.2 Restrict Core Dumps"),
        ("net.ipv4.ip_forward", "0", "3.2.1 Disable IP Forwarding"),
        ("net.ipv4.conf.all.send_redirects", "0", "3.2.2 Disable Send Redirects"),
        ("net.ipv4.conf.all.accept_source_route", "0", "3.2.3 Disable Source Route IPv4"),
        ("net.ipv4.conf.all.accept_redirects", "0", "3.2.4 Disable ICMP Redirects IPv4"),
        ("net.ipv4.tcp_syncookies", "1", "3.2.10 Enable TCP SYN Cookies"),
        ("net.ipv4.conf.all.rp_filter", "1", "3.2.9 Enable Reverse Path Filtering")
    ]

    for param, expected, desc in sysctl_tests:
        res = check_sysctl(param, expected)
        checks.append({
            "id": desc.split()[0],
            "description": desc,
            "category": "Kernel / Network",
            "passed": res["passed"],
            "details": f"actual={res['actual']}, expected={res['expected']}"
        })

    # 2. Insecure Services
    insecure_services = [
        "telnet.socket", "telnet-server", "rsh.socket", "rlogin.socket",
        "vsftpd", "httpd", "nginx", "dovecot", "smb", "squid", "snmpd"
    ]
    for srv in insecure_services:
        res = check_service_disabled(srv)
        checks.append({
            "id": f"srv_{srv}",
            "description": f"Service {srv} should not be active",
            "category": "Services",
            "passed": res["passed"],
            "details": f"status={res['status']}"
        })

    # 3. SELinux Check
    se_state = run_cmd(["getenforce"])
    checks.append({
        "id": "1.6.1.2",
        "description": "SELinux Enforcing Mode",
        "category": "Mandatory Access Control",
        "passed": (se_state == "Enforcing"),
        "details": f"state={se_state or 'disabled'}"
    })

    # 4. SSHD Configuration check
    sshd_config_path = "/etc/ssh/sshd_config"
    prl_pass = False
    prl_val = "not-found"
    if os.path.exists(sshd_config_path):
        try:
            with open(sshd_config_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("PermitRootLogin"):
                        parts = line.split()
                        if len(parts) > 1:
                            prl_val = parts[1]
                            prl_pass = prl_val.lower() in ["no", "prohibit-password"]
        except Exception as e:
            prl_val = f"error: {e}"

    checks.append({
        "id": "5.2.8",
        "description": "SSH PermitRootLogin is disabled",
        "category": "Access Control / SSH",
        "passed": prl_pass,
        "details": f"PermitRootLogin={prl_val}"
    })

    passed_count = sum(1 for c in checks if c["passed"])
    total_count = len(checks)
    score = round((passed_count / total_count * 100), 2) if total_count > 0 else 0

    return {
        "scanner": "Enterprise CIS Scanner",
        "version": "1.0.0",
        "timestamp": timestamp,
        "host": hostname,
        "summary": {
            "total": total_count,
            "passed": passed_count,
            "failed": total_count - passed_count,
            "score_percent": score
        },
        "checks": checks
    }

def generate_html_report(data: Dict[str, Any]) -> str:
    summary = data["summary"]
    checks = data["checks"]
    score_color = "#22c55e" if summary["score_percent"] >= 80 else ("#eab308" if summary["score_percent"] >= 60 else "#ef4444")

    rows = ""
    for c in checks:
        badge = '<span style="color:#22c55e;font-weight:bold;">PASS</span>' if c["passed"] else '<span style="color:#ef4444;font-weight:bold;">FAIL</span>'
        rows += f"""
        <tr>
            <td style="padding:8px;border-bottom:1px solid #334155;">{c['id']}</td>
            <td style="padding:8px;border-bottom:1px solid #334155;">{c['category']}</td>
            <td style="padding:8px;border-bottom:1px solid #334155;">{c['description']}</td>
            <td style="padding:8px;border-bottom:1px solid #334155;">{badge}</td>
            <td style="padding:8px;border-bottom:1px solid #334155;font-family:monospace;">{c['details']}</td>
        </tr>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CIS Hardening Audit Report - {data['host']}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 24px; margin: 0; }}
  .card {{ background: #1e293b; border-radius: 8px; padding: 20px; margin-bottom: 24px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }}
  .score {{ font-size: 48px; font-weight: bold; color: {score_color}; }}
  table {{ width: 100%; border-collapse: collapse; text-align: left; }}
  th {{ background: #334155; padding: 12px 8px; color: #cbd5e1; }}
</style>
</head>
<body>
  <div class="card">
    <h1>Enterprise CIS Benchmark Audit Report</h1>
    <p>Host: <strong>{data['host']}</strong> | Generated: <strong>{data['timestamp']}</strong></p>
    <div>Compliance Score: <span class="score">{summary['score_percent']}%</span> ({summary['passed']}/{summary['total']} Passed)</div>
  </div>
  <div class="card">
    <table>
      <thead>
        <tr><th>ID</th><th>Category</th><th>Description</th><th>Status</th><th>Details</th></tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
  </div>
</body>
</html>"""

def main():
    parser = argparse.ArgumentParser(description="Enterprise CIS Security Scanner for RHEL")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    parser.add_argument("--html", type=str, default="", help="Generate HTML report at given file path")
    args = parser.parse_args()

    results = run_all_checks()

    if args.html:
        html_content = generate_html_report(results)
        with open(args.html, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"HTML report successfully written to {args.html}")

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        summary = results["summary"]
        print("====================================================")
        print("            CIS SECURITY SCAN SUMMARY               ")
        print("====================================================")
        print(f"Host:       {results['host']}")
        print(f"Total:      {summary['total']}")
        print(f"Passed:     {summary['passed']}")
        print(f"Failed:     {summary['failed']}")
        print(f"Score:      {summary['score_percent']}%")
        print("====================================================")

    if results["summary"]["failed"] > 0:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
