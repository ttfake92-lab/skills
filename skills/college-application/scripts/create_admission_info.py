#!/usr/bin/env python3
"""Create a fillable gaokao admission information form.

Default output is a static HTML form that users can open in a browser and use to
export JSON/Markdown results for the Agent. Markdown output remains available as
a fallback mode.
"""

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_HTML_TEMPLATE = SKILL_DIR / "assets" / "admission-info-form.html"
DEFAULT_MD_TEMPLATE = SKILL_DIR / "assets" / "admission-info-template.md"


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
    parser = argparse.ArgumentParser(description="Create a fillable gaokao admission information form")
    parser.add_argument("--workspace", required=True, help="Candidate workspace directory")
    parser.add_argument("--format", choices=("html", "md"), default="html", help="Output format; defaults to html")
    parser.add_argument("--template", help="Template path; defaults to the skill's HTML or Markdown template")
    parser.add_argument("--output", help="Output path; defaults to <workspace>/admission-info-YYYY-MM-DD.<format>")
    parser.add_argument("--force", action="store_true", help="Overwrite output if it already exists")
    parser.add_argument("--open", action="store_true", help="Open the generated file with the system default app")
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    template_path = Path(args.template).expanduser().resolve() if args.template else (DEFAULT_HTML_TEMPLATE if args.format == "html" else DEFAULT_MD_TEMPLATE)
    output_path = Path(args.output).expanduser().resolve() if args.output else workspace / f"admission-info-{today()}.{args.format}"

    if not template_path.exists():
        raise SystemExit(f"template does not exist: {template_path}")

    workspace.mkdir(parents=True, exist_ok=True)
    if not output_path.exists() or args.force:
        content = template_path.read_text(encoding="utf-8")
        if args.format == "md":
            content = (
                "<!--\n"
                "This file was generated from assets/admission-info-template.md.\n"
                "Fill the '你的填写' column, save the file, then return it to the Agent.\n"
                "Do not treat this as an official application form.\n"
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
