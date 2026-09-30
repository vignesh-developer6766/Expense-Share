import os
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SCREENSHOT_DIR = BASE_DIR / "docs" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

from playwright.sync_api import sync_playwright

def capture():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # Desktop 1440px
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page.goto("http://127.0.0.1:5000/auth/login")
        page.fill("input[name='email']", "vignesh@example.com")
        page.fill("input[name='password']", "Password123")
        page.click("button[type='submit']")
        time.sleep(2)
        page.screenshot(path=str(SCREENSHOT_DIR / "dashboard-desktop.png"))

        # Users Management Page
        page.goto("http://127.0.0.1:5000/users")
        time.sleep(1)
        page.screenshot(path=str(SCREENSHOT_DIR / "users-desktop.png"))
        context.close()

        # Tablet 768px
        context = browser.new_context(viewport={"width": 768, "height": 1024})
        page = context.new_page()
        page.goto("http://127.0.0.1:5000/auth/login")
        page.fill("input[name='email']", "vignesh@example.com")
        page.fill("input[name='password']", "Password123")
        page.click("button[type='submit']")
        time.sleep(2)
        page.screenshot(path=str(SCREENSHOT_DIR / "dashboard-tablet.png"))
        context.close()

        # Mobile 390px
        context = browser.new_context(viewport={"width": 390, "height": 844})
        page = context.new_page()
        page.goto("http://127.0.0.1:5000/auth/login")
        page.fill("input[name='email']", "vignesh@example.com")
        page.fill("input[name='password']", "Password123")
        page.click("button[type='submit']")
        time.sleep(2)
        page.screenshot(path=str(SCREENSHOT_DIR / "dashboard-mobile.png"))
        context.close()

        browser.close()
        print("Screenshots captured successfully!")

if __name__ == "__main__":
    capture()

