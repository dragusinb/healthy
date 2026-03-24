"""
Clean demo video recorder. No CSS hacks — proper vault handling.

Usage:
    python record_demo.py --email user@example.com --password pass
    python record_demo.py --email user@example.com --password pass --headed
"""

import argparse
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = "https://analize.online"

LABELS = {
    "home": "Pagina principală",
    "login": "Autentificare",
    "dashboard": "Dashboard — Vedere de ansamblu",
    "documents": "Documente — Analize importate",
    "biomarkers": "Biomarkeri — Toate rezultatele",
    "evolution": "Evoluție — Grafice istorice",
    "health": "Doctor AI — Rapoarte de sănătate",
    "lifestyle": "Stil de viață — Recomandări",
    "billing": "Abonament — Planuri",
    "settings": "Setări — Securitate",
    "logout": "Deconectare",
}


def overlay(page, text):
    page.evaluate("""(t) => {
        let el = document.getElementById('demo-ol');
        if (!el) {
            el = document.createElement('div');
            el.id = 'demo-ol';
            Object.assign(el.style, {
                position:'fixed', top:'0', left:'0', width:'100%', zIndex:'999999',
                background:'rgba(15,23,42,0.88)', color:'#fff', fontSize:'20px',
                fontWeight:'600', fontFamily:'system-ui,sans-serif', textAlign:'center',
                padding:'14px 20px', letterSpacing:'0.5px', backdropFilter:'blur(6px)',
                borderBottom:'2px solid rgba(99,102,241,0.6)',
                boxShadow:'0 4px 24px rgba(0,0,0,0.3)'
            });
            document.body.appendChild(el);
        }
        el.textContent = t;
    }""", text)


def unlock_vault(page, password):
    """Unlock vault if the modal is showing. Returns True if unlocked."""
    try:
        modal = page.locator('.fixed.inset-0.z-50 input[type="password"]').first
        if modal.is_visible(timeout=2000):
            modal.fill(password)
            page.wait_for_timeout(300)
            page.locator('.fixed.inset-0.z-50 button:has-text("Deblocare"), .fixed.inset-0.z-50 button:has-text("Unlock")').first.click()
            page.wait_for_timeout(2500)
            return True
    except Exception:
        pass
    return False


def navigate(page, path, password):
    """Navigate to a page and handle vault unlock."""
    page.evaluate("window.scrollTo(0,0)")
    page.wait_for_timeout(200)

    # Use JS click on the sidebar link (bypasses modal overlay)
    clicked = page.evaluate(f"""() => {{
        const link = document.querySelector('a[href="{path}"]');
        if (link) {{ link.click(); return true; }}
        return false;
    }}""")

    if not clicked:
        # Fallback: direct navigation
        page.goto(f"{BASE_URL}{path}", wait_until="networkidle", timeout=20000)

    page.wait_for_timeout(2500)
    unlock_vault(page, password)
    page.wait_for_timeout(500)
    dismiss_cookies(page)


def dismiss_cookies(page):
    page.evaluate("""() => {
        localStorage.setItem('cookie_consent', 'true');
        localStorage.setItem('cookie_preferences', JSON.stringify({essential:true}));
        // Also remove cookie banner if visible
        document.querySelectorAll('.fixed.bottom-0, .fixed.top-0').forEach(el => {
            if (el.textContent.includes('cookie') || el.textContent.includes('Cookie'))
                el.remove();
        });
    }""")


def slow_scroll(page, steps=3, delay=600):
    for _ in range(steps):
        page.evaluate(f"window.scrollBy({{top:{page.viewport_size['height']//3},behavior:'smooth'}})")
        page.wait_for_timeout(delay)


