import json
from pathlib import Path

from agent_sandbox_run.cli import _receipt_digest, main


FIXTURE = Path(__file__).parent / "../conformance/agent-systems-lab.json"


def run_receipt(*args):
    import contextlib
    import io

    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = main(list(args))
    return code, json.loads(output.getvalue())


def test_manifest_pins_native_owner_and_shared_adapter():
    manifest = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert manifest["schema"] == "agent-systems-lab-sandbox-conformance/v1"
    assert manifest["owner"] == "agent-sandbox-run"
    assert manifest["native_schema"] == "agent-sandbox/v2"
    assert manifest["shared_adapter"]["schema"] == "agent-proof/interop/v1"
    assert len(manifest["cases"]) == 5
    assert manifest["privacy"]["raw_output_bounded"] is True


def test_receipt_exposes_enforcement_and_integrity_fields():
    code, receipt = run_receipt("run", "/bin/echo", "synthetic")
    assert code == 0
    assert receipt["schema"] == "agent-sandbox/v2"
    assert receipt["ok"] is True
    assert receipt["backend"] in {"bubblewrap", "fallback"}
    assert isinstance(receipt["enforced"], bool)
    assert len(receipt["command_sha256"]) == 64
    assert len(receipt["receipt_sha256"]) == 64
    assert receipt["receipt_sha256"] == _receipt_digest(receipt)


def test_bounded_output_and_timeout_preserve_unknown_failure_signals():
    code, bounded = run_receipt("run", "--max-output", "4", "/bin/echo", "abcdefgh")
    assert code == 0
    assert bounded["stdout"] == "abcd"
    assert bounded["stdout_truncated"] is True

    code, timeout = run_receipt("run", "--timeout", "1", "/bin/sh", "-c", "sleep 2")
    assert code == 124
    assert timeout["ok"] is False
    assert timeout["timed_out"] is True
    assert timeout["exit_code"] == 124
