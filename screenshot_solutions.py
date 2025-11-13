"""Generate screenshots for AMC solution HTML files.

This script loads the locally rendered solution HTML in a headless browser
and crops screenshots for each solution provided. If a problem has multiple
solutions, each solution is captured as a separate screenshot. Screenshots
are saved alongside each test/year in
`data/<test_type>/<year>/screenshot/problem_<n>_solution_<m>.png`.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Set

from playwright.async_api import Browser, BrowserType, Page, async_playwright


LOGGER = logging.getLogger("solution_screenshots")


@dataclass
class SolutionScreenshotTarget:
    """A single solution within a solution HTML file that needs a screenshot."""

    html_path: Path
    image_path: Path
    test_type: str
    year: str
    problem_number: int
    solution_number: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Render AMC solution HTML files in a headless browser and save "
            "screenshots of each solution separately."
        )
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path("data"),
        help="Root directory that contains the scraped test data.",
    )
    parser.add_argument(
        "--test-type",
        help="Restrict to a single test type (e.g., AMC10A, AMC12B).",
    )
    parser.add_argument(
        "--year",
        help="Restrict to a single contest year (e.g., 2024).",
    )
    parser.add_argument(
        "--problem",
        dest="problems",
        action="append",
        type=int,
        help="Problem number to capture; may be provided multiple times.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of solution screenshots to create (useful for smoke tests).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Recreate screenshots even if the PNG already exists.",
    )
    parser.add_argument(
        "--padding",
        type=int,
        default=24,
        help="Padding (in CSS pixels) around the cropped region.",
    )
    parser.add_argument(
        "--wait-ms",
        type=int,
        default=2000,
        help="How long to wait for inline images to load before capturing (ms).",
    )
    parser.add_argument(
        "--viewport-width",
        type=int,
        default=1400,
        help="Viewport width used when rendering each solution.",
    )
    parser.add_argument(
        "--viewport-height",
        type=int,
        default=4200,
        help="Viewport height used when rendering each solution.",
    )
    parser.add_argument(
        "--browser",
        choices=("chromium", "firefox", "webkit"),
        default="chromium",
        help="Which Playwright browser engine to use.",
    )
    parser.add_argument(
        "--browser-channel",
        help=(
            "Optional browser channel name (e.g., chrome, chrome-beta). "
            "Useful when the default bundled browsers are not permitted."
        ),
    )
    parser.add_argument(
        "--browser-arg",
        dest="browser_args",
        action="append",
        help="Additional command-line flag to pass to the browser (repeatable).",
    )
    parser.add_argument(
        "--browser-home",
        type=Path,
        help=(
            "Directory to use as $HOME for the browser profile. "
            "Defaults to <data-root>/.playwright-home."
        ),
    )
    parser.add_argument(
        "--device-scale-factor",
        type=float,
        default=2.0,
        help="Device scale factor passed to the browser for sharper images.",
    )
    parser.add_argument(
        "--show-browser",
        action="store_true",
        help="Run in headed mode for debugging instead of headless.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging.",
    )
    return parser.parse_args()


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s %(message)s")


def discover_targets(
    data_root: Path,
    test_type: Optional[str],
    year: Optional[str],
    problems: Optional[Set[int]],
    limit: Optional[int],
) -> List[SolutionScreenshotTarget]:
    if not data_root.is_dir():
        raise FileNotFoundError(f"Data directory not found: {data_root}")

    remaining = limit
    targets: List[SolutionScreenshotTarget] = []
    test_dirs: Iterable[Path]

    if test_type:
        test_dirs = [data_root / test_type]
    else:
        test_dirs = sorted(p for p in data_root.iterdir() if p.is_dir())

    for test_dir in test_dirs:
        if not test_dir.is_dir():
            LOGGER.debug("Skipping non-directory: %s", test_dir)
            continue
        resolved_test_type = test_dir.name
        year_dirs: Iterable[Path]
        if year:
            year_dirs = [test_dir / year]
        else:
            year_dirs = sorted(
                (p for p in test_dir.iterdir() if p.is_dir() and p.name.isdigit()),
                key=lambda path: path.name,
            )

        for year_dir in year_dirs:
            if not year_dir.is_dir():
                LOGGER.debug("Skipping missing year directory: %s", year_dir)
                continue
            html_dir = year_dir / "html"
            if not html_dir.is_dir():
                LOGGER.debug("No html directory in %s", year_dir)
                continue

            for html_file in sorted(html_dir.glob("solution_*.html")):
                match = re.match(r"solution_(\d+)\.html", html_file.name)
                if not match:
                    continue
                problem_number = int(match.group(1))
                if problems and problem_number not in problems:
                    continue
                
                # Read the HTML file to count how many solutions it contains
                try:
                    html_content = html_file.read_text(encoding="utf-8")
                    # Find all solution headers (h2 with id="Solution_X")
                    solution_matches = re.findall(r'<h2\s+id="Solution_(\d+)"', html_content)
                    solution_numbers = sorted([int(m) for m in solution_matches])
                    
                    if not solution_numbers:
                        LOGGER.warning("No solutions found in %s", html_file)
                        continue
                    
                    image_dir = year_dir / "screenshot"
                    for solution_num in solution_numbers:
                        image_path = image_dir / f"problem_{problem_number}_solution_{solution_num}.png"
                        targets.append(
                            SolutionScreenshotTarget(
                                html_path=html_file,
                                image_path=image_path,
                                test_type=resolved_test_type,
                                year=year_dir.name,
                                problem_number=problem_number,
                                solution_number=solution_num,
                            )
                        )
                        if remaining is not None:
                            remaining -= 1
                            if remaining <= 0:
                                return targets
                except Exception as exc:
                    LOGGER.error("Failed to process %s: %s", html_file, exc)
                    continue

    return targets


async def wait_for_images(page: Page, timeout_ms: int) -> None:
    if timeout_ms <= 0:
        return

    try:
        await page.wait_for_function(
            "Array.from(document.images).every((img) => img.complete)",
            timeout=timeout_ms,
        )
    except Exception:
        LOGGER.debug("Timed out waiting for inline images to finish loading")


async def capture_target(
    page: Page,
    target: SolutionScreenshotTarget,
    padding: int,
    wait_ms: int,
    overwrite: bool,
) -> bool:
    if target.image_path.exists() and not overwrite:
        LOGGER.info(
            "Skipping %s %s problem %s solution %s (already exists)",
            target.test_type,
            target.year,
            target.problem_number,
            target.solution_number,
        )
        return False

    target.image_path.parent.mkdir(parents=True, exist_ok=True)
    url = target.html_path.resolve().as_uri()
    LOGGER.debug("Loading %s", url)
    await page.goto(url)
    await page.wait_for_load_state("load")
    await wait_for_images(page, wait_ms)
    await page.wait_for_timeout(100)

    # Find the specific solution header and its content
    solution_id = f"Solution_{target.solution_number}"
    solution_header = await page.query_selector(f'h2#{solution_id}')
    
    if not solution_header:
        LOGGER.warning(
            "Solution %s not found in %s",
            solution_id,
            target.html_path,
        )
        return False

    # Get the solution header and its corresponding content div
    boxes = []
    header_box = await solution_header.bounding_box()
    if header_box:
        boxes.append(header_box)
    
    # Find the solution-content div that follows this header
    # Get all solution headers and content divs, then match by index
    all_solution_headers = await page.query_selector_all('h2[id^="Solution_"]')
    all_solution_contents = await page.query_selector_all('.solution-content')
    
    # Find the index of our target solution header
    solution_index = None
    for idx, header in enumerate(all_solution_headers):
        header_id = await header.get_attribute('id')
        if header_id == solution_id:
            solution_index = idx
            break
    
    # Match the solution content div at the same index
    if solution_index is not None and solution_index < len(all_solution_contents):
        content_element = all_solution_contents[solution_index]
        content_box = await content_element.bounding_box()
        if content_box:
            boxes.append(content_box)
    
    if not boxes:
        LOGGER.debug("Falling back to header bounding box for %s", target.html_path)
        if header_box:
            boxes = [header_box]
        else:
            raise RuntimeError(
                f"Could not determine capture region for {target.html_path} solution {target.solution_number}"
            )

    viewport = page.viewport_size
    if viewport is None:
        raise RuntimeError("Viewport size is not configured")

    clip = _combine_boxes(boxes, padding, viewport["width"], viewport["height"])
    LOGGER.info(
        "Saving screenshot: %s/%s problem %s solution %s -> %s",
        target.test_type,
        target.year,
        target.problem_number,
        target.solution_number,
        target.image_path,
    )
    await page.screenshot(path=str(target.image_path), clip=clip)
    return True


def _combine_boxes(boxes, padding: int, viewport_width: int, viewport_height: int):
    min_x = min(box["x"] for box in boxes)
    min_y = min(box["y"] for box in boxes)
    max_x = max(box["x"] + box["width"] for box in boxes)
    max_y = max(box["y"] + box["height"] for box in boxes)

    x = max(min_x - padding, 0)
    y = max(min_y - padding, 0)
    width = (max_x - min_x) + 2 * padding
    height = (max_y - min_y) + 2 * padding

    width = min(width, viewport_width - x)
    height = min(height, viewport_height - y)
    width = max(width, 1)
    height = max(height, 1)

    return {"x": x, "y": y, "width": width, "height": height}


async def run(args: argparse.Namespace) -> None:
    problems = set(args.problems) if args.problems else None
    targets = discover_targets(args.data_root, args.test_type, args.year, problems, args.limit)

    if not targets:
        LOGGER.warning("No solution HTML files matched the provided filters.")
        return

    LOGGER.info("Preparing to capture %s solution screenshot(s).", len(targets))

    async with async_playwright() as playwright:
        browser_type: BrowserType = getattr(playwright, args.browser)
        browser = await _launch_browser(browser_type, args)
        page = await browser.new_page(
            viewport={
                "width": args.viewport_width,
                "height": args.viewport_height,
                "device_scale_factor": args.device_scale_factor,
            }
        )

        successes = 0
        try:
            for target in targets:
                try:
                    created = await capture_target(
                        page,
                        target,
                        padding=args.padding,
                        wait_ms=args.wait_ms,
                        overwrite=args.overwrite,
                    )
                    if created:
                        successes += 1
                except Exception as exc:  # pylint: disable=broad-except
                    LOGGER.error("Failed to capture %s: %s", target.html_path, exc)
        finally:
            await browser.close()

    LOGGER.info("Finished writing %s screenshot(s).", successes)


def _prepare_browser_env(args: argparse.Namespace) -> dict:
    home_base: Path
    if args.browser_home:
        home_base = args.browser_home
    else:
        home_base = args.data_root / ".playwright-home"

    home_dir = home_base.expanduser().resolve()
    home_dir.mkdir(parents=True, exist_ok=True)
    LOGGER.debug("Browser HOME directory: %s", home_dir)

    env = os.environ.copy()
    env["HOME"] = str(home_dir)
    env["USERPROFILE"] = str(home_dir)
    if sys.platform.startswith("linux"):
        env.setdefault("XDG_CACHE_HOME", str(home_dir / ".cache"))
        env.setdefault("XDG_CONFIG_HOME", str(home_dir / ".config"))

    if args.browser == "chromium":
        crashpad_dir = home_dir / "Library" / "Application Support" / "Google" / "Chrome" / "Crashpad"
        crashpad_dir.mkdir(parents=True, exist_ok=True)

    return env


async def _launch_browser(browser_type: BrowserType, args: argparse.Namespace) -> Browser:
    launch_kwargs = {"headless": not args.show_browser}
    if args.browser_channel:
        launch_kwargs["channel"] = args.browser_channel
    browser_args = list(args.browser_args or [])
    if args.browser == "chromium" and "--disable-crashpad" not in browser_args:
        browser_args.append("--disable-crashpad")
    if browser_args:
        launch_kwargs["args"] = browser_args
    launch_kwargs["env"] = _prepare_browser_env(args)
    return await browser_type.launch(**launch_kwargs)


def main() -> None:
    args = parse_args()
    configure_logging(args.verbose)
    try:
        asyncio.run(run(args))
    except KeyboardInterrupt:  # pragma: no cover - convenience
        LOGGER.warning("Cancelled by user")


if __name__ == "__main__":
    main()

