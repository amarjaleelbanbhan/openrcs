"""OpenRCS command-line interface."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from . import rcp, rcs

NOT_IMPLEMENTED = (
    "Not implemented: OpenRCS cannot decode RCS point data. No public "
    "specification exists for the point-record layout, and decompiling "
    "Autodesk ReCap to recover it is prohibited by Autodesk's License and "
    "Services Agreement without specific legal authorization (see "
    "docs/format-findings.md and docs/limitations.md). To get E57/LAS/LAZ "
    "today, export directly from Autodesk ReCap."
)


def _print_json(data: dict[str, Any]) -> None:
    print(json.dumps(data, indent=2))


def cmd_inspect_scan(args: argparse.Namespace) -> int:
    try:
        result = rcs.inspect_scan(args.path)
    except FileNotFoundError:
        print(f"error: file not found: {args.path}", file=sys.stderr)
        return 1
    _print_json(result)
    return 0 if result["signature"]["valid"] else 1


def cmd_inspect_project(args: argparse.Namespace) -> int:
    try:
        result = rcp.inspect_project(args.path)
    except FileNotFoundError:
        print(f"error: file not found: {args.path}", file=sys.stderr)
        return 1
    _print_json(result)
    return 0 if result.get("is_zip_container") else 1


def cmd_validate(args: argparse.Namespace) -> int:
    is_rcs = args.path.lower().endswith(".rcs")
    is_rcp = args.path.lower().endswith(".rcp")
    if not is_rcs and not is_rcp:
        print("error: validate requires a .rcs or .rcp path", file=sys.stderr)
        return 1
    try:
        result = rcs.inspect_scan(args.path) if is_rcs else rcp.inspect_project(args.path)
    except FileNotFoundError:
        print(f"error: file not found: {args.path}", file=sys.stderr)
        return 1

    valid = result["signature"]["valid"] if is_rcs else result.get("is_zip_container", False)
    report = {
        "path": args.path,
        "kind": "rcs" if is_rcs else "rcp",
        "structurally_valid": valid,
        "fully_validated": False,
        "note": "Structural validity only (signature/container check). "
        "Internal structure is not fully understood, so this is never a "
        "complete validation — see docs/limitations.md.",
        "details": result,
    }
    _print_json(report)
    return 0 if valid else 1


def cmd_convert(args: argparse.Namespace) -> int:
    print(NOT_IMPLEMENTED, file=sys.stderr)
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="openrcs")
    sub = parser.add_subparsers(dest="command", required=True)

    p_scan = sub.add_parser("inspect-scan", help="Inspect an .rcs scan file")
    p_scan.add_argument("path")
    p_scan.set_defaults(func=cmd_inspect_scan)

    p_proj = sub.add_parser("inspect-project", help="Inspect an .rcp project file")
    p_proj.add_argument("path")
    p_proj.set_defaults(func=cmd_inspect_project)

    p_val = sub.add_parser("validate", help="Report structural validity of an .rcs/.rcp file")
    p_val.add_argument("path")
    p_val.set_defaults(func=cmd_validate)

    p_conv = sub.add_parser("convert", help="Convert an .rcs file (not implemented)")
    p_conv.add_argument("path")
    p_conv.add_argument("--format", choices=["e57", "las", "laz"], required=True)
    p_conv.add_argument("--output", required=True)
    p_conv.set_defaults(func=cmd_convert)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
