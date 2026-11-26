"""Offline tests for the fail-closed Shad worker scaffold."""
from __future__ import annotations

import contextlib
import io
import os
import unittest
from unittest.mock import patch

import shad_worker


class ShadWorkerTests(unittest.TestCase):
    def run_main(self, **overrides: str) -> tuple[int, str, str]:
        values = {
            "SHAD_ENABLED": "false",
            "SHAD_DRY_RUN": "true",
            "SHAD_AUTO_REPLY": "false",
            "SHAD_GROUP_NAME": "ریاضی۱-۱۰۱",
            "SHAD_GROUP_GUID": "g0DhwiT05ffedba9a45513dfcfe78f72",
            "SHAD_SESSION_DIR": "/tmp/shad-test-session",
        }
        values.update(overrides)
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.dict(os.environ, values, clear=True):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                code = shad_worker.main()
        return code, stdout.getvalue(), stderr.getvalue()

    def test_disabled_by_default_does_not_connect(self) -> None:
        code, out, err = self.run_main(SHAD_ENABLED="false")
        self.assertEqual(code, 0)
        self.assertIn("disabled", out)
        self.assertIn("ریاضی۱-۱۰۱", out)
        self.assertEqual(err, "")

    def test_enabled_dry_run_still_blocks_network_polling(self) -> None:
        code, out, err = self.run_main(SHAD_ENABLED="true", SHAD_DRY_RUN="true")
        self.assertEqual(code, 0)
        self.assertIn("network polling is blocked", out)
        self.assertEqual(err, "")

    def test_missing_group_refuses_to_start(self) -> None:
        code, _, err = self.run_main(SHAD_ENABLED="true", SHAD_GROUP_GUID="")
        self.assertEqual(code, 2)
        self.assertIn("SHAD_GROUP_GUID", err)

    def test_live_mode_is_refused(self) -> None:
        code, _, err = self.run_main(
            SHAD_ENABLED="true",
            SHAD_DRY_RUN="false",
            SHAD_AUTO_REPLY="true",
        )
        self.assertEqual(code, 3)
        self.assertIn("Refusing live operation", err)

    def test_invalid_boolean_is_rejected(self) -> None:
        with patch.dict(os.environ, {"SHAD_ENABLED": "maybe"}, clear=True):
            with self.assertRaises(ValueError):
                shad_worker.env_bool("SHAD_ENABLED")


if __name__ == "__main__":
    unittest.main()
