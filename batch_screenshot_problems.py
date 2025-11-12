"""Run `screenshot_problems.py` across every contest and year on disk."""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple


DEFAULT_TEST_TYPES: Sequence[str] = ("AMC8", "AMC10A", "AMC10B", "AMC12A", "AMC12B")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Iterate over every test/year pair in the local data folder and "
            "invoke screenshot_problems.py with the appropriate flags."
        )
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path("data"),
        help="Location of the scraped contest data (defaults to ./data).",
    )
    parser.add_argument(
        "--test-type",
        dest="test_types",
        action="append",
        help="Limit the run to specific test types (repeatable).",
    )
    parser.add_argument(
        "--year",
        dest="years",
        action="append",
        type=int,
        help="Limit the run to specific years (repeatable).",
    )
    parser.add_argument(
        "--browser",
        choices=("chromium", "firefox", "webkit"),
        default="chromium",
        help="Browser engine passed to screenshot_problems.py.",
    )
    parser.add_argument(
        "--browser-channel",
        default="chrome",
        help="Browser channel to use (defaults to Chrome for compatibility).",
    )
    parser.add_argument(
        "--browser-home",
        type=Path,
        default=Path("data/.playwright-home"),
        help="Where Playwright should store its profile for every invocation.",
    )
    parser.add_argument(
        "--browser-arg",
        dest="browser_args",
        action="append",
        default=None,
        help="Extra flag to pass to the browser process (repeatable).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print each command without executing it.",
    )
    parser.add_argument(
        "--stop-on-error",
        action="store_true",
        help="Abort immediately if any invocation fails.",
    )
    parser.add_argument(
        "--screenshots-script",
        type=Path,
        default=Path(__file__).with_name("screenshot_problems.py"),
        help="Path to screenshot_problems.py (override if relocated).",
    )
    parser.add_argument(
        "forward_args",
        nargs=argparse.REMAINDER,
        help=(
            "Extra arguments forwarded verbatim to screenshot_problems.py. Use "
            "the `--` delimiter before these flags."
        ),
    )
    return parser.parse_args()


def discover_combinations(
    data_root: Path, test_types: Iterable[str], allowed_years: Iterable[str] | None
) -> List[Tuple[str, str]]:
    combinations: List[Tuple[str, str]] = []
    allowed_year_set = set(allowed_years) if allowed_years else None

    for test_type in test_types:
        test_dir = data_root / test_type
        if not test_dir.is_dir():
            print(f"[skip] No directory for {test_type} in {data_root}")
            continue

        year_dirs = sorted(
            p for p in test_dir.iterdir() if p.is_dir() and p.name.isdigit()
        )

        for year_dir in year_dirs:
            year = year_dir.name
            if allowed_year_set and year not in allowed_year_set:
                continue
            combinations.append((test_type, year))

    return combinations


def build_command(
    script_path: Path,
    browser: str,
    browser_channel: str | None,
    browser_home: Path | None,
    browser_args: Sequence[str] | None,
    test_type: str,
    year: str,
    forward_args: Sequence[str] | None,
) -> List[str]:
    cmd: List[str] = [
        sys.executable,
        str(script_path),
        "--test-type",
        test_type,
        "--year",
        year,
        "--browser",
        browser,
    ]
    if browser_channel:
        cmd.extend(["--browser-channel", browser_channel])
    if browser_home:
        cmd.extend(["--browser-home", str(browser_home)])
    if browser_args:
        for arg in browser_args:
            cmd.extend(["--browser-arg", arg])
    if forward_args:
        cmd.extend(forward_args)
    return cmd


def main() -> None:
    args = parse_args()
    script_path = args.screenshots_script
    if not script_path.is_file():
        raise FileNotFoundError(f"Cannot find screenshot script: {script_path}")

    tests = args.test_types or DEFAULT_TEST_TYPES
    years = [str(year) for year in args.years] if args.years else None
    combos = discover_combinations(args.data_root, tests, years)
    if not combos:
        print("No matching test/year combinations found.")
        return

    total = len(combos)
    print(f"Discovered {total} test/year combinations.")

    for index, (test_type, year) in enumerate(combos, start=1):
        cmd = build_command(
            script_path,
            args.browser,
            args.browser_channel,
            args.browser_home,
            args.browser_args,
            test_type,
            year,
            args.forward_args,
        )
        display_cmd = " ".join(shlex.quote(part) for part in cmd)
        print(f"[{index}/{total}] {display_cmd}")
        if args.dry_run:
            continue

        result = subprocess.run(cmd, check=False)  # noqa: S603,S607
        if result.returncode != 0:
            print(
                f"Command failed with exit code {result.returncode}."
                f" (test={test_type}, year={year})"
            )
            if args.stop_on_error:
                sys.exit(result.returncode)


if __name__ == "__main__":
    main()
