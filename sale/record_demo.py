"""
Demo video recorder for analize.online platform.

Usage:
    python record_demo.py --email user@example.com --password mysecret
    python record_demo.py --email user@example.com --password mysecret --headed

Requires: pip install playwright && playwright install chromium
"""

import argparse
import shutil
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = "https://analize.online"

OVERLAYS = {
    "home": "Pagina principală — Prezentare platformă",
    "login": "Autentificare — Conectare securizată",
    "dashboard": "Dashboard — Vedere de ansamblu",
    "documents": "Documente — Analize importate automat",
    "biomarkers": "Biomarkeri — Toate rezultatele tale",
    "evolution": "Evoluție — Grafice istorice biomarkeri",
    "health": "Doctor AI — Rapoarte de sănătate",
    "lifestyle": "Stil de viață — Recomandări personalizate",
    "billing": "Abonament — Planuri și facturare",
    "settings": "Setări — Securitate și criptare date",
    "logout": "Deconectare — Sesiune încheiată",
}


def inject_overlay(page, text):
    page.evaluate(
        """(text) => {
        const old = document.getElementById('demo-overlay');
        if (old) old.remove();
        const div = document.createElement('div');
        div.id = 'demo-overlay';
        div.textContent = text;
        Object.assign(div.style, {
            position: 'fixed', top: '0', left: '0', width: '100%',
            zIndex: '999999',
            background: 'rgba(15, 23, 42, 0.88)',
            color: '#fff', fontSize: '20px', fontWeight: '600',
            fontFamily: 'system-ui, sans-serif',
            textAlign: 'center', padding: '14px 20px',
            letterSpacing: '0.5px',
            backdropFilter: 'blur(6px)',
            borderBottom: '2px solid rgba(99, 102, 241, 0.6)',
            boxShadow: '0 4px 24px rgba(0,0,0,0.3)',
        });
        document.body.appendChild(div);
    }""",
        text,
    )


def slow_scroll(page, steps=5, delay_ms=600):
    for _ in range(steps):
        page.evaluate(
            f"window.scrollBy({{ top: {page.viewport_size['height'] // 3}, behavior: 'smooth' }})"
        )
        page.wait_for_timeout(delay_ms)


def _inject_vault_hider(page):
    """Inject CSS + MutationObserver to hide all vault/session modals."""
    page.evaluate("""() => {
        if (document.getElementById('hide-vault')) return;
        const style = document.createElement('style');
        style.id = 'hide-vault';
        style.textContent = `
            div.fixed.inset-0.z-50,
            div[class*="fixed"][class*="inset-0"][class*="z-50"] {
                display: none !important;
                opacity: 0 !important;
                pointer-events: none !important;
            }
        `;
        document.head.appendChild(style);
        const obs = new MutationObserver(() => {
            document.querySelectorAll('div.fixed.inset-0').forEach(el => {
                if (el.querySelector('input[type=password]') ||
                    el.textContent.includes('Sesiune') ||
                    el.textContent.includes('Deblocare') ||
                    el.textContent.includes('blocat') ||
                    el.textContent.includes('Vault') ||
                    el.textContent.includes('Seif')) {
                    el.remove();
                }
            });
        });
        obs.observe(document.body, { childList: true, subtree: true });
    }""")


def dismiss_vault(page, password):
    """Dismiss vault unlock modal if it appears."""
    try:
        modal = page.locator('div:has-text("Sesiune Expir") input[type="password"], div:has-text("Deblocare") input[type="password"]').first
        if modal.is_visible(timeout=2000):
            modal.fill(password)
            page.wait_for_timeout(300)
            page.locator('button:has-text("Deblocare"), button:has-text("Unlock")').first.click()
            page.wait_for_timeout(2000)
            print("   -> Vault unlocked")
    except Exception:
        pass


def nav_sidebar(page, link_text, password, pause=4):
    """Navigate via sidebar click (SPA routing, preserves vault session)."""
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(300)
    # ALWAYS dismiss vault first — it blocks clicks
    dismiss_vault(page, password)
    page.wait_for_timeout(300)
    dismiss_vault(page, password)  # Double-check
    page.wait_for_timeout(300)
    try:
        link = page.locator(f'nav a:has-text("{link_text}"), aside a:has-text("{link_text}"), a[href]:has-text("{link_text}")').first
        link.click(timeout=5000)
    except Exception:
        # Vault might have reappeared — dismiss again and retry
        dismiss_vault(page, password)
        page.wait_for_timeout(500)
        try:
            link = page.locator(f'a[title*="{link_text}"], a[aria-label*="{link_text}"]').first
            link.click(timeout=5000)
        except Exception:
            # Last resort: JS navigation
            href_map = {
                "Documente": "/documents", "Biomarkeri": "/biomarkers",
                "Doctor AI": "/health", "Stil de Via": "/lifestyle",
                "Abonament": "/billing", "Set\u0103ri": "/settings",
                "Panou": "/",
            }
            for key, href in href_map.items():
                if key in link_text:
                    page.evaluate(f"window.history.pushState({{}}, '', '{href}'); window.dispatchEvent(new PopStateEvent('popstate'))")
                    page.wait_for_timeout(1000)
                    break
    page.wait_for_timeout(2000)
    _inject_vault_hider(page)
    page.wait_for_timeout(int(pause * 1000))


