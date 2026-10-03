# Agent Systems Lab sandbox conformance

Agent Sandbox Run remains the owner of `agent-sandbox/v2`. This fixture and test
make its native receipt boundary explicit without importing Agent Policy or Agent
Proof at runtime.

The owner proves that every receipt discloses the backend and `enforced` state,
keeps command/output identity hashes, bounds output, and preserves timeout as a
failed/unknown observation. The manifest records Agent Proof's existing
`agent-proof/interop/v1` adapter as the downstream handoff owner, pinned to the
reviewed Agent Proof manifest revision and SHA-256; it does not create a second
registry.

Run `python -m unittest discover -s tests` or the focused conformance test from
a fresh checkout. The fixtures execute only `/bin/echo` and a bounded synthetic
sleep command.
