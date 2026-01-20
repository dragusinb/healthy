import os
import datetime
import requests
from typing import Dict, Any, List
from playwright.sync_api import Page
from backend_v2.services.base import BaseCrawler


class SynevoCrawler(BaseCrawler):
    def __init__(self, headless: bool = False):
        super().__init__("synevo", headless)
        self.login_url = "https://webresults.synevo.ro/Account/Login?defaultusertype=2"
        self.dashboard_url = "https://webresults.synevo.ro/ro-RO"

    def login_sync(self, page: Page, credentials: Dict[str, str]):
        self.log("Navigating to login page...")
        page.goto(self.login_url)

        try:
            # Handle Cookie Consent if it appears
            page.wait_for_timeout(2000)
            for text in ["Accept", "Accept toate", "De acord", "I agree"]:
                btn = page.get_by_text(text, exact=True)
                if btn.count() > 0:
                    btn.first.click()
                    self.log(f"Clicked cookie accept: {text}")
                    break
        except Exception as e:
            self.log(f"Cookie handling warning: {e}")

        self.log("Filling credentials...")

        # 1. Terms and Policy Checkboxes
        try:
            checkboxes = page.locator("input[type='checkbox']").all()
            if len(checkboxes) >= 2:
                for i in range(2):
                    if not checkboxes[i].is_checked():
                        checkboxes[i].click()
                self.log("Clicked first two checkboxes (Termeni/Politica).")
            else:
                self.log("Less than 2 checkboxes found.")
        except Exception as e:
            self.log(f"Checkbox click failed: {e}")

        # 2. CNP Input
        try:
            text_inputs = page.locator("input[type='text']").all()
            visible_inputs = [i for i in text_inputs if i.is_visible()]

            if len(visible_inputs) > 0:
                visible_inputs[0].click()
                visible_inputs[0].fill(credentials["username"])
                self.log("Filled first visible text input with CNP.")
            else:
                self.log("No visible text inputs found for CNP.")

        except Exception as e:
            self.log(f"CNP fill failed: {e}")

        # 3. Password Input
        try:
            page.click("input[type='password']")
            page.fill("input[type='password']", credentials["password"])
        except Exception as e:
            self.log(f"Password fill failed: {e}")

        # Try Enter key to submit
        self.log("Pressing Enter to login...")
        page.keyboard.press("Enter")
        page.wait_for_timeout(2000)

        self.log("Clicking login (fallback)...")
        try:
            page.locator("button.btnAuth").click(timeout=3000)
        except:
            pass

        try:
            page.get_by_role("button", name="Autentificare").click(timeout=3000)
        except:
            pass

        self.log("Checking login status...")
        try:
            page.wait_for_url(lambda u: "Account/Login" not in u, timeout=20000)
            self.log("Login URL changed, assuming success.")
        except:
            self.log("URL did not change, might be stuck or SPA.")

        # Final check
        page.wait_for_timeout(5000)
        current_url = page.url
        if "webresults" in current_url and "Login" not in current_url:
            self.log("Login Successful (Dashboard detected).")
        else:
            self.log(f"Login outcome uncertain. URL: {current_url}")
            page.screenshot(path=f"{self.download_dir}/login_outcome.png")

    def navigate_to_records_sync(self, page: Page):
        self.log("Verifying we are on the dashboard/records page...")
        try:
            page.wait_for_selector("a[href*='/Orders/ResultsPDF/']", timeout=10000)
            self.log("Records detected (Download buttons visible).")
        except:
            self.log("Download buttons not immediately visible. Attempting to ensure we are on the results page...")
            if "webresults" not in page.url:
                self.log("Not on webresults, navigating manually...")
                page.goto(self.dashboard_url)
            page.wait_for_timeout(3000)

    def extract_documents_sync(self, page: Page) -> List[Dict[str, Any]]:
        extracted = []
        self.log("Scanning for documents...")

        page.wait_for_timeout(5000)  # Wait for list to load

        # Selector identified: a[href*='/Orders/ResultsPDF/']
        pdf_links = page.locator("a[href*='/Orders/ResultsPDF/']").all()

        self.log(f"Found {len(pdf_links)} potential PDF links.")

        if len(pdf_links) == 0:
            self.log("No PDF links found. Dumping DOM for debug.")
            page.screenshot(path=f"{self.download_dir}/no_pdfs_found.png")
            return extracted

        # Get all href values first to avoid stale element issues
        pdf_urls = []
        for link in pdf_links:
            href = link.get_attribute("href")
            if href:
                if href.startswith("/"):
                    href = f"https://webresults.synevo.ro{href}"
                pdf_urls.append(href)

        self.log(f"Collected {len(pdf_urls)} PDF URLs.")

        # Get cookies from the browser context for authenticated requests
        cookies = page.context.cookies()
        cookie_header = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

        for i, pdf_url in enumerate(pdf_urls):
            try:
                self.log(f"Processing document {i+1}/{len(pdf_urls)}...")

                # Extract filename from URL
                url_parts = pdf_url.rstrip("/").split("/")
                doc_id = url_parts[-1] if url_parts else f"doc_{i}"
                filename = f"{doc_id}.pdf"
                target_path = os.path.join(self.download_dir, filename)

                download_success = False

                # Try Method 1: expect_download
                try:
                    with page.expect_download(timeout=10000) as download_info:
                        page.goto(pdf_url)
                    download = download_info.value
                    if os.path.exists(target_path):
                        os.remove(target_path)
                    download.save_as(target_path)
                    download_success = True
                    self.log(f"Downloaded via browser: {filename}")
                except Exception as e1:
                    self.log(f"Browser download failed, trying direct fetch: {e1}")

                # Try Method 2: Direct HTTP request with session cookies
                if not download_success:
                    try:
                        headers = {
                            "Cookie": cookie_header,
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                        }
                        response = requests.get(pdf_url, headers=headers, timeout=60)
                        if response.status_code == 200:
                            if os.path.exists(target_path):
                                os.remove(target_path)
                            with open(target_path, "wb") as f:
                                f.write(response.content)
                            download_success = True
                            self.log(f"Downloaded via HTTP: {filename}")
                        else:
                            self.log(f"HTTP request failed with status {response.status_code}")
                    except Exception as e2:
                        self.log(f"Direct HTTP download failed: {e2}")

                # Try Method 3: Open in new tab and capture response
                if not download_success:
                    try:
                        new_page = page.context.new_page()
                        response = new_page.goto(pdf_url, wait_until="networkidle")
                        if response and response.ok:
                            content_type = response.headers.get("content-type", "")
                            if "pdf" in content_type.lower() or "octet-stream" in content_type.lower():
                                body = response.body()
                                if os.path.exists(target_path):
                                    os.remove(target_path)
                                with open(target_path, "wb") as f:
                                    f.write(body)
                                download_success = True
                                self.log(f"Downloaded via new tab: {filename}")
                        new_page.close()
                    except Exception as e3:
                        self.log(f"New tab download failed: {e3}")

                if download_success and os.path.exists(target_path):
                    extracted.append({
                        "filename": filename,
                        "local_path": target_path,
                        "date": datetime.datetime.now(),
                        "category": "Analize Synevo"
                    })
                else:
                    self.log(f"All download methods failed for document {i}")

                # Navigate back to the main page for next iteration
                if page.url != self.dashboard_url:
                    page.goto(self.dashboard_url)
                    page.wait_for_timeout(2000)

            except Exception as e:
                self.log(f"Failed to download document {i}: {e}")
                continue

        return extracted
