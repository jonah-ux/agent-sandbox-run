"""Run bounded commands and emit honest, integrity-bound receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import signal
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


def _run_process(
    command: list[str],
    *,
    cwd: str,
    timeout: int,
) -> tuple[int, str, str, bool, str | None]:
    """Run one process and terminate its entire session on timeout.

    The extra spawn-error value lets the caller distinguish a command's non-zero
    result from a backend that could not be started at all.
    """

    try:
        process = subprocess.Popen(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            start_new_session=True,
        )
    except OSError as exc:
        return 127, "", str(exc), False, str(exc)

    try:
        stdout, stderr = process.communicate(timeout=timeout)
        return process.returncode, stdout or "", stderr or "", False, None
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        stdout, stderr = process.communicate()
        return 124, stdout or "", (stderr or "") or "timeout", True, None


def _probe_backend(
    backend: str,
    *,
    root: str,
    cwd: str,
    timeout: int,
) -> tuple[bool, int, str]:
    """Check that the detected backend can create its declared boundary."""

    probe = [
        backend,
        "--ro-bind",
        root,
        "/workspace",
        "--chdir",
        "/workspace",
        "--proc",
        "/proc",
        "--dev",
        "/dev",
        "--unshare-net",
        "--",
        "/bin/true",
    ]
    code, _stdout, _stderr, timed_out, spawn_error = _run_process(
        probe,
        cwd=cwd,
        timeout=min(timeout, 5),
    )
    if timed_out:
        return False, code, "probe_timeout"
    if spawn_error:
        return False, code, "probe_spawn_error"
    if code != 0:
        return False, code, "probe_exit"
    return True, code, ""


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
    backend_detected = bool(backend)
    backend_attempted = False
    backend_failed = False
    backend_failure_reason: str | None = None
    backend_probe_exit_code: int | None = None
    enforced = False
    if backend:
        backend_attempted = True
        usable, backend_probe_exit_code, backend_failure_reason = _probe_backend(
            backend,
            root=root,
            cwd=cwd,
            timeout=args.timeout,
        )
        if usable:
            enforced = True
            backend_failure_reason = None
    if enforced:
        actual = [backend, "--ro-bind", root, "/workspace", "--chdir", "/workspace", "--proc", "/proc", "--dev", "/dev", "--unshare-net", "--", *command]
    else:
        if backend_attempted and backend_failure_reason:
            backend_failed = True
        actual = command

    started = time.time()
    code, stdout, stderr, timed_out, spawn_error = _run_process(actual, cwd=cwd, timeout=args.timeout)
    if spawn_error and enforced:
        backend_failed = True
        backend_failure_reason = "execution_spawn_error"
        enforced = False
        actual = command
        code, stdout, stderr, timed_out, _spawn_error = _run_process(actual, cwd=cwd, timeout=args.timeout)

    stdout, stdout_truncated = _bounded(stdout, args.max_output)
    stderr, stderr_truncated = _bounded(stderr, args.max_output)
    receipt = {
        "schema": "agent-sandbox/v2",
        "version": VERSION,
        "ok": code == 0 and not timed_out,
        "exit_code": code,
        "backend": "bubblewrap" if enforced else "fallback",
        "enforced": enforced,
        "backend_detected": backend_detected,
        "backend_attempted": backend_attempted,
        "backend_failed": backend_failed,
        "backend_failure_reason": backend_failure_reason,
        "backend_probe_exit_code": backend_probe_exit_code,
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
