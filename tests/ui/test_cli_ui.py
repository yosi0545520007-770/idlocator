﻿﻿﻿"""בדיקות UI בסיסיות לממשק ה-CLI של הפרויקט."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
import unittest

ROOT_DIR = Path(__file__).resolve().parents[2]


class CLITestCase(unittest.TestCase):
    """בדיקות ממשק משתמש דרך שורת הפקודה."""

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"  # Force subprocess to use UTF-8
        command = [sys.executable, "-m", "idlocator.cli", *args]
        return subprocess.run(
            command,
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",  # Expect UTF-8 output
            env=env,
        )

    def test_cli_returns_result_for_known_id(self) -> None:
        # This ID exists in sample_people_20.csv which is the default for cli
        result = self.run_cli("--id", "200000001")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("תעודת זהות: 200000001", result.stdout)

    def test_cli_no_results_message(self) -> None:
        result = self.run_cli("--id", "000000000")
        # We check for the message in stdout. The exit code could be 1 for other errors too.
        self.assertEqual(result.returncode, 1, msg=f"Expected return code 1 for no results, but got {result.returncode}. Stderr: {result.stderr}")
        self.assertIn("לא נמצאו תוצאות", result.stdout)


if __name__ == "__main__":
    unittest.main()
