import os
import datetime
import logging
from typing import Dict, Any, List
from playwright.sync_api import Page

try:
    from backend_v2.services.base import BaseCrawler
    from backend_v2.services.captcha_solver import CaptchaSolver, extract_recaptcha_sitekey, inject_captcha_token
except ImportError:
    from services.base import BaseCrawler
    from services.captcha_solver import CaptchaSolver, extract_recaptcha_sitekey, inject_captcha_token

logger = logging.getLogger(__name__)


class CaptchaRequiredError(Exception):
    """Raised when CAPTCHA is detected and visible browser is needed."""
    pass


class ReginaMariaCrawler(BaseCrawler):

    def __init__(self, headless: bool = True, user_id: int = None):  # Headless by default
        super().__init__("regina_maria", headless, user_id)
        # Main page has the login form
        self.login_url = "https://contulmeu.reginamaria.ro/#/"
        self.dashboard_url = "https://contulmeu.reginamaria.ro/#/Pacient/Dashboard"
        self.analize_url = "https://contulmeu.reginamaria.ro/#/Pacient/Analize"

    def _dismiss_cookie_consent(self, page: Page):
        """Aggressively dismiss cookie consent dialog."""
        self.log("Handling cookie consent...")
        page.wait_for_timeout(2000)

        # Method 1: Try clicking the accept button
        for text in ["Accept toate", "Accept toate cookie-urile", "De acord", "Accept"]:
            try:
                btn = page.get_by_text(text, exact=False)
                if btn.count() > 0:
                    btn.first.click(timeout=3000)
                    self.log(f"Clicked cookie button: {text}")
                    page.wait_for_timeout(1000)
                    return
            except:
                pass

        # Method 2: Click by ID (OneTrust specific)
        try:
            accept_btn = page.locator("#onetrust-accept-btn-handler")
            if accept_btn.count() > 0:
                accept_btn.click(timeout=3000)
                self.log("Clicked OneTrust accept button by ID")
                page.wait_for_timeout(1000)
                return
        except:
            pass

        # Method 3: Force remove the overlay via JavaScript
        try:
            page.evaluate("""
                // Remove OneTrust overlay
                const overlay = document.querySelector('.onetrust-pc-dark-filter');
                if (overlay) overlay.remove();

                // Remove OneTrust banner
                const banner = document.querySelector('#onetrust-consent-sdk');
                if (banner) banner.remove();

                // Remove any onetrust elements
                document.querySelectorAll('[class*="onetrust"]').forEach(el => el.remove());
            """)
            self.log("Removed cookie consent overlay via JavaScript")
        except Exception as e:
            self.log(f"JS overlay removal failed: {e}")

        # Method 4: Remove Usercentrics overlay (newer than OneTrust)
        # This overlay uses an <aside> with pointer-events that blocks all clicks
        try:
            removed = page.evaluate("""
                let removed = 0;
                // Remove the main Usercentrics element
                const uc = document.querySelector('#usercentrics-cmp-ui');
                if (uc) { uc.remove(); removed++; }
                // Remove by attribute patterns
                document.querySelectorAll('[id*="usercentrics"], [class*="usercentrics"]').forEach(el => { el.remove(); removed++; });
                // Remove any aside elements that intercept pointer events (consent overlays)
                document.querySelectorAll('aside[data-nosnippet]').forEach(el => { el.remove(); removed++; });
                // Nuclear option: remove ANY element covering the page with pointer-events
                // that isn't part of the app itself
                document.querySelectorAll('aside, [class*="cmp"], [class*="consent"], [class*="cookie"]').forEach(el => {
                    const style = window.getComputedStyle(el);
                    if (style.position === 'fixed' || style.position === 'absolute') {
                        el.remove(); removed++;
                    }
                });
                return removed;
            """)
            self.log(f"Removed {removed} Usercentrics/consent overlay elements via JavaScript")
        except Exception as e:
            self.log(f"Usercentrics removal failed: {e}")

    def _force_remove_overlays(self, page: Page):
        """Remove any overlay elements that block pointer events (Usercentrics, OneTrust, etc.)."""
        try:
            page.evaluate("""
                // Remove Usercentrics
                document.querySelectorAll('#usercentrics-cmp-ui, [id*="usercentrics"], aside[data-nosnippet]').forEach(el => el.remove());
                // Remove OneTrust
                document.querySelectorAll('#onetrust-consent-sdk, .onetrust-pc-dark-filter, [class*="onetrust"]').forEach(el => el.remove());
                // Remove any fixed/absolute positioned overlays that cover the page
                document.querySelectorAll('aside, [class*="cmp"], [class*="consent"], [class*="cookie-banner"]').forEach(el => {
                    const style = window.getComputedStyle(el);
                    if (style.position === 'fixed' || style.position === 'absolute') el.remove();
                });
            """)
        except Exception:
            pass

    def login_sync(self, page: Page, credentials: Dict[str, str]):
        self.log("Navigating to login page...")
        page.goto(self.login_url, wait_until="domcontentloaded")

        # Handle cookie consent
        self._dismiss_cookie_consent(page)

        self.log("Filling credentials...")
        page.wait_for_timeout(1000)

        # Remove all overlays that block interaction
        self._force_remove_overlays(page)

        # Use Playwright type() to simulate real keystrokes — this triggers Angular's
        # model binding correctly (unlike setting input.value via JS which Angular ignores).
        # Clear first, then type character by character.
        username_input = page.locator("#input-username")
        password_input = page.locator("#input-password")

        # Focus and type via JS focus + Playwright keyboard (bypasses overlay click issues)
        page.evaluate("document.querySelector('#input-username').focus()")
        page.keyboard.press("Control+a")
        page.keyboard.type(credentials["username"], delay=20)

        page.evaluate("document.querySelector('#input-password').focus()")
        page.keyboard.press("Control+a")
        page.keyboard.type(credentials["password"], delay=20)

        self.log("Filled credentials via keyboard input")

        page.screenshot(path=f"{self.download_dir}/pre_login_filled.png")

        self.log("Clicking login...")
        page.wait_for_timeout(500)

        # Remove overlay before clicking submit
        self._force_remove_overlays(page)

        # Submit the login form via JS button click (NOT form.submit() which bypasses Angular)
        login_clicked = False

        # Method 1: JavaScript button click (immune to overlays, triggers Angular handler)
        try:
            login_clicked = page.evaluate("""
                () => {
                    const submitBtn = document.querySelector("button[type='submit']");
                    if (submitBtn) { submitBtn.click(); return true; }
                    const primaryBtn = document.querySelector("button.k-button-solid-primary");
                    if (primaryBtn) { primaryBtn.click(); return true; }
                    return false;
                }
            """)
            if login_clicked:
                self.log("Submitted login via JavaScript button click")
        except Exception as e:
            self.log(f"JS submit failed: {e}")

        # Method 2: Press Enter (triggers Angular form submit)
        if not login_clicked:
            self.log("Pressing Enter to login...")
            page.keyboard.press("Enter")

        self.log("Checking login status...")

        # Track CAPTCHA solving attempts to avoid excessive costs
        captcha_solve_attempts = 0
        max_captcha_attempts = 3  # Limit to 3 auto-solve attempts

        # Check for reCAPTCHA/Error/Success loop
        # Wait up to 3 minutes for manual reCAPTCHA solving (36 * 5s = 180s)
        for i in range(36):
            current_url = page.url
            content = page.content()

            # 1. Check if we're actually authenticated by looking for authenticated UI elements
            # Look for elements that only appear when logged in
            is_authenticated = self._check_authenticated(page)
            if is_authenticated:
                self.log("Login Successful (Authenticated content detected).")
                return

            # 2. ReCAPTCHA Detection - try auto-solve first
            if "recaptcha" in content.lower() or "g-recaptcha" in content.lower():
                # Only attempt auto-solve a limited number of times
                if captcha_solve_attempts < max_captcha_attempts:
                    captcha_solve_attempts += 1
                    self.log(f"reCAPTCHA detected! Attempting automatic solving (attempt {captcha_solve_attempts}/{max_captcha_attempts})...")

                    # Try to solve automatically using CAPTCHA service
                    try:
                        solved = self._solve_recaptcha(page)
                        if solved:
                            self.log("reCAPTCHA solved! Waiting for token processing...")
                            page.wait_for_timeout(3000)  # Wait for callback to process

                            # Check if the page auto-submitted after CAPTCHA solve
                            current_after_captcha = page.url
                            if current_after_captcha != current_url:
                                self.log(f"Page navigated after CAPTCHA: {current_after_captcha}")

                            # Check if already authenticated (invisible CAPTCHA may auto-submit)
                            if self._check_authenticated(page):
                                self.log("Login successful after CAPTCHA solve (auto-submit)!")
                                return

                            # For invisible reCAPTCHA, the callback should have auto-submitted.
                            # If not, force submit via JS button click (never form.submit which bypasses Angular)
                            self.log("Submitting login form after CAPTCHA...")
                            try:
                                page.evaluate("""
                                    () => {
                                        // Enable submit button if Angular disabled it
                                        const submitBtn = document.querySelector("button[type='submit']");
                                        if (submitBtn) {
                                            submitBtn.disabled = false;
                                            submitBtn.removeAttribute('disabled');
                                            submitBtn.click();
                                        }
                                    }
                                """)
                                self.log("Forced submit via JavaScript button click")
                            except Exception as submit_err:
                                self.log(f"JS submit failed: {submit_err}")
                                page.keyboard.press("Enter")

                            page.wait_for_timeout(5000)  # Wait for login to process
                            page.screenshot(path=f"{self.download_dir}/after_captcha_submit.png")

                            # Check if we're now authenticated
                            if self._check_authenticated(page):
                                self.log("Login successful after CAPTCHA solve!")
                                return

                            # Log what we see now
                            new_content = page.content()
                            if "recaptcha" in new_content.lower():
                                self.log("reCAPTCHA still present after submission - token may have expired")
                            elif "Date de autentificare incorecte" in new_content:
                                self.log("Invalid credentials message after CAPTCHA")
                            else:
                                self.log(f"After CAPTCHA URL: {page.url}")

                            continue  # Continue checking login status
                    except Exception as captcha_error:
                        self.log(f"Auto CAPTCHA solve failed: {captcha_error}")

                # If we've exhausted auto-solve attempts or it failed
                if captcha_solve_attempts >= max_captcha_attempts:
                    if self.headless:
                        self.log(f"reCAPTCHA still present after {max_captcha_attempts} auto-solve attempts - need visible browser")
                        raise CaptchaRequiredError("reCAPTCHA detected - visible browser required")
                    if captcha_solve_attempts == max_captcha_attempts:  # Only log once
                        self.log("Auto CAPTCHA solving exhausted. Please solve manually in the browser window.")
                        self.log("Waiting for manual reCAPTCHA solution...")

            # 3. Error Message
            if "Date de autentificare incorecte" in content or "Incercare de autentificare nereusita" in content:
                raise Exception("Invalid credentials detected on page.")

            # 4. 404 Recovery - navigate to main page and check again
            if "404" in current_url:
                self.log("Detected 404 Page. Navigating to main page...")
                try:
                    page.goto("https://contulmeu.reginamaria.ro/#/")
                    page.wait_for_load_state("domcontentloaded")
                    page.wait_for_timeout(3000)
                except:
                    pass

            if i % 6 == 0:  # Log every 30 seconds
                self.log(f"Waiting for login... (Attempt {i+1}/36) URL: {current_url}")
            page.wait_for_timeout(5000)

        # Final check
        if self._check_authenticated(page):
            self.log("Login successful after wait.")
        else:
            self.log(f"Stuck on URL: {page.url}")
            page.screenshot(path=f"{self.download_dir}/login_stuck.png")
            raise Exception(f"Login failed - Could not detect authenticated session. Stuck at {page.url}")

    def _solve_recaptcha(self, page: Page) -> bool:
        """
        Attempt to solve reCAPTCHA using external service.

        Returns:
            True if CAPTCHA was solved and token injected
        """
        try:
            # Screenshot before solving
            page.screenshot(path=f"{self.download_dir}/captcha_before.png")

            # Detect CAPTCHA type (visible vs invisible)
            captcha_info = page.evaluate("""
                () => {
                    const recaptchaDiv = document.querySelector('.g-recaptcha');
                    const iframe = document.querySelector('iframe[src*="recaptcha"]');

                    let isInvisible = false;
                    let siteKey = null;
                    let dataCallback = null;

                    if (recaptchaDiv) {
                        siteKey = recaptchaDiv.getAttribute('data-sitekey');
                        dataCallback = recaptchaDiv.getAttribute('data-callback');
                        isInvisible = recaptchaDiv.getAttribute('data-size') === 'invisible';
                    }

                    if (iframe && iframe.src) {
                        const match = iframe.src.match(/[?&]k=([^&]+)/);
                        if (match && !siteKey) siteKey = match[1];
                        if (iframe.src.includes('invisible')) isInvisible = true;
                    }

                    return {
                        isInvisible: isInvisible,
                        siteKey: siteKey,
                        dataCallback: dataCallback,
                        hasIframe: !!iframe,
                        iframeSrc: iframe ? iframe.src.substring(0, 100) : null
                    };
                }
            """)

            self.log(f"CAPTCHA info: invisible={captcha_info.get('isInvisible')}, callback={captcha_info.get('dataCallback')}")

            # Extract the site key
            site_key = captcha_info.get('siteKey') or extract_recaptcha_sitekey(page)
            if not site_key:
                self.log("Could not find reCAPTCHA site key")
                return False

            self.log(f"Found reCAPTCHA site key: {site_key[:20]}...")

            # Get the current page URL
            page_url = page.url

            # Initialize solver and solve
            solver = CaptchaSolver()

            # Check balance first
            balance = solver.get_balance()
            self.log(f"CAPTCHA service balance: ${balance:.2f}")
            if balance < 0.01:
                self.log("CAPTCHA service balance too low!")
                return False

            # Solve the CAPTCHA (pass invisible flag)
            is_invisible = captcha_info.get('isInvisible', False)
            self.log(f"Sending CAPTCHA to solving service (invisible={is_invisible})...")
            token = solver.solve_recaptcha_v2(page_url, site_key, invisible=is_invisible)

            if not token:
                self.log("CAPTCHA solving returned empty token")
                return False

            self.log(f"Got CAPTCHA token: {token[:50]}...")

            # Inject the token into the page
            success = inject_captcha_token(page, token)

            # Screenshot after injection
            page.screenshot(path=f"{self.download_dir}/captcha_after_inject.png")

            if success:
                self.log("CAPTCHA token injected successfully!")

                # If there's a callback, try to call it directly
                if captcha_info.get('dataCallback'):
                    callback_name = captcha_info['dataCallback']
                    self.log(f"Trying to call callback: {callback_name}")
                    try:
                        page.evaluate(f"""
                            (token) => {{
                                if (typeof window['{callback_name}'] === 'function') {{
                                    window['{callback_name}'](token);
                                    return true;
                                }}
                                // Try Angular scope
                                const scope = angular && angular.element(document.body).scope();
                                if (scope && typeof scope['{callback_name}'] === 'function') {{
                                    scope['{callback_name}'](token);
                                    return true;
                                }}
                                return false;
                            }}
                        """, token)
                    except Exception as cb_err:
                        self.log(f"Callback call failed: {cb_err}")

                return True
            else:
                self.log("Failed to inject CAPTCHA token")
                return False

        except Exception as e:
            self.log(f"CAPTCHA solving error: {e}")
            logger.exception("CAPTCHA solving failed")
            return False

    def _check_authenticated(self, page: Page, wait_for_spa: bool = True) -> bool:
        """Check if we're actually logged in by looking for authenticated UI elements."""
        try:
            # Wait for SPA to render if requested
            if wait_for_spa:
                page.wait_for_timeout(2000)

            # Check URL first - certain URLs definitively mean we're authenticated
            url = page.url.lower()
            if "pacient/dashboard" in url or "pacient/rezultate" in url or "pacient/programari" in url:
                self.log(f"Authenticated: URL confirms login ({page.url})")
                return True

            content = page.content()

            # Check for login page elements (means NOT authenticated)
            login_indicators = [
                "Intra in cont",
                "Creeaza cont nou",
                "Ai uitat parola",
                "input-username",
                "input-password",
                "Autentificare",
                "g-recaptcha"
            ]
            for indicator in login_indicators:
                if indicator in content:
                    return False

            # Check for authenticated elements (means logged in)
            auth_indicators = [
                "Deconectare",
                "Logout",
                "Programarile mele",
                "Rezultate analize",
                "Dosarul meu",
                "Bun venit",
                "Contul meu",
                "Profil",
                "Ieșire",
                "Iesire"
            ]
            for indicator in auth_indicators:
                if indicator in content:
                    self.log(f"Authenticated: found '{indicator}'")
                    return True

            # Also check URL patterns that indicate authenticated state
            if any(x in url for x in ["pacient", "dashboard", "contulmeu"]) and "login" not in url and "autentificare" not in url:
                # Check for user menu or profile indicators via selectors
                try:
                    # Wait for any dynamic content to load
                    page.wait_for_timeout(1000)

                    # Check for user avatar/menu (common in authenticated SPAs)
                    user_elements = page.locator("[class*='user'], [class*='avatar'], [class*='profile'], [data-testid*='user']")
                    if user_elements.count() > 0:
                        self.log("Authenticated: found user elements")
                        return True

                    # Check for logout button variants
                    logout_btn = page.locator("text=Deconectare, text=Logout, text=Iesire, text=Ieșire").first
                    if logout_btn.count() > 0:
                        self.log("Authenticated: found logout button")
                        return True
                except:
                    pass

            return False
        except Exception as e:
            self.log(f"Auth check error: {e}")
            return False

    def navigate_to_records_sync(self, page: Page):
        self.log(f"Navigating to {self.analize_url}...")

        page.goto(self.analize_url, wait_until="domcontentloaded")

        self.log("Waiting for SPA to render...")
        page.wait_for_timeout(5000)

        # Dismiss cookie consent if it reappeared
        self._dismiss_cookie_consent(page)

        self.log("Navigated to records list.")

    def get_expected_document_count(self, page: Page) -> int:
        """
        Extract the expected document count from the provider page.
        Looks for text like "Rezultate analize 33" or similar indicators.

        Returns:
            Expected document count, or -1 if not found
        """
        try:
            content = page.content()

            # Look for "Rezultate analize XX" pattern
            import re
            patterns = [
                r'Rezultate\s+analize[:\s]*(\d+)',
                r'(\d+)\s+rezultate',
                r'(\d+)\s+analize',
                r'Total[:\s]*(\d+)',
            ]

            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    count = int(match.group(1))
                    self.log(f"Found expected document count: {count}")
                    return count

            # Try to count visible document rows/cards
            doc_elements = page.locator("[class*='result'], [class*='analiz'], [class*='document']").all()
            if doc_elements:
                count = len(doc_elements)
                self.log(f"Counted {count} document elements on page")
                return count

            self.log("Could not determine expected document count")
            return -1

        except Exception as e:
            self.log(f"Error getting expected count: {e}")
            return -1

    def extract_documents_sync(self, page: Page) -> List[Dict[str, Any]]:
        extracted = []
        self.log("Scanning for documents...")

        # Take a screenshot of what we have
        page.screenshot(path=f"{self.download_dir}/analize_page_load_top.png")

        # Scroll to bottom to trigger any lazy loading
        self.log("Scrolling to trigger lazy loading...")
        for _ in range(5):
            page.mouse.wheel(0, 3000)
            page.wait_for_timeout(1500)

        page.screenshot(path=f"{self.download_dir}/analize_page_load_bottom.png")

        # Try multiple strategies to find download buttons

        # Strategy 1: Direct "Descarca" buttons
        download_btns = page.locator("button:has-text('Descarca')").all()
        self.log(f"Found {len(download_btns)} 'Descarca' buttons.")

        # Strategy 2: Look for download links/icons
        if len(download_btns) == 0:
            download_btns = page.locator("a:has-text('Descarca')").all()
            self.log(f"Found {len(download_btns)} 'Descarca' links.")

        # Strategy 3: Look for PDF icons or download icons
        if len(download_btns) == 0:
            download_btns = page.locator("[class*='download'], [class*='pdf'], a[href*='.pdf']").all()
            self.log(f"Found {len(download_btns)} download/PDF elements.")

        # Strategy 4: Navigate to detail pages and find downloads there
        if len(download_btns) == 0:
            self.log("No direct download buttons. Trying to access detail pages...")
            extracted = self._extract_from_detail_pages(page)
            return extracted

        # If we found download buttons, process them
        total_docs = len(download_btns)
        self.log(f"Processing {total_docs} download buttons...")

        for i, btn in enumerate(download_btns):
            try:
                current = i + 1
                self.log(f"Processing document {current}/{total_docs}...")
                self.update_status("downloading", f"Downloading {current}/{total_docs}", current, total_docs)

                # Scroll to the button
                btn.scroll_into_view_if_needed()
                page.wait_for_timeout(500)

                if not btn.is_visible():
                    self.log(f"Button {i} not visible, skipping.")
                    continue

                # Try to download
                download_success = False
                filename = f"regina_maria_doc_{i}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                target_path = os.path.join(self.download_dir, filename)

                # Method 1: expect_download
                try:
                    with page.expect_download(timeout=60000) as download_info:
                        btn.click()
                    download = download_info.value
                    if download.suggested_filename:
                        # Add index to filename to avoid overwriting
                        base_name = download.suggested_filename
                        name_part = base_name.rsplit('.', 1)[0] if '.' in base_name else base_name
                        ext_part = '.' + base_name.rsplit('.', 1)[1] if '.' in base_name else '.pdf'
                        filename = f"{name_part}_{i+1:03d}{ext_part}"
                        target_path = os.path.join(self.download_dir, filename)
                    # Don't remove existing - we want unique files
                    download.save_as(target_path)
                    download_success = True
                    self.log(f"Downloaded: {filename}")
                except Exception as e:
                    self.log(f"Download method failed: {e}")

                # Method 2: If click opens a new page with PDF
                if not download_success:
                    try:
                        with page.context.expect_page(timeout=10000) as new_page_info:
                            btn.click()
                        new_page = new_page_info.value
                        new_page.wait_for_load_state("domcontentloaded")

                        if ".pdf" in new_page.url.lower() or "download" in new_page.url.lower():
                            response = new_page.goto(new_page.url)
                            if response:
                                body = response.body()
                                with open(target_path, "wb") as f:
                                    f.write(body)
                                download_success = True
                                self.log(f"Downloaded from new page: {filename}")
                        new_page.close()
                    except Exception as e:
                        self.log(f"New page method failed: {e}")

                if download_success and os.path.exists(target_path):
                    extracted.append({
                        "filename": filename,
                        "local_path": target_path,
                        "date": datetime.datetime.now(),
                        "category": "Analize"
                    })

                # Delay between downloads
                page.wait_for_timeout(2000)

            except Exception as e:
                self.log(f"Failed to download document {i}: {e}")
                continue

        return extracted

    def _extract_from_detail_pages(self, page: Page) -> List[Dict[str, Any]]:
        """Extract documents by navigating to detail pages."""
        extracted = []

        # Look for buttons that navigate to detail pages
        detail_selectors = [
            "button:has-text('Vezi detalii')",
            "button:has-text('Vezi raport')",
            "button:has-text('Detalii')",
            "a:has-text('Vezi detalii')",
            "a:has-text('Vezi raport')",
        ]

        detail_btns = []
        for selector in detail_selectors:
            btns = page.locator(selector).all()
            if btns:
                detail_btns.extend(btns)
                self.log(f"Found {len(btns)} buttons with selector: {selector}")

        if not detail_btns:
            self.log("No detail page buttons found. Debug: listing all buttons...")
            all_btns = page.locator("button").all()
            for b in all_btns[:15]:
                txt = b.text_content()
                self.log(f" - Button: {txt.strip() if txt else '(empty)'}")
            return extracted

        total_docs = min(len(detail_btns), 20)
        self.log(f"Found {len(detail_btns)} detail page buttons to process (limit: {total_docs}).")

        # Process each detail page
        for i, btn in enumerate(detail_btns[:20]):  # Limit to 20
            try:
                current = i + 1
                self.log(f"Accessing detail page {current}/{total_docs}...")
                self.update_status("downloading", f"Downloading {current}/{total_docs}", current, total_docs)

                btn.scroll_into_view_if_needed()
                page.wait_for_timeout(500)

                # Click to navigate to detail page
                btn.click()
                page.wait_for_timeout(3000)

                # Take screenshot of detail page
                page.screenshot(path=f"{self.download_dir}/detail_page_{i}.png")

                # Look for download buttons on detail page
                download_selectors = [
                    "button:has-text('Descarca')",
                    "a:has-text('Descarca')",
                    "button:has-text('Download')",
                    "a[href*='.pdf']",
                    "[class*='download']",
                ]

                for selector in download_selectors:
                    download_btn = page.locator(selector).first
                    if download_btn.count() > 0:
                        try:
                            filename = f"rezultat_{i}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                            target_path = os.path.join(self.download_dir, filename)

                            with page.expect_download(timeout=60000) as download_info:
                                download_btn.click()
                            download = download_info.value
                            if download.suggested_filename:
                                filename = download.suggested_filename
                                target_path = os.path.join(self.download_dir, filename)
                            if os.path.exists(target_path):
                                os.remove(target_path)
                            download.save_as(target_path)

                            self.log(f"Downloaded: {filename}")
                            extracted.append({
                                "filename": filename,
                                "local_path": target_path,
                                "date": datetime.datetime.now(),
                                "category": "Analize"
                            })
                            break
                        except Exception as e:
                            self.log(f"Download from detail page failed: {e}")

                # Navigate back to the list
                page.go_back()
                page.wait_for_timeout(2000)

            except Exception as e:
                self.log(f"Failed to process detail page {i}: {e}")
                try:
                    page.goto(self.analize_url)
                    page.wait_for_timeout(3000)
                except:
                    pass
                continue

        return extracted