def run_demo(email, password, headed):
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
            locale="ro",
            color_scheme="light",
        )

        page = context.new_page()

        # CRITICAL: Route handler to intercept and block vault-related responses
        # Plus CSS injection via add_init_script
        def handle_route(route):
            """Block API calls that trigger vault unlock modal."""
            url = route.request.url
            if "/auth/unlock" in url or "/vault" in url:
                route.fulfill(status=200, content_type="application/json", body='{"status":"ok"}')
            else:
                route.continue_()

        context.route("**/auth/unlock**", handle_route)
        context.route("**/vault**", handle_route)

        context.add_init_script("""
            (function() {
                // Nuclear option: override the CSS for ANY fixed overlay with backdrop
                var css = document.createElement('style');
                css.textContent = [
                    '.fixed.inset-0.z-50 { display:none !important; }',
                    '.fixed.inset-0[class*="backdrop"] { display:none !important; }',
                    '.fixed.inset-0[class*="bg-black"] { display:none !important; }',
                    'div[class*="fixed"][class*="inset-0"][class*="z-50"] { display:none !important; }'
                ].join('\\n');
                (document.head || document.documentElement).appendChild(css);

                // Poll every 100ms to remove vault modals (faster than MutationObserver)
                setInterval(function() {
                    document.querySelectorAll('.fixed.inset-0').forEach(function(el) {
                        var t = (el.textContent || '').toLowerCase();
                        if (t.indexOf('sesiune') !== -1 || t.indexOf('deblocare') !== -1 ||
                            t.indexOf('blocat') !== -1 || t.indexOf('expir') !== -1 ||
                            t.indexOf('seif') !== -1 || t.indexOf('vault') !== -1) {
                            el.parentNode.removeChild(el);
                        }
                    });
                }, 100);
            })();
        """)

        try:
            # ── 1. Landing page ─────────────────────────────
            print("[1/10] Landing page...")
            page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
            # Dismiss cookies AND pre-inject vault modal hider
            page.evaluate("""() => {
                localStorage.setItem('cookie_consent', 'true');
                localStorage.setItem('cookie_preferences', JSON.stringify({essential:true}));
            }""")
            _inject_vault_hider(page)
            page.reload(wait_until="networkidle")
            _inject_vault_hider(page)
            inject_overlay(page, OVERLAYS["home"])
            page.wait_for_timeout(3000)
            slow_scroll(page, steps=2, delay_ms=700)
            page.wait_for_timeout(1000)

            # ── 2. Login ────────────────────────────────────
            print("[2/10] Login...")
            page.goto(f"{BASE_URL}/login", wait_until="networkidle", timeout=20000)
            # Re-inject vault hider (page.goto reloads DOM)
            _inject_vault_hider(page)
            inject_overlay(page, OVERLAYS["login"])
            page.wait_for_timeout(1000)
            page.locator("input[type=email], input[name=email], input[placeholder*=email]").first.fill(email)
            page.wait_for_timeout(400)
            page.locator("input[type=password]").first.fill(password)
            page.wait_for_timeout(500)
            page.locator("button[type=submit]").first.click()
            page.wait_for_timeout(4000)

            # Handle vault unlock after login — do it silently
            # First hide the modal visually, then interact with it
            _inject_vault_hider(page)
            page.wait_for_timeout(500)
            # Now unlock vault via JS (fill password and click without showing modal)
            page.evaluate("""(pw) => {
                const inputs = document.querySelectorAll('input[type=password]');
                const lastInput = inputs[inputs.length - 1];
                if (lastInput) {
                    // Temporarily show the modal to interact
                    const modal = lastInput.closest('div.fixed.inset-0') || lastInput.closest('div[class*="fixed"]');
                    if (modal) {
                        modal.style.display = 'block';
                        modal.style.opacity = '0'; // invisible but interactable
                    }
                }
            }""", password)
            page.wait_for_timeout(300)
            try:
                pw_field = page.locator('input[type=password]').first
                if pw_field.is_visible(timeout=1000):
                    pw_field.fill(password)
                    page.locator('button:has-text("Deblocare"), button:has-text("Unlock")').first.click()
                    page.wait_for_timeout(2000)
            except Exception:
                pass
            _inject_vault_hider(page)
            page.wait_for_timeout(1000)

            # ── 3. Dashboard (already here after login) ─────
            print("[3/10] Dashboard...")
            inject_overlay(page, OVERLAYS["dashboard"])
            dismiss_vault(page, password)
            page.wait_for_timeout(4000)
            slow_scroll(page, steps=2, delay_ms=700)
            page.wait_for_timeout(1000)
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(500)

            # ── From here on, use sidebar clicks (SPA nav) ──

            # ── 4. Documents ────────────────────────────────
            print("[4/10] Documents...")
            nav_sidebar(page, "Documente", password, pause=3)
            inject_overlay(page, OVERLAYS["documents"])
            page.wait_for_timeout(2000)
            slow_scroll(page, steps=2, delay_ms=600)
            page.wait_for_timeout(1000)

            # ── 5. Biomarkers ───────────────────────────────
            print("[5/10] Biomarkers...")
            nav_sidebar(page, "Biomarkeri", password, pause=3)
            inject_overlay(page, OVERLAYS["biomarkers"])
            page.wait_for_timeout(2000)
            slow_scroll(page, steps=3, delay_ms=600)
            page.wait_for_timeout(1000)

            # ── 6. Evolution ────────────────────────────────
            print("[6/10] Evolution charts...")
            # Try clicking an evolution link from biomarkers page
            evo_link = page.locator('a[href*="/evolution/"]').first
            try:
                if evo_link.is_visible(timeout=2000):
                    evo_link.click()
                    page.wait_for_timeout(3000)
                    dismiss_vault(page, password)
                else:
                    # Navigate via sidebar to Biomarkeri first, then try
                    nav_sidebar(page, "Biomarkeri", password, pause=2)
            except Exception:
                pass
            inject_overlay(page, OVERLAYS["evolution"])
            page.wait_for_timeout(3000)
            slow_scroll(page, steps=2, delay_ms=600)
            page.wait_for_timeout(1000)

            # ── 7. Health Reports ───────────────────────────
            print("[7/10] Health Reports...")
            nav_sidebar(page, "Doctor AI", password, pause=3)
            inject_overlay(page, OVERLAYS["health"])
            page.wait_for_timeout(2000)
            slow_scroll(page, steps=2, delay_ms=600)
            page.wait_for_timeout(1000)

            # ── 8. Lifestyle ────────────────────────────────
            print("[8/10] Lifestyle...")
            nav_sidebar(page, "Stil de Via", password, pause=3)
            inject_overlay(page, OVERLAYS["lifestyle"])
            page.wait_for_timeout(2000)
            slow_scroll(page, steps=2, delay_ms=600)
            page.wait_for_timeout(1000)

            # ── 9. Billing ──────────────────────────────────
            print("[9/10] Billing...")
            nav_sidebar(page, "Abonament", password, pause=2)
            inject_overlay(page, OVERLAYS["billing"])
            page.wait_for_timeout(2000)

            # ── 10. Settings ────────────────────────────────
            print("[10/10] Settings...")
            nav_sidebar(page, "Set\u0103ri", password, pause=2)
            inject_overlay(page, OVERLAYS["settings"])
            page.wait_for_timeout(2000)
            slow_scroll(page, steps=2, delay_ms=500)
            page.wait_for_timeout(1000)

            # ── Logout ──────────────────────────────────────
            print("Logging out...")
            inject_overlay(page, OVERLAYS["logout"])
            page.wait_for_timeout(2000)
            try:
                page.locator('button:has-text("Deconectare"), button:has-text("Logout")').first.click()
                page.wait_for_timeout(2000)
            except Exception:
                pass

        except Exception as e:
            print(f"\n[ERROR] Demo recording failed: {e}")
            raise
        finally:
            page.close()
            context.close()
            browser.close()

    # Move the recorded video
    recordings = sorted(output_dir.glob("*.webm"), key=lambda f: f.stat().st_mtime)
    if recordings:
        latest = recordings[-1]
        shutil.move(str(latest), str(final_video))
        print(f"\n{'='*60}")
        print(f"Demo video saved: {final_video}")
        print(f"{'='*60}")
    else:
        print("\n[WARNING] No video file found.")

    try:
        shutil.rmtree(output_dir, ignore_errors=True)
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="Record demo video")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--headed", action="store_true", default=False)
    args = parser.parse_args()
    run_demo(args.email, args.password, args.headed)


if __name__ == "__main__":
    main()
