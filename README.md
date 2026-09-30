# Agent Sandbox Run

![explicit command isolation runner workflow](docs/header.svg)

**Run a command with visible limits and an honest receipt of what was enforced.**

[![CI](https://github.com/jonah-ux/agent-sandbox-run/actions/workflows/ci.yml/badge.svg)](https://github.com/jonah-ux/agent-sandbox-run/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-3776ab)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-22c55e)](LICENSE)

Agent Sandbox Run executes a command and emits a JSON receipt showing the exit code, duration,
stdout, timeout behavior, and whether bubblewrap was actually available as the backend. The
fallback is intentionally visible instead of being described as isolation.

## Try it in 30 seconds

```bash
python -m pip install git+https://github.com/jonah-ux/agent-sandbox-run.git@main
python demos/demo.py
```

Run a bounded command and inspect the receipt:

```bash
agent-sandbox run --timeout 5 /bin/echo hello
```

## See it work

The receipt names the backend and whether isolation was actually enforced:

```json
{"schema":"agent-sandbox/v1","ok":true,"backend":"fallback","enforced":false,"exit_code":0,"stdout":"hello from the sandbox\n"}
```

## Related tools

Use [Agent Policy](https://github.com/jonah-ux/agent-policy) before deciding whether a command may run, [Agent Proof](https://github.com/jonah-ux/agent-proof) to archive the receipt, and [MCP Doctor](https://github.com/jonah-ux/mcp-doctor) to inspect the tools an agent can call.

Look for `backend`, `enforced`, `exit_code`, and `duration_ms` in the `agent-sandbox/v1`
result. A fallback execution is still useful evidence, but it is not isolation.

## Development

```bash
python -m unittest discover -s tests
python -m build --sdist --wheel
python demos/demo.py
```

Read [SECURITY.md](SECURITY.md) before using this around untrusted commands. Treat the receipt
as an observation of this process, not a system security guarantee.

MIT licensed.