def run(email, password, headed):
    out_dir = Path(__file__).parent / "demo-recordings"
    out_dir.mkdir(exist_ok=True)
    final = Path(__file__).parent / "demo-video.webm"

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=not headed,
            args=["--disable-blink-features=AutomationControlled"],
        )
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=str(out_dir),
            record_video_size={"width": 1280, "height": 720},
            locale="ro",
            color_scheme="light",
        )
        page = ctx.new_page()

        try:
            # 1. Landing
            print("[1/10] Landing page...")
            page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
            dismiss_cookies(page)
            page.reload(wait_until="networkidle")
            dismiss_cookies(page)
            overlay(page, LABELS["home"])
            page.wait_for_timeout(3000)
            slow_scroll(page, 2, 700)
            page.wait_for_timeout(1000)

            # 2. Login
            print("[2/10] Login...")
            page.goto(f"{BASE_URL}/login", wait_until="networkidle", timeout=20000)
            dismiss_cookies(page)
            overlay(page, LABELS["login"])
            page.wait_for_timeout(1000)
            page.locator("input[type=email], input[placeholder*=email]").first.fill(email)
            page.wait_for_timeout(400)
            page.locator("input[type=password]").first.fill(password)
            page.wait_for_timeout(500)
            page.locator("button[type=submit]").first.click()
            page.wait_for_timeout(4000)

            # Vault unlock after login
            if unlock_vault(page, password):
                print("   Vault unlocked")
            page.wait_for_timeout(2000)
            dismiss_cookies(page)

            # 3. Dashboard
            print("[3/10] Dashboard...")
            unlock_vault(page, password)
            dismiss_cookies(page)
            overlay(page, LABELS["dashboard"])
            page.wait_for_timeout(3000)
            slow_scroll(page, 2, 600)
            page.wait_for_timeout(1000)

            # 4. Documents (sidebar click)
            print("[4/10] Documents...")
            navigate(page, "/documents", password)
            dismiss_cookies(page)
            overlay(page, LABELS["documents"])
            page.wait_for_timeout(2000)
            slow_scroll(page, 2, 600)
            page.wait_for_timeout(1000)

            # 5. Biomarkers
            print("[5/10] Biomarkers...")
            navigate(page, "/biomarkers", password)
            dismiss_cookies(page)
            overlay(page, LABELS["biomarkers"])
            page.wait_for_timeout(2000)
            slow_scroll(page, 3, 600)
            page.wait_for_timeout(1000)

            # 6. Evolution (click a biomarker link)
            print("[6/10] Evolution charts...")
            evo = page.locator('a[href*="/evolution/"]').first
            try:
                if evo.is_visible(timeout=2000):
                    evo.click()
                    page.wait_for_timeout(3000)
                    unlock_vault(page, password)
            except Exception:
                pass
            dismiss_cookies(page)
            overlay(page, LABELS["evolution"])
            page.wait_for_timeout(2000)
            slow_scroll(page, 2, 600)
            page.wait_for_timeout(1000)

            # 7. Health Reports (sidebar)
            print("[7/10] Health Reports...")
            navigate(page, "/health", password)
            dismiss_cookies(page)
            overlay(page, LABELS["health"])
            page.wait_for_timeout(2000)
            slow_scroll(page, 2, 600)
            page.wait_for_timeout(1000)

            # 8. Lifestyle
            print("[8/10] Lifestyle...")
            navigate(page, "/lifestyle", password)
            dismiss_cookies(page)
            overlay(page, LABELS["lifestyle"])
            page.wait_for_timeout(2000)
            slow_scroll(page, 2, 600)
            page.wait_for_timeout(1000)

            # 9. Billing
            print("[9/10] Billing...")
            navigate(page, "/billing", password)
            dismiss_cookies(page)
            overlay(page, LABELS["billing"])
            page.wait_for_timeout(2000)

            # 10. Settings
            print("[10/10] Settings...")
            navigate(page, "/settings", password)
            dismiss_cookies(page)
            overlay(page, LABELS["settings"])
            page.wait_for_timeout(2000)
            slow_scroll(page, 2, 500)
            page.wait_for_timeout(1000)

            # Logout
            print("Logging out...")
            overlay(page, LABELS["logout"])
            page.wait_for_timeout(2000)
            try:
                page.locator('button:has-text("Deconectare"), button:has-text("Logout")').first.click()
                page.wait_for_timeout(2000)
            except Exception:
                pass

        except Exception as e:
            print(f"\n[ERROR] {e}")
            raise
        finally:
            page.close()
            ctx.close()
            browser.close()

    recordings = sorted(out_dir.glob("*.webm"), key=lambda f: f.stat().st_mtime)
    if recordings:
        shutil.move(str(recordings[-1]), str(final))
        print(f"\n{'='*60}\nDemo video saved: {final}\n{'='*60}")
    else:
        print("\n[WARNING] No video file found.")
    shutil.rmtree(out_dir, ignore_errors=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--headed", action="store_true")
    args = parser.parse_args()
    run(args.email, args.password, args.headed)
