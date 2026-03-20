"""
Demo video recorder for analize.online platform.

Usage:
    python record_demo.py --email user@example.com --password mysecret
    python record_demo.py --email user@example.com --password mysecret --headed
    python record_demo.py --email user@example.com --password mysecret --lang en

Requires: pip install playwright && playwright install chromium
"""

import argparse
import shutil
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = "https://analize.online"

# Romanian overlay labels for each demo step
OVERLAYS = {
    "home": "Pagina principala — Prezentare platforma",
    "login": "Autentificare — Conectare securizata",
    "dashboard": "Dashboard — Vedere de ansamblu",
    "documents": "Documente — Analize importate automat",
    "biomarkers": "Biomarkeri — Toate rezultatele tale",
    "evolution": "Evolutie — Grafice istorice biomarkeri",
    "health": "Doctor AI — Rapoarte de sanatate",
    "lifestyle": "Stil de viata — Recomandari personalizate",
    "billing": "Abonament — Planuri si facturare",
    "settings": "Setari — Securitate si criptare date",
    "logout": "Deconectare — Sesiune incheiata",
}

OVERLAYS_EN = {
    "home": "Landing Page — Platform Overview",
    "login": "Authentication — Secure Login",
    "dashboard": "Dashboard — Health Overview",
    "documents": "Documents — Auto-imported Lab Results",
    "biomarkers": "Biomarkers — All Your Results",
    "evolution": "Evolution — Historical Biomarker Charts",
    "health": "Doctor AI — Health Reports",
    "lifestyle": "Lifestyle — Personalized Recommendations",
    "billing": "Billing — Plans & Invoicing",
    "settings": "Settings — Security & Data Encryption",
    "logout": "Logout — Session Ended",
}


def inject_overlay(page, text: str):
    """Inject a semi-transparent banner overlay at the top of the page."""
    page.evaluate(
        """(text) => {
        // Remove previous overlay if any
        const old = document.getElementById('demo-overlay');
        if (old) old.remove();

        const div = document.createElement('div');
        div.id = 'demo-overlay';
        div.textContent = text;
        Object.assign(div.style, {
            position: 'fixed',
            top: '0',
            left: '0',
            width: '100%',
            zIndex: '999999',
            background: 'rgba(15, 23, 42, 0.85)',
            color: '#fff',
            fontSize: '20px',
            fontWeight: '600',
            fontFamily: 'system-ui, -apple-system, sans-serif',
            textAlign: 'center',
            padding: '14px 20px',
            letterSpacing: '0.5px',
            backdropFilter: 'blur(6px)',
            borderBottom: '2px solid rgba(99, 102, 241, 0.6)',
            boxShadow: '0 4px 24px rgba(0,0,0,0.3)',
        });
        document.body.appendChild(div);
    }""",
        text,
    )


def remove_overlay(page):
    """Remove the overlay banner."""
    page.evaluate(
        """() => {
        const el = document.getElementById('demo-overlay');
        if (el) el.remove();
    }"""
    )


def slow_scroll(page, steps=5, delay_ms=600):
    """Scroll down the page slowly in increments."""
    for i in range(steps):
        page.evaluate(
            f"window.scrollBy({{ top: {page.viewport_size['height'] // 3}, behavior: 'smooth' }})"
        )
        page.wait_for_timeout(delay_ms)


def dismiss_vault_modal(page, password: str):
    """Dismiss the vault unlock modal if it appears."""
    try:
        # Look for vault modal with password input
        modal_pw = page.locator('div:has-text("Sesiune Expir") input[type="password"], div:has-text("Vault") input[type="password"]').first
        if modal_pw.is_visible(timeout=2000):
            modal_pw.fill(password)
            page.wait_for_timeout(300)
            # Click "Deblocare Seif" / unlock button
            page.locator('button:has-text("Deblocare"), button:has-text("Unlock")').first.click()
            page.wait_for_timeout(2000)
    except Exception:
        pass


def wait_and_pause(page, seconds: float, password: str = None):
    """Wait for network idle, dismiss vault modal if needed, then pause."""
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass
    if password:
        dismiss_vault_modal(page, password)
    page.wait_for_timeout(int(seconds * 1000))


