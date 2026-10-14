from __future__ import annotations

import argparse
import json
import os
from collections.abc import Sequence
from pathlib import Path

from learning_plane.demo import DemoEnvironment


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="learning-plane")
    commands = root.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("demo", help="run deterministic offline demonstrations")
    demo.add_argument("lab", choices=["lab1", "lab2", "lab3", "lab4", "all"])
    demo.add_argument(
        "--evidence-dir",
        default=os.getenv("LEARNING_PLANE_EVIDENCE", "evidence"),
        help="artifact output directory",
    )
    return root


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    environment = DemoEnvironment(Path(args.evidence_dir))
    try:
        result = getattr(environment, args.lab)()
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, indent=2))
        return 1
    summary = {
        "status": "completed",
        "lab": args.lab,
        "evidence_dir": str(Path(args.evidence_dir).resolve()),
        "keys": list(result),
    }
    print(json.dumps(summary, indent=2))
    return 0
