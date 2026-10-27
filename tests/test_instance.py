"""Regressões do bloqueio real de arquivos entre processos no Windows."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from narrador.instance import instanceLock
from narrador.paths import ROOT

childCode = """
import sys
from pathlib import Path
from narrador.instance import AppAlreadyRunningError, instanceLock
try:
    with instanceLock(Path(sys.argv[1])):
        print('ACQUIRED')
except AppAlreadyRunningError:
    print('ALREADY_RUNNING')
"""


class InstanceTests(unittest.TestCase):
    def setUp(self):
        cacheDirectory = (ROOT / ".cache").resolve()
        self.temporaryDirectory = tempfile.TemporaryDirectory(
            prefix="instance-tests-", dir=cacheDirectory
        )
        testDirectory = Path(self.temporaryDirectory.name).resolve()
        self.assertIn(cacheDirectory, testDirectory.parents)
        self.addCleanup(self.temporaryDirectory.cleanup)
        self.lockPath = testDirectory / ".app.lock"

    def childStatus(self):
        result = subprocess.run(
            [sys.executable, "-c", childCode, str(self.lockPath)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=15,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        return result.stdout.strip()

    def testFirstStartCanLockEmptyFile(self):
        self.assertEqual(self.childStatus(), "ACQUIRED")
        self.assertEqual(self.lockPath.stat().st_size, 0)

    def testSecondProcessRecognizesExistingLockedByte(self):
        self.lockPath.write_bytes(b"0")
        with instanceLock(self.lockPath):
            self.assertEqual(self.childStatus(), "ALREADY_RUNNING")
        self.assertEqual(self.childStatus(), "ACQUIRED")

    def testExceptionReleasesLock(self):
        with self.assertRaisesRegex(RuntimeError, "falha simulada"):
            with instanceLock(self.lockPath):
                raise RuntimeError("falha simulada")
        self.assertEqual(self.childStatus(), "ACQUIRED")


if __name__ == "__main__":
    unittest.main()
