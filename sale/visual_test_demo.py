#!/usr/bin/env python3
"""
Visual Playwright test for demo accounts.
Takes screenshots of all main pages to verify they show real data.

Run locally:
  pip install playwright && playwright install chromium
  python sale/visual_test_demo.py
"""
import sys
import os
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Installing playwright...")
    os.system(f"{sys.executable} -m pip install playwright")
    os.system("playwright install chromium")
    from playwright.sync_api import sync_playwright

BASE_URL = "https://analize.online"
EMAIL = "elena.popescu@demo.analize.online"
PASSWORD = "DemoPass123!"
SCREENSHOT_DIR = Path(__file__).parent / "demo_screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True)


def take_screenshot(page, name, wait_ms=2000):
    """Take a full-page screenshot."""
    page.wait_for_timeout(wait_ms)
    path = SCREENSHOT_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=True)
    print(f"  Screenshot: {path}")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="ro-RO",
        )
        page = context.new_page()

        # 1. Login
        print("Step 1: Login...")
        page.goto(f"{BASE_URL}/login")
        page.wait_for_timeout(2000)
        page.fill('input[type="email"], input[name="email"]', EMAIL)
        page.fill('input[type="password"], input[name="password"]', PASSWORD)
        page.click('button[type="submit"]')
        page.wait_for_timeout(3000)
        take_screenshot(page, "01_after_login")

        # Check if we're logged in (should be on dashboard or home)
        current_url = page.url
        print(f"  Current URL after login: {current_url}")

        # 2. Dashboard
        print("Step 2: Dashboard...")
        page.goto(f"{BASE_URL}/dashboard")
        page.wait_for_timeout(3000)
        take_screenshot(page, "02_dashboard")

        # Check for vault errors or empty states
        page_content = page.text_content("body")
        if "vault" in page_content.lower() and "error" in page_content.lower():
            print("  WARNING: Vault error detected on dashboard!")
        if "Nu aveti" in page_content or "No data" in page_content:
            print("  WARNING: Empty state detected on dashboard!")

        # 3. Documents
        print("Step 3: Documents...")
        page.goto(f"{BASE_URL}/documents")
        page.wait_for_timeout(3000)
        take_screenshot(page, "03_documents")

        # 4. Biomarkers
        print("Step 4: Biomarkers...")
        page.goto(f"{BASE_URL}/biomarkers")
        page.wait_for_timeout(3000)
        take_screenshot(page, "04_biomarkers")

        # 5. Health Reports
        print("Step 5: Health Reports...")
        page.goto(f"{BASE_URL}/health")
        page.wait_for_timeout(3000)
        take_screenshot(page, "05_health_reports")

        # 6. Lifestyle (nutrition/exercise)
        print("Step 6: Lifestyle...")
        page.goto(f"{BASE_URL}/lifestyle")
        page.wait_for_timeout(3000)
        take_screenshot(page, "06_lifestyle")

        # 7. Profile
        print("Step 7: Profile...")
        page.goto(f"{BASE_URL}/profile")
        page.wait_for_timeout(3000)
        take_screenshot(page, "07_profile")

        # 8. Medications
        print("Step 8: Medications...")
        page.goto(f"{BASE_URL}/medications")
        page.wait_for_timeout(3000)
        take_screenshot(page, "08_medications")

        # 9. Check for any console errors
        print("\nStep 9: Checking for issues...")
        errors_found = []
        page.goto(f"{BASE_URL}/dashboard")
        page.wait_for_timeout(2000)
        body_text = page.text_content("body") or ""

        # Check various warning signs
        for warning in ["vault_locked", "vault error", "Encryption error", "decrypt", "Nu aveti documente"]:
            if warning.lower() in body_text.lower():
                errors_found.append(f"Found '{warning}' on dashboard")

        if errors_found:
            print("  ISSUES FOUND:")
            for e in errors_found:
                print(f"    - {e}")
        else:
            print("  No issues found!")

        browser.close()

    print(f"\nAll screenshots saved to: {SCREENSHOT_DIR}")
    print("Visual test complete!")


if __name__ == "__main__":
    main()
