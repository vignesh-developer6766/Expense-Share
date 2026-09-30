import time
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
SCREENSHOT_DIR = BASE_DIR / "docs" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

def capture_login():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # Desktop 1440px
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page.goto("http://127.0.0.1:5000/auth/login")
        time.sleep(1)
        page.screenshot(path=str(SCREENSHOT_DIR / "login-desktop.png"))
        context.close()

        # Mobile 390px
        context = browser.new_context(viewport={"width": 390, "height": 844})
        page = context.new_page()
        page.goto("http://127.0.0.1:5000/auth/login")
        time.sleep(1)
        page.screenshot(path=str(SCREENSHOT_DIR / "login-mobile.png"))
        context.close()

        browser.close()
        print("Login screenshots captured successfully!")

if __name__ == "__main__":
    capture_login()
