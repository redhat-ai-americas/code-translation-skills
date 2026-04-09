#!/usr/bin/env python3
"""Render a spec JSON file into Markdown for human review.

Usage:
    python spec-schema/render.py path/to/spec.json
    python spec-schema/render.py path/to/spec.json --output review.md
    python spec-schema/render.py path/to/spec.json --template custom.md.j2
"""

import argparse
import json
import sys
from pathlib import Path

from jinja2 import ChainableUndefined, Environment, FileSystemLoader

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
DEFAULT_TEMPLATE = "spec-review.md.j2"
SCHEMA_PATH = Path(__file__).resolve().parent / "spec.schema.json"


def validate_spec(spec: dict) -> list[str]:
    """Validate spec against JSON schema. Returns list of error messages."""
    try:
        import jsonschema
    except ImportError:
        return ["jsonschema not installed, skipping validation"]

    try:
        schema = json.loads(SCHEMA_PATH.read_text())
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        return [f"could not load schema: {exc}"]

    errors = []
    validator = jsonschema.Draft202012Validator(schema)
    for error in validator.iter_errors(spec):
        path = ".".join(str(p) for p in error.absolute_path) or "(root)"
        errors.append(f"{path}: {error.message}")
    return errors


def render(spec: dict, template_path: Path | None = None) -> str:
    """Render a spec dict to Markdown using the Jinja2 template."""
    loader_dir = str(template_path.parent) if template_path else str(TEMPLATE_DIR)
    template_name = template_path.name if template_path else DEFAULT_TEMPLATE

    env = Environment(
        loader=FileSystemLoader(loader_dir),
        keep_trailing_newline=True,
        undefined=ChainableUndefined,  # missing vars become empty, chainable
    )

    template = env.get_template(template_name)
    return template.render(**spec)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render a spec JSON file into Markdown for review."
    )
    parser.add_argument("spec", help="Path to spec JSON file")
    parser.add_argument("--output", "-o", help="Write to file instead of stdout")
    parser.add_argument("--template", "-t", help="Custom Jinja2 template path")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    if not spec_path.exists():
        print(f"error: {spec_path} not found", file=sys.stderr)
        return 1

    try:
        spec = json.loads(spec_path.read_text())
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON: {exc}", file=sys.stderr)
        return 1

    warnings = validate_spec(spec)
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)

    template_path = Path(args.template) if args.template else None
    output = render(spec, template_path)

    if args.output:
        Path(args.output).write_text(output)
        print(f"wrote {args.output}", file=sys.stderr)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
