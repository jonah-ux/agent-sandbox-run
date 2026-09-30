# Explicit Command Isolation Runner

![explicit command isolation runner workflow](docs/header.svg)

**Run a command with visible limits and an honest receipt of what was enforced.**

## Install

```bash
pip install git+https://github.com/jonah-ux/agent-sandbox-run.git@v0.1.0
```

## Quick start

```bash
agent-sandbox --help
```

The first release is intentionally small, offline-friendly, and easy to inspect. JSON output is designed for agents; diagnostics stay explicit.

## Development

```bash
python -m unittest discover -s tests
python -m build --sdist --wheel
python demos/demo.py
```

## Limits

Read the command help and [release guide](docs/releasing.md) before using this in automation. This project does not claim permissions, isolation, verification, or provider behavior beyond the output fields it can prove.

MIT licensed. Contributions and sanitized bug reports are welcome.
