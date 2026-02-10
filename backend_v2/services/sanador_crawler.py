import os
import datetime
import requests
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


class SanadorCrawler(BaseCrawler):
    """
    Crawler for Sanador Romania patient portal.

    Sanador is a major Romanian private healthcare provider.
    The portal allows patients to view and download their lab results.
    """

    def __init__(self, headless: bool = True, user_id: int = None):
        super().__init__("sanador", headless, user_id)
        # Sanador portal URLs - these may need verification
        self.login_url = "https://portal.sanador.ro/login"
        self.dashboard_url = "https://portal.sanador.ro/dashboard"
        self.results_url = "https://portal.sanador.ro/rezultate"
        # Alternative URLs to try
        self.alt_login_urls = [
            "https://contulmeu.sanador.ro/login",
            "https://rezultate.sanador.ro/login",
            "https://www.sanador.ro/cont",
            "https://www.sanador.ro/pacient",
        ]

    def _dismiss_cookie_consent(self, page: Page):
        """Dismiss cookie consent dialog if present."""
        self.log("Checking for cookie consent...")
        page.wait_for_timeout(2000)

        consent_selectors = [
            "text=Accept toate",
            "text=Acceptă toate",
            "text=Accept",
            "text=Accepta",
            "#onetrust-accept-btn-handler",
            "[id*='cookie'] button:has-text('Accept')",
            "[class*='cookie'] button:has-text('Accept')",
            "button:has-text('Sunt de acord')",
            ".btn-accept-cookies",
            "#accept-cookies",
        ]

        for selector in consent_selectors:
            try:
                btn = page.locator(selector).first
                if btn.count() > 0 and btn.is_visible():
                    btn.click(timeout=3000)
                    self.log(f"Clicked cookie consent: {selector}")
                    page.wait_for_timeout(1000)
                    return
            except Exception:
                pass

    def _check_authenticated(self, page: Page) -> bool:
        """Check if user is logged in."""
        try:
            content = page.content().lower()
            url = page.url.lower()

            # Login page indicators (NOT authenticated)
            if any(x in url for x in ["login", "auth", "signin", "autentificare"]):
                return False

            # Check for password field (indicates login form)
            try:
                pwd_field = page.locator("input[type='password']")
                if pwd_field.count() > 0 and pwd_field.first.is_visible():
                    return False
            except Exception:
                pass

            # Authenticated indicators
            auth_indicators = [
                "deconectare",
                "logout",
                "contul meu",
                "rezultate",
                "programari",
                "bine ai venit",
                "dashboard",
                "profil",
            ]
            for indicator in auth_indicators:
                if indicator in content:
                    return True

            # Check for authenticated URL patterns
            if any(x in url for x in ["dashboard", "rezultate", "cont", "profil", "pacient"]) and "login" not in url:
                return True

            return False
        except Exception:
            return False

    def _find_and_try_login_url(self, page: Page) -> str:
        """Try to find a working login URL."""
        # First try main URL
        try:
            page.goto(self.login_url, wait_until="domcontentloaded", timeout=30000)
            if "404" not in page.content() and "not found" not in page.content().lower():
                self.log(f"Using primary login URL: {self.login_url}")
                return self.login_url
        except Exception as e:
            self.log(f"Primary URL failed: {e}")

        # Try alternative URLs
        for url in self.alt_login_urls:
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                if "404" not in page.content() and "not found" not in page.content().lower():
                    self.log(f"Using alternative login URL: {url}")
                    self.login_url = url
                    return url
            except Exception as e:
                self.log(f"Alternative URL {url} failed: {e}")

        # Fallback to main site and look for login link
        try:
            page.goto("https://www.sanador.ro", wait_until="domcontentloaded")
            self._dismiss_cookie_consent(page)

            login_link = page.locator("a:has-text('Cont'), a:has-text('Login'), a:has-text('Autentificare'), a:has-text('Pacient')").first
            if login_link.count() > 0:
                login_link.click()
                page.wait_for_timeout(3000)
                self.login_url = page.url
                self.log(f"Found login via main site: {self.login_url}")
                return self.login_url
        except Exception as e:
            self.log(f"Main site login link search failed: {e}")

        return self.login_url

    def login_sync(self, page: Page, credentials: Dict[str, str]):
        """Perform login to Sanador portal."""
        self.log("Finding login page...")

        working_url = self._find_and_try_login_url(page)
        page.goto(working_url, wait_until="domcontentloaded")

        self._dismiss_cookie_consent(page)

        self.log("Looking for login form...")
        page.wait_for_timeout(2000)

        # Try to find username/email input
        username_selectors = [
            "input[name='email']",
            "input[name='username']",
            "input[name='user']",
            "input[name='cnp']",
            "input[type='email']",
            "#email",
            "#username",
            "#user",
            "#cnp",
            "[placeholder*='email' i]",
            "[placeholder*='cnp' i]",
            "[placeholder*='utilizator' i]",
            "input[autocomplete='email']",
            "input[autocomplete='username']",
        ]

        username_input = None
        for selector in username_selectors:
            try:
                elem = page.locator(selector).first
                if elem.count() > 0 and elem.is_visible():
                    username_input = elem
                    self.log(f"Found username input: {selector}")
                    break
            except Exception:
                pass

        if not username_input:
            # Try generic text input before password
            try:
                text_inputs = page.locator("input[type='text'], input:not([type])").all()
                visible_inputs = [i for i in text_inputs if i.is_visible()]
                if visible_inputs:
                    username_input = visible_inputs[0]
                    self.log("Found username input via generic text input")
            except Exception:
                pass

        if not username_input:
            page.screenshot(path=f"{self.download_dir}/login_no_username_field.png")
            raise Exception("Could not find username input field")

        # Fill username
        username_input.click()
        username_input.fill("")
        username_input.type(credentials["username"], delay=50)

        # Find and fill password
        password_input = page.locator("input[type='password']").first
        if password_input.count() == 0:
            page.screenshot(path=f"{self.download_dir}/login_no_password_field.png")
            raise Exception("Could not find password input field")

        password_input.click()
        password_input.fill("")
        password_input.type(credentials["password"], delay=50)

        page.screenshot(path=f"{self.download_dir}/pre_login.png")

        # Submit login
        self.log("Submitting login form...")

        submit_selectors = [
            "button[type='submit']",
            "input[type='submit']",
            "button:has-text('Autentificare')",
            "button:has-text('Conectare')",
            "button:has-text('Login')",
            "button:has-text('Intra')",
            ".btn-login",
            ".login-button",
        ]

        submitted = False
        for selector in submit_selectors:
            try:
                btn = page.locator(selector).first
                if btn.count() > 0 and btn.is_visible():
                    btn.click(timeout=5000)
                    submitted = True
                    self.log(f"Clicked submit: {selector}")
                    break
            except Exception:
                pass

        if not submitted:
            page.keyboard.press("Enter")
            self.log("Pressed Enter to submit")

        # Wait and check for CAPTCHA/success
        self._wait_for_login(page)

    def _wait_for_login(self, page: Page, max_attempts: int = 24):
        """Wait for login to complete, handling CAPTCHA if needed."""
        captcha_solve_attempts = 0
        max_captcha_attempts = 3

        for i in range(max_attempts):
            page.wait_for_timeout(5000)

            # Check if authenticated
            if self._check_authenticated(page):
                self.log("Login Successful!")
                return

            content = page.content()

            # Check for reCAPTCHA
            if "recaptcha" in content.lower() or "g-recaptcha" in content.lower():
                if captcha_solve_attempts < max_captcha_attempts:
                    captcha_solve_attempts += 1
                    self.log(f"CAPTCHA detected - attempt {captcha_solve_attempts}/{max_captcha_attempts}")

                    try:
                        if self._solve_recaptcha(page):
                            page.wait_for_timeout(2000)
                            # Re-submit after CAPTCHA
                            try:
                                page.locator("button[type='submit']").first.click(force=True)
                            except Exception:
                                page.keyboard.press("Enter")
                            page.wait_for_timeout(5000)

                            if self._check_authenticated(page):
                                self.log("Login successful after CAPTCHA!")
                                return
                    except Exception as e:
                        self.log(f"CAPTCHA solve failed: {e}")

                if captcha_solve_attempts >= max_captcha_attempts:
                    if self.headless:
                        raise CaptchaRequiredError("CAPTCHA detected - visible browser required")
                    self.log("Waiting for manual CAPTCHA solution...")

            # Check for error messages
            error_indicators = [
                "date de autentificare incorecte",
                "parola gresita",
                "utilizator inexistent",
                "invalid credentials",
                "email sau parola incorecta",
                "cont inexistent",
            ]
            for error in error_indicators:
                if error in content.lower():
                    raise Exception(f"Login failed: {error}")

            if i % 4 == 0:
                self.log(f"Waiting for login... ({i+1}/{max_attempts})")

        # Final check
        if not self._check_authenticated(page):
            page.screenshot(path=f"{self.download_dir}/login_failed.png")
            raise Exception(f"Login timeout - stuck at {page.url}")

    def _solve_recaptcha(self, page: Page) -> bool:
        """Attempt to solve reCAPTCHA using external service."""
        try:
            site_key = extract_recaptcha_sitekey(page)
            if not site_key:
                self.log("Could not find reCAPTCHA site key")
                return False

            self.log(f"Found reCAPTCHA site key: {site_key[:20]}...")

            solver = CaptchaSolver()
            balance = solver.get_balance()
            self.log(f"CAPTCHA service balance: ${balance:.2f}")

            if balance < 0.01:
                self.log("CAPTCHA service balance too low!")
                return False

            token = solver.solve_recaptcha_v2(page.url, site_key)
            if not token:
                return False

            self.log(f"Got CAPTCHA token: {token[:50]}...")
            return inject_captcha_token(page, token)

        except Exception as e:
            self.log(f"CAPTCHA solving error: {e}")
            return False

    def navigate_to_records_sync(self, page: Page):
        """Navigate to lab results page."""
        self.log(f"Navigating to results: {self.results_url}")

        # Try direct navigation first
        try:
            page.goto(self.results_url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)
            self._dismiss_cookie_consent(page)
        except Exception as e:
            self.log(f"Direct navigation failed: {e}")

        # If direct navigation doesn't work, try clicking menu items
        results_selectors = [
            "a:has-text('Rezultate')",
            "a:has-text('Analize')",
            "a:has-text('Documente')",
            "a:has-text('Istoric')",
            "[href*='rezultate']",
            "[href*='results']",
            "[href*='analize']",
            "[href*='documents']",
            "[href*='istoric']",
        ]

        for selector in results_selectors:
            try:
                link = page.locator(selector).first
                if link.count() > 0 and link.is_visible():
                    link.click()
                    self.log(f"Clicked results link: {selector}")
                    page.wait_for_timeout(3000)
                    break
            except Exception:
                pass

        page.screenshot(path=f"{self.download_dir}/results_page.png")
        self.log("Navigated to results page")

    def get_expected_document_count(self, page: Page) -> int:
        """Try to extract expected document count."""
        try:
            import re
            content = page.content()

            patterns = [
                r'(\d+)\s+rezultate',
                r'(\d+)\s+analize',
                r'Total[:\s]*(\d+)',
                r'Gasit[:\s]*(\d+)',
                r'(\d+)\s+documente',
            ]

            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    count = int(match.group(1))
                    self.log(f"Found expected count: {count}")
                    return count

            return -1
        except Exception:
            return -1

    def extract_documents_sync(self, page: Page) -> List[Dict[str, Any]]:
        """Extract and download documents."""
        extracted = []
        self.log("Scanning for documents...")

        page.screenshot(path=f"{self.download_dir}/extract_start.png")

        # Scroll to load lazy content
        for _ in range(5):
            page.mouse.wheel(0, 2000)
            page.wait_for_timeout(1500)

        # Get session cookies for authenticated requests
        cookies = page.context.cookies()
        cookie_header = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

        # Look for download buttons/links
        download_selectors = [
            "a[href*='.pdf']",
            "a[href*='download']",
            "a[href*='descarca']",
            "button:has-text('Descarca')",
            "button:has-text('Download')",
            "a:has-text('Descarca')",
            "a:has-text('PDF')",
            "[class*='download']",
            "[data-action='download']",
            ".pdf-link",
            ".download-btn",
        ]

        download_elements = []
        for selector in download_selectors:
            try:
                elements = page.locator(selector).all()
                if elements:
                    self.log(f"Found {len(elements)} elements with: {selector}")
                    download_elements.extend(elements)
            except Exception:
                pass

        if not download_elements:
            self.log("No download elements found. Trying detail page approach...")
            return self._extract_from_detail_pages(page)

        self.log(f"Processing {len(download_elements)} download elements...")

        # Process unique elements
        processed_urls = set()
        for i, elem in enumerate(download_elements[:50]):  # Limit to 50
            try:
                # Get href if available
                href = elem.get_attribute("href")
                if href and href in processed_urls:
                    continue
                if href:
                    processed_urls.add(href)

                self.log(f"Processing document {i+1}...")

                filename = f"sanador_doc_{i}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                target_path = os.path.join(self.download_dir, filename)

                # Try download
                download_success = False

                try:
                    elem.scroll_into_view_if_needed()
                    page.wait_for_timeout(500)

                    with page.expect_download(timeout=60000) as download_info:
                        elem.click()

                    download = download_info.value
                    if download.suggested_filename:
                        filename = f"{download.suggested_filename.rsplit('.', 1)[0]}_{i+1:03d}.pdf"
                        target_path = os.path.join(self.download_dir, filename)

                    download.save_as(target_path)
                    download_success = True
                    self.log(f"Downloaded: {filename}")
                except Exception as e:
                    self.log(f"Browser download failed: {e}")

                    # Try HTTP download
                    if href:
                        try:
                            download_success = self._download_via_http(page, href, target_path, cookie_header)
                        except Exception as e2:
                            self.log(f"HTTP download also failed: {e2}")

                if download_success and os.path.exists(target_path):
                    extracted.append({
                        "filename": filename,
                        "local_path": target_path,
                        "date": datetime.datetime.now(),
                        "category": "Analize Sanador"
                    })

                page.wait_for_timeout(1000)

            except Exception as e:
                self.log(f"Failed document {i}: {e}")
                continue

        return extracted

    def _download_via_http(self, page: Page, url: str, target_path: str, cookie_header: str) -> bool:
        """Download file via HTTP request."""
        # Make URL absolute if needed
        if url.startswith("/"):
            base_url = page.url.split("//")[0] + "//" + page.url.split("//")[1].split("/")[0]
            url = base_url + url

        try:
            headers = {
                "Cookie": cookie_header,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=60)
            if response.status_code == 200:
                with open(target_path, "wb") as f:
                    f.write(response.content)
                self.log(f"Downloaded via HTTP: {os.path.basename(target_path)}")
                return True
        except Exception as e:
            self.log(f"HTTP download failed: {e}")
        return False

    def _extract_from_detail_pages(self, page: Page) -> List[Dict[str, Any]]:
        """Navigate to detail pages to find downloads."""
        extracted = []

        detail_selectors = [
            "button:has-text('Detalii')",
            "button:has-text('Vezi')",
            "a:has-text('Detalii')",
            "a:has-text('Vezi raport')",
            "a:has-text('Vezi rezultat')",
            "[class*='detail']",
            "tr[onclick]",
            "[data-id]",
            ".result-item",
            ".document-item",
            ".analysis-row",
        ]

        detail_elements = []
        for selector in detail_selectors:
            try:
                elements = page.locator(selector).all()
                if elements:
                    detail_elements.extend(elements)
                    self.log(f"Found {len(elements)} detail elements: {selector}")
            except Exception:
                pass

        if not detail_elements:
            self.log("No detail elements found")
            page.screenshot(path=f"{self.download_dir}/no_details_found.png")
            return extracted

        results_url = page.url

        for i, elem in enumerate(detail_elements[:30]):  # Limit to 30
            try:
                self.log(f"Opening detail page {i+1}/{min(len(detail_elements), 30)}...")

                elem.scroll_into_view_if_needed()
                page.wait_for_timeout(500)
                elem.click()
                page.wait_for_timeout(3000)

                page.screenshot(path=f"{self.download_dir}/detail_{i}.png")

                # Look for download on detail page
                for dl_selector in ["a[href*='.pdf']", "button:has-text('Descarca')", "a:has-text('Descarca')"]:
                    try:
                        dl_btn = page.locator(dl_selector).first
                        if dl_btn.count() > 0 and dl_btn.is_visible():
                            filename = f"sanador_detail_{i}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                            target_path = os.path.join(self.download_dir, filename)

                            with page.expect_download(timeout=60000) as download_info:
                                dl_btn.click()

                            download = download_info.value
                            if download.suggested_filename:
                                filename = download.suggested_filename
                                target_path = os.path.join(self.download_dir, filename)

                            download.save_as(target_path)

                            extracted.append({
                                "filename": filename,
                                "local_path": target_path,
                                "date": datetime.datetime.now(),
                                "category": "Analize Sanador"
                            })
                            self.log(f"Downloaded: {filename}")
                            break
                    except Exception as e:
                        self.log(f"Download from detail failed: {e}")

                # Go back
                page.go_back()
                page.wait_for_timeout(2000)

            except Exception as e:
                self.log(f"Detail page {i} failed: {e}")
                try:
                    page.goto(results_url)
                    page.wait_for_timeout(3000)
                except Exception:
                    pass

        return extracted
