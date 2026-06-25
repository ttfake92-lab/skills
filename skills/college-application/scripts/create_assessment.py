#!/usr/bin/env python3
"""Create a fillable personality assessment form for a candidate workspace.

Default output is a static HTML form that users can open in a browser and use to
export JSON/Markdown results for the Agent. Markdown output remains available as
an accessibility/fallback mode.
"""

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_HTML_TEMPLATE = SKILL_DIR / "assets" / "personality-assessment-form.html"
DEFAULT_MD_TEMPLATE = SKILL_DIR / "assets" / "personality-assessment-template.md"


def today():
    return datetime.now(timezone.utc).astimezone().date().isoformat()


def open_file(path):
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False)
        elif sys.platform.startswith("win"):
            subprocess.run(["cmd", "/c", "start", "", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path)], check=False)
    except OSError:
        pass


def main():
    parser = argparse.ArgumentParser(description="Create a fillable personality assessment form")
    parser.add_argument("--workspace", required=True, help="Candidate workspace directory")
    parser.add_argument("--format", choices=("html", "md"), default="html", help="Output format; defaults to html")
    parser.add_argument("--template", help="Template path; defaults to the skill's HTML or Markdown template")
    parser.add_argument("--output", help="Output path; defaults to <workspace>/personality-assessment-YYYY-MM-DD.<format>")
    parser.add_argument("--force", action="store_true", help="Overwrite output if it already exists")
    parser.add_argument("--open", action="store_true", help="Open the generated file with the system default app")
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    template_path = Path(args.template).expanduser().resolve() if args.template else (DEFAULT_HTML_TEMPLATE if args.format == "html" else DEFAULT_MD_TEMPLATE)
    output_path = Path(args.output).expanduser().resolve() if args.output else workspace / f"personality-assessment-{today()}.{args.format}"

    if not template_path.exists():
        raise SystemExit(f"template does not exist: {template_path}")

    workspace.mkdir(parents=True, exist_ok=True)
    if not output_path.exists() or args.force:
        content = template_path.read_text(encoding="utf-8")
        if args.format == "md":
            content = (
                "<!--\n"
                "This file was generated from assets/personality-assessment-template.md.\n"
                "Fill the score columns, save the file, then return it to the Agent.\n"
                "Do not edit the scoring rules unless you intentionally change the assessment design.\n"
                "-->\n\n"
                + content
            )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")

    if args.open:
        open_file(output_path)
    print(output_path)


if __name__ == "__main__":
    main()
