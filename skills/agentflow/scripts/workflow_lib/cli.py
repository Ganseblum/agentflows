"""Command-line adapter for portable workflow evidence operations."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, NoReturn

from .execution import run_plan
from .managed import apply_managed, preview_managed
from .snapshots import WorkflowError, envelope, inventory, seal_plan, verify_plan


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise WorkflowError("invalid-arguments", message)


def parser() -> argparse.ArgumentParser:
    result = ArgumentParser(
        description="Bind plans and current native test evidence without a model runtime."
    )
    commands = result.add_subparsers(
        dest="operation", required=True, parser_class=ArgumentParser
    )
    seal = commands.add_parser(
        "seal", help="Bind a request to its Markdown plan and source baseline"
    )
    seal.add_argument("--root", required=True)
    seal.add_argument("--input", required=True)
    seal.add_argument("--output", required=True)
    for name in ("verify", "run"):
        command = commands.add_parser(name)
        command.add_argument("--root", required=True)
        command.add_argument("--sealed", required=True)
        command.add_argument("--fingerprint", required=True)
        if name == "run":
            command.add_argument("--output", required=True)
            command.add_argument("--phase", choices=("green", "red"), default="green")
    census = commands.add_parser(
        "inventory", help="Check a complete declared backfill census"
    )
    census.add_argument("--root", required=True)
    census.add_argument("--input", required=True)
    preview = commands.add_parser("managed-preview")
    preview.add_argument("--target", required=True)
    preview.add_argument("--content", required=True)
    preview.add_argument("--output", required=True)
    preview.add_argument("--begin-marker")
    preview.add_argument("--end-marker")
    preview.add_argument("--new-begin-marker")
    apply = commands.add_parser("managed-apply")
    apply.add_argument("--preview", required=True)
    apply.add_argument("--fingerprint", required=True)
    return result


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    operation = (
        arguments[0] if arguments and not arguments[0].startswith("-") else "workflow"
    )
    try:
        args = parser().parse_args(arguments)
        operation = args.operation
        result: dict[str, Any]
        if operation == "seal":
            result = seal_plan(args.root, args.input, args.output)
        elif operation == "verify":
            result = verify_plan(args.root, args.sealed, args.fingerprint)
        elif operation == "run":
            result = run_plan(
                args.root, args.sealed, args.fingerprint, args.output, args.phase
            )
        elif operation == "inventory":
            result = inventory(args.root, args.input)
        elif operation == "managed-preview":
            result = preview_managed(
                args.target,
                args.content,
                args.output,
                args.begin_marker,
                args.end_marker,
                args.new_begin_marker,
            )
        else:
            result = apply_managed(args.preview, args.fingerprint)
    except WorkflowError as exc:
        result = envelope(
            operation,
            {"message": str(exc)},
            exc.code,
            exc.kind,
            "resolve_input_or_refresh_preview"
            if exc.code in {2, 3}
            else "inspect_failure_evidence",
        )
    except (OSError, ValueError, TypeError, KeyError) as exc:
        # Malformed input must fail closed and remain machine readable; it must not be
        # mistaken for an empty successful result or a Python traceback-only response.
        result = envelope(
            operation, {"message": str(exc)}, 2, "invalid-input", "correct_input"
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return int(result["exit_code"])
