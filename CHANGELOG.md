# Changelog

## Unreleased

- Add integrity-bound v2 receipts with command/output digests and bounded output capture.
- Add explicit timeout state, working-directory readback, focused tests, and bump the source candidate to 0.2.0.
- Probe a detected bubblewrap backend before claiming enforcement and report additive backend
  discovery, attempt, failure, and probe-exit fields when falling back.
- Run commands in fresh process sessions and terminate the full session when a timeout fires.

## 0.1.0 - 2026-09-30

Initial focused release with a stable CLI contract and synthetic demo.
