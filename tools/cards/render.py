"""Render the profile cards (1200x750) to assets/cards/ with Playwright and Microsoft Edge.
The artifacts in src/ come from each project's own README tooling.

    python tools/cards/render.py
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
OUT = HERE.parent.parent / "assets" / "cards"
CARDS = ["tanksim", "deskpal", "sitright", "mixinsmith"]

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", args=["--disable-lcd-text"])
    page = browser.new_page(viewport={"width": 1200, "height": 750}, color_scheme="dark")
    for name in CARDS:
        page.goto((HERE / f"{name}.html").as_uri())
        page.evaluate("document.fonts.ready")
        page.wait_for_timeout(200)
        page.screenshot(path=str(OUT / f"{name}.png"))
        print(OUT / f"{name}.png")
    browser.close()
