import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "src" / "training" / "pipeline.py"


def main():
    print("=== AutoMLOps Lab ===", flush=True)
    print("Starting training and evaluation pipeline...", flush=True)

    result = subprocess.run(
        [sys.executable, "-m", "src.training.pipeline"],
        cwd=ROOT,
        check=False,
    )

    if result.returncode != 0:
        print("Pipeline failed.", flush=True)
        raise SystemExit(result.returncode)

    print("Pipeline completed successfully.", flush=True)


if __name__ == "__main__":
    main()
