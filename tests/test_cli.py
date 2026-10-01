import contextlib
import io
import json
import unittest

from agent_sandbox_run.cli import _receipt_digest, main


class SandboxTests(unittest.TestCase):
    def run_cli(self, *args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(list(args))
        return code, json.loads(output.getvalue())

    def test_receipt_is_bound_to_command_and_output(self):
        code, receipt = self.run_cli("run", "/bin/echo", "hello")
        self.assertEqual(code, 0)
        self.assertEqual(receipt["schema"], "agent-sandbox/v2")
        self.assertEqual(receipt["stdout"], "hello\n")
        self.assertEqual(receipt["receipt_sha256"], _receipt_digest(receipt))
        self.assertEqual(len(receipt["command_sha256"]), 64)

    def test_output_is_bounded_and_digest_is_explicit(self):
        code, receipt = self.run_cli("run", "--max-output", "4", "/bin/echo", "abcdefgh")
        self.assertEqual(code, 0)
        self.assertEqual(receipt["stdout"], "abcd")
        self.assertTrue(receipt["stdout_truncated"])
        self.assertEqual(len(receipt["stdout_sha256"]), 64)

    def test_timeout_is_fail_closed(self):
        code, receipt = self.run_cli("run", "--timeout", "1", "/bin/sh", "-c", "sleep 2")
        self.assertEqual(code, 124)
        self.assertFalse(receipt["ok"])
        self.assertTrue(receipt["timed_out"])
        self.assertEqual(receipt["exit_code"], 124)


if __name__ == "__main__":
    unittest.main()
