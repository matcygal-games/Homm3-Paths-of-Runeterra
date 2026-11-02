"""Run contributor checks, with an offline smoke check in public checkouts."""
import ast
from pathlib import Path
import subprocess
import sys
import unittest


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / "matt_dev" / "tests"
    if not directory.is_dir():
        for name in ("cli.py", "play.py", "publication_audit.py", "public_source.py", "authoring.py"):
            path = root / "dev" / name
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        result = subprocess.run([sys.executable, "-B", "-m", "dev", "--help"], cwd=root,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode:
            print(result.stderr, file=sys.stderr)
            return result.returncode
        print("Public smoke checks passed. The extended test suite requires separate maintainer inputs.")
        return 0
    suite = unittest.TestSuite()
    for pattern in ("test_developer_workflow.py", "test_public_source.py",
                    "test_provenance.py", "test_engine_source.py", "test_manual_zip.py"):
        suite.addTests(unittest.defaultTestLoader.discover(str(directory), pattern=pattern))
    return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
