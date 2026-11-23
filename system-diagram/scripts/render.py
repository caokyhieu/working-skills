#!/usr/bin/env python3
"""Render an .excalidraw file to PNG (and optionally SVG) with Excalidraw's own exporter.

Uses Playwright + headless Chromium and loads a pinned @excalidraw/excalidraw from esm.sh,
so the picture is exactly what excalidraw.com shows (hachure fills, fonts, arrowheads).

Usage (no install step; uv fetches playwright on first run):
    uv run --with playwright python render.py DIAGRAM.excalidraw [-o OUT.png] [--svg] [--scale 2] [--dark]

First time on a machine without Chromium:
    uv run --with playwright playwright install chromium
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

EXCALIDRAW_VERSION = "0.18.0"
HERE = Path(__file__).resolve().parent


def chromium_candidates() -> list[str]:
    """Chromium binaries already on this machine (any Playwright cache version, system installs)."""
    import glob
    import os
    import shutil
    out = []
    env = os.environ.get("SYSDIAG_CHROMIUM")
    if env:
        out.append(env)
    cache = Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", Path.home() / ".cache" / "ms-playwright"))
    pats = ["chromium_headless_shell-*/chrome-*/chrome-headless-shell", "chromium_headless_shell-*/chrome-*/headless_shell",
            "chromium-*/chrome-linux*/chrome", "chromium-*/chrome-mac*/Chromium.app/Contents/MacOS/Chromium",
            "chromium-*/chrome-mac*/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing",
            "chromium-*/chrome-win*/chrome.exe"]
    for pat in pats:
        out += sorted(glob.glob(str(cache / pat)), reverse=True)
    for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable"):
        w = shutil.which(name)
        if w:
            out.append(w)
    return out


def launch(p):
    try:
        return p.chromium.launch(headless=True)
    except Exception as first:  # noqa: BLE001  bundled build missing -> try what is installed
        for exe in chromium_candidates():
            try:
                return p.chromium.launch(headless=True, executable_path=exe)
            except Exception:  # noqa: BLE001
                continue
        sys.exit(f"Chromium failed to start ({str(first).splitlines()[0]}).\n"
                 "Run: uv run --with playwright playwright install chromium   "
                 "(or set SYSDIAG_CHROMIUM=/path/to/chrome)")


def render(src: Path, out: Path, scale: float, svg_out: Path | None, dark: bool, timeout_s: int) -> dict:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("playwright missing. Run with: uv run --with playwright python render.py ...")
    data = json.loads(src.read_text(encoding="utf-8"))
    if data.get("type") != "excalidraw" or not data.get("elements"):
        sys.exit(f"{src}: not an excalidraw file or no elements")
    html = (HERE / "render_template.html").read_text().replace("__VERSION__", EXCALIDRAW_VERSION)
    src = src.resolve()
    page_file = src.with_name(f".{src.stem}.render.html")
    page_file.write_text(html)
    try:
        with sync_playwright() as p:
            browser = launch(p)
            page = browser.new_page(viewport={"width": 1600, "height": 1000}, device_scale_factor=scale)
            page.goto(page_file.as_uri())
            page.wait_for_function("window.__moduleReady === true", timeout=timeout_s * 1000)
            res = page.evaluate("([d, o]) => window.renderDiagram(d, o)", [data, {"dark": dark}])
            if not res or not res.get("success"):
                browser.close()
                sys.exit(f"render failed: {res and res.get('error')}")
            page.wait_for_timeout(400)  # let embedded fonts settle
            el = page.query_selector("#root svg")
            el.screenshot(path=str(out))
            if svg_out:
                svg_out.write_text(res["svg"], encoding="utf-8")
            browser.close()
            return res
    finally:
        page_file.unlink(missing_ok=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", type=Path)
    ap.add_argument("-o", "--output", type=Path)
    ap.add_argument("--svg", action="store_true", help="also write OUT.svg (fonts embedded)")
    ap.add_argument("--scale", type=float, default=2)
    ap.add_argument("--dark", action="store_true")
    ap.add_argument("--timeout", type=int, default=60)
    a = ap.parse_args()
    if not a.input.exists():
        sys.exit(f"not found: {a.input}")
    out = a.output or a.input.with_suffix(".png")
    svg = out.with_suffix(".svg") if a.svg else None
    res = render(a.input, out, a.scale, svg, a.dark, a.timeout)
    print(f"{out}  ({res.get('width')}x{res.get('height')} css px, scale {a.scale})" + (f"; {svg}" if svg else ""))


if __name__ == "__main__":
    main()
