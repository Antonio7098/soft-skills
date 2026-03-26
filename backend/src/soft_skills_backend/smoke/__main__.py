"""Module entrypoint for smoke runs."""

from __future__ import annotations

import argparse
import io
import logging
from collections.abc import Sequence
from contextlib import redirect_stderr, redirect_stdout

from soft_skills_backend.smoke import build_default_runner


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entrypoint."""

    parser = argparse.ArgumentParser(description="Run backend smoke suites.")
    parser.add_argument("smoke", nargs="?", help="Registered smoke name.")
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_smokes",
        help="List registered smoke suites.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    runner = build_default_runner()
    if args.list_smokes:
        for smoke in runner.definitions():
            print(f"{smoke.name}: {smoke.description}")
        return

    buffer = io.StringIO()
    previous_disable = logging.root.manager.disable
    try:
        logging.disable(logging.CRITICAL)
        with redirect_stdout(buffer), redirect_stderr(buffer):
            result = runner.run(args.smoke)
    finally:
        logging.disable(previous_disable)
    print(result.model_dump_json())


if __name__ == "__main__":
    main()