def run_demo(email: str, password: str, headed: bool, lang: str):
    overlays = OVERLAYS if lang == "ro" else OVERLAYS_EN

    output_dir = Path(__file__).parent / "demo-recordings"
    output_dir.mkdir(exist_ok=True)
    final_video = Path(__file__).parent / "demo-video.webm"

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=not headed,
            args=["--disable-blink-features=AutomationControlled"],
        )

        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=str(output_dir),
            record_video_size={"width": 1280, "height": 720},
            locale=lang,
            color_scheme="light",
        )

        page = context.new_page()

        try:
            # ── 1. Landing page ──────────────────────────────────
            print("[1/10] Landing page...")
            page.goto(BASE_URL, wait_until="networkidle", timeout=30000)

            # Dismiss cookie banner by setting consent in localStorage
            page.evaluate("""() => {
                localStorage.setItem('cookie_consent', 'true');
                localStorage.setItem('cookie_preferences', JSON.stringify({essential: true, analytics: false, marketing: false}));
            }""")
            page.reload(wait_until="networkidle")

            inject_overlay(page, overlays["home"])
            wait_and_pause(page, 4, password)
            slow_scroll(page, steps=3, delay_ms=800)
            page.wait_for_timeout(1000)

            # ── 2. Login ─────────────────────────────────────────
            print("[2/10] Login...")
            page.goto(f"{BASE_URL}/login", wait_until="networkidle", timeout=20000)
            inject_overlay(page, overlays["login"])
            page.wait_for_timeout(1500)

            # Fill credentials with realistic typing speed
            email_input = page.locator(
                "input[type=email], input[name=email], #login-email, "
                "input[placeholder*=email], input[placeholder*=Email]"
            ).first
            email_input.fill(email)
            page.wait_for_timeout(400)
            pw_input = page.locator("input[type=password]").first
            pw_input.fill(password)
            page.wait_for_timeout(600)

            # Submit login form
            page.locator("button[type=submit]").first.click()
            page.wait_for_timeout(3000)

            # Wait for navigation to dashboard (redirect after login)
            try:
                page.wait_for_url("**/", timeout=15000)
            except Exception:
                # May already be on dashboard or vault unlock needed
                pass

            # Handle vault unlock modal if it appears
            try:
                vault_input = page.locator('input[type="password"]').first
                if vault_input.is_visible(timeout=3000):
                    vault_input.fill(password)
                    page.click('button[type="submit"]')
                    page.wait_for_timeout(2000)
            except Exception:
                pass

            # ── 3. Dashboard ─────────────────────────────────────
            print("[3/10] Dashboard...")
            page.goto(f"{BASE_URL}/", wait_until="networkidle", timeout=20000)
            inject_overlay(page, overlays["dashboard"])
            wait_and_pause(page, 5, password)
            slow_scroll(page, steps=3, delay_ms=700)
            page.wait_for_timeout(1000)

            # ── 4. Documents ─────────────────────────────────────
            print("[4/10] Documents...")
            page.goto(f"{BASE_URL}/documents", wait_until="networkidle", timeout=20000)
            inject_overlay(page, overlays["documents"])
            wait_and_pause(page, 4, password)
            slow_scroll(page, steps=2, delay_ms=700)
            page.wait_for_timeout(1000)

            # ── 5. Biomarkers ────────────────────────────────────
            print("[5/10] Biomarkers...")
            page.goto(
                f"{BASE_URL}/biomarkers", wait_until="networkidle", timeout=20000
            )
            inject_overlay(page, overlays["biomarkers"])
            wait_and_pause(page, 5, password)
            slow_scroll(page, steps=4, delay_ms=700)
            page.wait_for_timeout(1000)

            # ── 6. Evolution (pick first biomarker link if available) ──
            print("[6/10] Evolution charts...")
            # Try to find and click a biomarker evolution link
            evolution_link = page.locator('a[href*="/evolution/"]').first
            try:
                if evolution_link.is_visible(timeout=3000):
                    evolution_name = (
                        evolution_link.get_attribute("href").split("/evolution/")[1]
                    )
                    page.goto(
                        f"{BASE_URL}/evolution/{evolution_name}",
                        wait_until="networkidle",
                        timeout=20000,
                    )
                else:
                    # Fallback: go to a common biomarker
                    page.goto(
                        f"{BASE_URL}/evolution/Hemoglobina",
                        wait_until="networkidle",
                        timeout=20000,
                    )
            except Exception:
                page.goto(
                    f"{BASE_URL}/evolution/Hemoglobina",
                    wait_until="networkidle",
                    timeout=20000,
                )

            inject_overlay(page, overlays["evolution"])
            wait_and_pause(page, 5, password)
            slow_scroll(page, steps=2, delay_ms=700)
            page.wait_for_timeout(1000)

            # ── 7. Health Reports ────────────────────────────────
            print("[7/10] Health Reports (Doctor AI)...")
            page.goto(f"{BASE_URL}/health", wait_until="networkidle", timeout=20000)
            inject_overlay(page, overlays["health"])
            wait_and_pause(page, 5, password)
            slow_scroll(page, steps=3, delay_ms=700)
            page.wait_for_timeout(1000)

            # ── 8. Lifestyle ─────────────────────────────────────
            print("[8/10] Lifestyle...")
            page.goto(
                f"{BASE_URL}/lifestyle", wait_until="networkidle", timeout=20000
            )
            inject_overlay(page, overlays["lifestyle"])
            wait_and_pause(page, 4, password)
            slow_scroll(page, steps=2, delay_ms=700)
            page.wait_for_timeout(1000)

            # ── 9. Billing ───────────────────────────────────────
            print("[9/10] Billing...")
            page.goto(f"{BASE_URL}/billing", wait_until="networkidle", timeout=20000)
            inject_overlay(page, overlays["billing"])
            wait_and_pause(page, 3, password)

            # ── 10. Settings ─────────────────────────────────────
            print("[10/10] Settings...")
            page.goto(f"{BASE_URL}/settings", wait_until="networkidle", timeout=20000)
            inject_overlay(page, overlays["settings"])
            wait_and_pause(page, 3, password)
            slow_scroll(page, steps=2, delay_ms=600)
            page.wait_for_timeout(1000)

            # ── Logout ───────────────────────────────────────────
            print("Logging out...")
            inject_overlay(page, overlays["logout"])
            page.wait_for_timeout(2000)

            # Click logout button in sidebar
            logout_btn = page.locator('button:has-text("Deconectare"), button:has-text("Logout")').first
            try:
                if logout_btn.is_visible(timeout=3000):
                    logout_btn.click()
                    page.wait_for_timeout(2000)
            except Exception:
                # Navigate to login as fallback
                page.goto(f"{BASE_URL}/login", wait_until="networkidle", timeout=10000)
                page.wait_for_timeout(2000)

        except Exception as e:
            print(f"\n[ERROR] Demo recording failed: {e}")
            raise
        finally:
            # Close context to finalize video
            page.close()
            context.close()
            browser.close()

    # Move the recorded video to the final destination
    recordings = sorted(output_dir.glob("*.webm"), key=lambda f: f.stat().st_mtime)
    if recordings:
        latest = recordings[-1]
        shutil.move(str(latest), str(final_video))
        print(f"\n{'='*60}")
        print(f"Demo video saved: {final_video}")
        print(f"{'='*60}")
    else:
        print("\n[WARNING] No video file found in recordings directory.")

    # Cleanup temp dir
    try:
        shutil.rmtree(output_dir, ignore_errors=True)
    except Exception:
        pass

    # Print conversion instructions
    print(
        f"""
To convert to MP4 (recommended for sharing):

    ffmpeg -i "{final_video}" -c:v libx264 -preset slow -crf 22 -c:a aac -b:a 128k "{final_video.with_suffix('.mp4')}"

To trim (e.g. first 2 minutes):

    ffmpeg -i "{final_video}" -t 120 -c copy "{final_video.parent / 'demo-trimmed.webm'}"

To add background music:

    ffmpeg -i "{final_video}" -i music.mp3 -c:v copy -c:a aac -shortest "{final_video.parent / 'demo-with-music.mp4'}"
"""
    )


def main():
    parser = argparse.ArgumentParser(
        description="Record a demo video of the analize.online platform"
    )
    parser.add_argument(
        "--email", required=True, help="Login email for the demo account"
    )
    parser.add_argument(
        "--password", required=True, help="Login password for the demo account"
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        default=False,
        help="Run with visible browser window",
    )
    parser.add_argument(
        "--lang",
        default="ro",
        choices=["ro", "en"],
        help="Browser locale / overlay language (default: ro)",
    )
    args = parser.parse_args()

    run_demo(
        email=args.email,
        password=args.password,
        headed=args.headed,
        lang=args.lang,
    )


if __name__ == "__main__":
    main()
