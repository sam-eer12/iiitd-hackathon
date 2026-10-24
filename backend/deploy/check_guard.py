"""Run CloudFormation Guard against both rendered templates."""

import json
from pathlib import Path

import guardpycfn

root = Path(__file__).parent
failed = False
for path in sorted((root / "templates").glob("*.json")):
    result = guardpycfn.validate_with_guard(
        path.read_text(), (root / "security.guard").read_text(), verbose=True
    )
    if isinstance(result, str):
        result = json.loads(result)
    status = result.get("result", {}).get("container", {}).get("FileCheck", {}).get("status")
    report = Path("/private/tmp") if Path("/private/tmp").exists() else Path("/tmp")
    (report / f"tenderlens-guard-{path.stem}.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({"template": path.name, "status": status, "success": result.get("success")}))
    failed = failed or not result.get("success") or status != "PASS"
raise SystemExit(1 if failed else 0)
