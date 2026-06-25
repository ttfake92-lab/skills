#!/usr/bin/env python3
"""Create a shareable report bundle from a college-application workspace.

The bundle contains the most important deliverables for handoff / demo:
- final-report.html
- personality-report.html
- research.json
- CANDIDATE.md
- SOURCES.md
- personality-assessment-result.json (if present)
- admission-info-result.json (if present)

This is intentionally simple: no compression, no external dependencies.
"""

import argparse
import shutil
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_BUNDLE_NAME = f"college-application-report-{datetime.now(timezone.utc).astimezone().date().isoformat()}"


def copy_if_exists(source, destination):
    if source.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        return True
    return False


def main():
    parser = argparse.ArgumentParser(description="Package a college-application report bundle")
    parser.add_argument("--workspace", required=True, help="Candidate workspace directory")
    parser.add_argument("--output", help="Output bundle directory; defaults to <workspace>/<bundle-name>")
    parser.add_argument("--bundle-name", default=DEFAULT_BUNDLE_NAME, help="Bundle directory name")
    parser.add_argument("--force", action="store_true", help="Overwrite bundle directory if it already exists")
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve() if args.output else workspace / args.bundle_name

    if output_path.exists() and not args.force:
        print(output_path)
        return

    if output_path.exists() and args.force:
        shutil.rmtree(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    core_files = [
        workspace / "final-report.html",
        workspace / "personality-report.html",
        workspace / "research.json",
        workspace / "CANDIDATE.md",
        workspace / "SOURCES.md",
        workspace / "PERSONALITY-REPORT.md",
        workspace / "CAREER-INDUSTRY-REPORT.md",
    ]

    optional_files = [
        workspace / "personality-assessment-result.json",
        workspace / "admission-info-result.json",
        workspace / "admission-info-result.demo.json",
        workspace / "personality-assessment-result.demo.json",
    ]

    copied = []
    for path in core_files + optional_files:
        if path.exists():
            copy_if_exists(path, output_path / path.name)
            copied.append(path.name)

    readme = output_path / "README.txt"
    readme.write_text(
        f"College Application Report Bundle\n\nGenerated from: {workspace}\nFiles: {', '.join(copied) or 'none'}\n", encoding="utf-8"
    )
    print(output_path)


if __name__ == "__main__":
    main()
