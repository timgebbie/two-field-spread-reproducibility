from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
required = [root / "config/default.yaml", root / "provenance/SCIENTIFIC-BOUNDARY.md"]
missing = [str(path) for path in required if not path.exists()]
if missing:
    raise SystemExit("Missing template files: " + ", ".join(missing))
subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(root / "tests"), "-v"], check=True)
print("v0.0.0 template route completed successfully.")
