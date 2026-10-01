"""Run bounded commands and emit honest, integrity-bound receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

VERSION = "0.2.0"


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(value: str | bytes) -> str:
    payload = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.sha256(payload).hexdigest()


def _bounded(value: str, limit: int) -> tuple[str, bool]:
    if len(value) <= limit:
        return value, False
    return value[:limit], True


def _receipt_digest(receipt: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    return _sha256(_canonical(unsigned))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agent-sandbox")
    commands = parser.add_subparsers(dest="command", required=True)
    run_parser = commands.add_parser("run")
    run_parser.add_argument("--root", default=".")
    run_parser.add_argument("--cwd", default=None, help="working directory for the command")
    run_parser.add_argument("--timeout", type=int, default=10)
    run_parser.add_argument("--max-output", type=int, default=16384)
    run_parser.add_argument("cmd", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    if args.timeout < 1 or args.max_output < 1:
        parser.error("--timeout and --max-output must be positive")

    command = args.cmd or ["/bin/echo", "sandbox demo"]
    root = str(Path(args.root).resolve())
    cwd = str(Path(args.cwd or root).resolve())
    backend = shutil.which("bwrap")
    enforced = bool(backend)
    if enforced:
        actual = [backend, "--ro-bind", root, "/workspace", "--chdir", "/workspace", "--proc", "/proc", "--dev", "/dev", "--unshare-net", "--", *command]
    else:
        actual = command

    started = time.time()
    timed_out = False
    try:
        result = subprocess.run(actual, text=True, capture_output=True, timeout=args.timeout, cwd=cwd)
        code, stdout, stderr = result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        code, stdout, stderr = 124, exc.stdout or "", "timeout"

    stdout, stdout_truncated = _bounded(stdout, args.max_output)
    stderr, stderr_truncated = _bounded(stderr, args.max_output)
    receipt = {
        "schema": "agent-sandbox/v2",
        "version": VERSION,
        "ok": code == 0 and not timed_out,
        "exit_code": code,
        "backend": "bubblewrap" if enforced else "fallback",
        "enforced": enforced,
        "timed_out": timed_out,
        "duration_ms": round((time.time() - started) * 1000),
        "command": command,
        "command_sha256": _sha256(_canonical(command)),
        "cwd": cwd,
        "root": root,
        "stdout": stdout,
        "stderr": stderr,
        "stdout_sha256": _sha256(stdout),
        "stderr_sha256": _sha256(stderr),
        "stdout_truncated": stdout_truncated,
        "stderr_truncated": stderr_truncated,
    }
    receipt["receipt_sha256"] = _receipt_digest(receipt)
    print(json.dumps(receipt, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
