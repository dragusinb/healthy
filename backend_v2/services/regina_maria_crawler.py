import os
import datetime
from typing import Dict, Any, List
from playwright.sync_api import Page
from backend_v2.services.base import BaseCrawler


class ReginaMariaCrawler(BaseCrawler):

    def __init__(self, headless: bool = False):  # Default to non-headless for reCAPTCHA
        super().__init__("regina_maria", headless)
        self.login_url = "https://contulmeu.reginamaria.ro/#/login"
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

    def login_sync(self, page: Page, credentials: Dict[str, str]):
        self.log("Navigating to login page...")
        page.goto(self.login_url, wait_until="domcontentloaded")

        # Handle cookie consent
        self._dismiss_cookie_consent(page)

        self.log("Filling credentials...")
        page.wait_for_timeout(1000)

        # Fill username
        username_input = page.locator("#input-username")
        username_input.click(timeout=5000)
        username_input.fill("")
        username_input.type(credentials["username"], delay=50)

        # Fill password
        password_input = page.locator("#input-password")
        password_input.click(timeout=5000)
        password_input.fill("")
        password_input.type(credentials["password"], delay=50)

        page.screenshot(path=f"{self.download_dir}/pre_login_filled.png")

        self.log("Clicking login...")
        page.wait_for_timeout(500)

        # Remove overlay before clicking (in case it reappeared)
        self._dismiss_cookie_consent(page)

        # Try multiple methods to submit the login form
        login_clicked = False

        # Method 1: Click the submit button directly
        try:
            submit_btn = page.locator("button[type='submit']")
            if submit_btn.count() > 0:
                submit_btn.first.click(timeout=3000, force=True)
                login_clicked = True
                self.log("Clicked submit button")
        except Exception as e:
            self.log(f"Submit button click failed: {e}")

        # Method 2: Try by class
        if not login_clicked:
            try:
                page.click("button.k-button-solid-primary", timeout=2000, force=True)
                login_clicked = True
                self.log("Clicked primary button by class")
            except:
                pass

        # Method 3: Press Enter
        if not login_clicked:
            self.log("Pressing Enter to login...")
            page.keyboard.press("Enter")

        self.log("Checking login status...")

        # Check for reCAPTCHA/Error/Success loop
        # Wait up to 3 minutes for manual reCAPTCHA solving (36 * 5s = 180s)
        for i in range(36):
            current_url = page.url
            content = page.content()

            # 1. Success - check for dashboard or any authenticated page
            # Root URL /#/ also indicates successful login (redirects there)
            if "login" not in current_url.lower():
                # Check if we're on an authenticated page
                if any(x in current_url.lower() for x in ["dashboard", "pacient", "acasa"]) or current_url.endswith("/#/") or current_url.endswith("/#"):
                    self.log("Login Successful (Authenticated page detected).")
                    return

            # 2. ReCAPTCHA Detection
            if "recaptcha" in content.lower() or "g-recaptcha" in content.lower():
                if i == 0:  # Only log once
                    self.log("reCAPTCHA detected! Please solve it manually in the browser window.")
                    self.log("Waiting for manual reCAPTCHA solution...")

            # 3. Error Message
            if "Date de autentificare incorecte" in content or "Incercare de autentificare nereusita" in content:
                raise Exception("Invalid credentials detected on page.")

            # 4. 404 Recovery - might have been redirected oddly
            if "404" in current_url and "login" not in current_url:
                self.log("Detected 404 Page. Attempting to recover to Dashboard...")
                try:
                    page.goto(self.dashboard_url)
                    page.wait_for_load_state("domcontentloaded")
                    page.wait_for_timeout(2000)
                    if "dashboard" in page.url.lower() or "pacient" in page.url.lower():
                        self.log("Successfully recovered to dashboard.")
                        return
                except:
                    pass

            if i % 6 == 0:  # Log every 30 seconds
                self.log(f"Waiting for login... (Attempt {i+1}/36) URL: {current_url}")
            page.wait_for_timeout(5000)

        # Final check
        final_url = page.url
        if "login" not in final_url.lower() and (
            any(x in final_url.lower() for x in ["dashboard", "pacient"]) or
            final_url.endswith("/#/") or final_url.endswith("/#")
        ):
            self.log("Login seemingly successful.")
        else:
            self.log(f"Stuck on URL: {final_url}")
            page.screenshot(path=f"{self.download_dir}/login_stuck.png")
            raise Exception(f"Login failed - Timed out waiting for Dashboard. Stuck at {final_url}")

    def navigate_to_records_sync(self, page: Page):
        self.log(f"Navigating to {self.analize_url}...")

        page.goto(self.analize_url, wait_until="domcontentloaded")

        self.log("Waiting for SPA to render...")
        page.wait_for_timeout(5000)

        # Dismiss cookie consent if it reappeared
        self._dismiss_cookie_consent(page)

        self.log("Navigated to records list.")

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
        self.log(f"Processing {len(download_btns)} download buttons...")

        for i, btn in enumerate(download_btns):
            try:
                self.log(f"Processing document {i+1}/{len(download_btns)}...")

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
                        filename = download.suggested_filename
                        target_path = os.path.join(self.download_dir, filename)
                    if os.path.exists(target_path):
                        os.remove(target_path)
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

        self.log(f"Found {len(detail_btns)} detail page buttons to process.")

        # Process each detail page
        for i, btn in enumerate(detail_btns[:20]):  # Limit to 20
            try:
                self.log(f"Accessing detail page {i+1}/{min(len(detail_btns), 20)}...")

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
