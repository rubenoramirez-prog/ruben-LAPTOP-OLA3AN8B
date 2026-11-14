#!/usr/bin/env bash
# Tests for the modular Linux security auditor.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT="${ROOT_DIR}/scripts/bash/audit_vulnerabilities.sh"
TEST_OUTPUT="${ROOT_DIR}/reports/test_audit_script"

rm -rf "$TEST_OUTPUT"
mkdir -p "$TEST_OUTPUT"

bash -n "$SCRIPT"

set +e
bash "$SCRIPT" \
  --modules auth,ssh \
  --client "Test Client" \
  --output-dir "$TEST_OUTPUT" \
  --quiet
AUDIT_RC=$?
set -e

# A real audit may return non-zero when findings exist; that is expected.
if [[ "$AUDIT_RC" -ne 0 && "$AUDIT_RC" -ne 1 ]]; then
  echo "Unexpected auditor exit code: $AUDIT_RC" >&2
  exit 1
fi

python - "$TEST_OUTPUT" <<'PY'
import json
import pathlib
import sys

output = pathlib.Path(sys.argv[1])
json_path = output / "audit_report.json"
html_path = output / "client_dashboard.html"

if not json_path.is_file():
    raise SystemExit("JSON report was not generated")
if not html_path.is_file():
    raise SystemExit("HTML dashboard was not generated")

data = json.loads(json_path.read_text(encoding="utf-8"))
summary = data["summary"]
findings = data["findings"]

assert data["audit_metadata"]["client"] == "Test Client"
assert summary["total_controls"] == len(findings)
assert summary["passed"] + summary["failed"] == summary["total_controls"]
assert 0 <= summary["security_score_percent"] <= 100
assert "AUDIT_DATA" in html_path.read_text(encoding="utf-8")
print(f"Audit report valid: {len(findings)} findings, score={summary['security_score_percent']}%")
PY

rm -rf "$TEST_OUTPUT"
echo "Modular auditor tests passed"
