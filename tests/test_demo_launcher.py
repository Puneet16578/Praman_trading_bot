"""Exercise the PowerShell launcher with a fake Python command, never a server."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


class DemoLauncherTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which("powershell"), "PowerShell required")
    def test_launcher_passes_localhost_from_another_directory(self):
        launcher = Path(__file__).resolve().parents[1] / "demo" / "run_demo.ps1"
        quoted = str(launcher).replace("'", "''")
        command = (
            "function python { $global:LASTEXITCODE = 0; "
            "$args | ConvertTo-Json -Compress }; & '" + quoted + "'"
        )
        with tempfile.TemporaryDirectory() as other_folder:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
                cwd=other_folder, capture_output=True, text=True, check=True,
            )
        self.assertEqual(json.loads(result.stdout), [
            "-m", "streamlit", "run", str(launcher.with_name("Home.py")),
            "--server.address", "localhost",
        ])
