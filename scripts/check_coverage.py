"""Check that each file meets minimum coverage threshold."""
import json
import sys
from pathlib import Path

# ruff: noqa: T201


def check_file_coverage(coverage_file: Path, threshold: float = 80.0) -> bool:
    """Check if all files meet the coverage threshold."""
    with coverage_file.open() as f:
        data = json.load(f)

    files = data.get("files", {})
    failed_files = []

    for filepath, stats in files.items():
        coverage = stats["summary"]["percent_covered"]
        if coverage < threshold:
            failed_files.append((filepath, coverage))

    if failed_files:
        print(f"\n❌ Files below {threshold}% coverage:")
        for filepath, coverage in sorted(failed_files, key=lambda x: x[1]):
            print(f"  {filepath}: {coverage:.2f}%")
        return False

    print(f"\n✅ All files meet {threshold}% coverage threshold")
    return True


if __name__ == "__main__":
    threshold = float(sys.argv[1]) if len(sys.argv) > 1 else 80.0
    success = check_file_coverage(Path("coverage.json"), threshold)
    sys.exit(0 if success else 1)
