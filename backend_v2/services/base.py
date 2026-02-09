from abc import ABC, abstractmethod
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright, Page, Browser
from playwright.async_api import async_playwright, Page as AsyncPage
import os
import asyncio
import datetime
from concurrent.futures import ThreadPoolExecutor

# Thread pool for running sync playwright
_executor = ThreadPoolExecutor(max_workers=2)

class BaseCrawler(ABC):
    def __init__(self, provider_name: str, headless: bool = True, user_id: int = None):
        self.provider_name = provider_name
        self.headless = headless
        self.user_id = user_id
        # CRITICAL: Use user-specific directory to prevent data mixing between users
        if user_id:
            self.download_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), f"../../data/raw/{user_id}/{provider_name}"))
        else:
            # Fallback for backwards compatibility (should not happen in production)
            self.download_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), f"../../data/raw/_unknown/{provider_name}"))
        os.makedirs(self.download_dir, exist_ok=True)
        self._status_callback = None

    def set_status_callback(self, callback):
        """Set callback for status updates. Callback signature: (stage: str, message: str)"""
        self._status_callback = callback

    def update_status(self, stage: str, message: str):
        """Update status via callback if set."""
        if self._status_callback:
            self._status_callback(stage, message)

    def log(self, msg: str):
        """Log message to console and file."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_msg = f"[{timestamp}] [{self.provider_name}] {msg}"
        print(formatted_msg)
        try:
            with open(os.path.join(self.download_dir, "crawler.log"), "a", encoding="utf-8") as f:
                f.write(formatted_msg + "\n")
        except Exception:
            pass # Fallback if file write fails

    def _run_sync(self, credentials: Dict[str, str]):
        """Synchronous execution flow - runs in thread pool."""
        self.log(f"Starting browser (headless={self.headless})")
        with sync_playwright() as p:
            # Simple browser launch - no stealth/anti-detection
            # For providers with bot detection (Regina Maria), we use visible browser mode
            browser = p.chromium.launch(
                headless=self.headless,
                channel="chrome",  # Use installed Chrome for consistency
                slow_mo=100,  # Small delay for more reliable automation
                timeout=60000,  # 60 second timeout for browser launch
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ]
            )
            context = browser.new_context(
                accept_downloads=True,
                viewport={"width": 1920, "height": 1080}
            )
            page = context.new_page()

            try:
                self.log("Starting Login...")
                self.update_status("login", "Logging in...")
                self.login_sync(page, credentials)
                self.log("Login Successful.")
                self.update_status("logged_in", "Login successful")

                self.log("Navigating to documents...")
                self.update_status("navigating", "Navigating to documents...")
                self.navigate_to_records_sync(page)

                self.log("Extracting documents...")
                self.update_status("scanning", "Scanning for documents...")

                # Get expected count from provider page before downloading
                expected_count = -1
                if hasattr(self, 'get_expected_document_count'):
                    expected_count = self.get_expected_document_count(page)

                documents = self.extract_documents_sync(page)
                downloaded_count = len(documents)
                self.log(f"Downloaded {downloaded_count} documents.")

                # Verification: compare expected vs downloaded
                if expected_count > 0:
                    if downloaded_count == expected_count:
                        self.log(f"✓ Verification PASSED: Downloaded {downloaded_count} = Expected {expected_count}")
                    elif downloaded_count < expected_count:
                        self.log(f"⚠ Verification WARNING: Downloaded {downloaded_count} < Expected {expected_count} (missing {expected_count - downloaded_count})")
                    else:
                        self.log(f"✓ Downloaded {downloaded_count} >= Expected {expected_count}")

                # Return documents with metadata
                return {
                    "documents": documents,
                    "downloaded_count": downloaded_count,
                    "expected_count": expected_count,
                    "verification_status": "ok" if expected_count <= 0 or downloaded_count >= expected_count else "warning"
                }

            except Exception as e:
                self.log(f"Error: {e}")
                # Take screenshot on error
                try:
                    page.screenshot(path=f"{self.download_dir}/error_screenshot.png")
                except:
                    pass
                raise e
            finally:
                browser.close()

    async def run(self, credentials: Dict[str, str]):
        """Main execution flow - runs sync playwright in thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._run_sync, credentials)

    @abstractmethod
    def login_sync(self, page: Page, credentials: Dict[str, str]):
        """Perform login actions (sync version)."""
        pass

    @abstractmethod
    def navigate_to_records_sync(self, page: Page):
        """Navigate from dashboard to records/medical history page (sync version)."""
        pass

    @abstractmethod
    def extract_documents_sync(self, page: Page) -> List[Dict[str, Any]]:
        """Find and download documents (sync version)."""
        pass

    def download_file(self, download_obj, filename: str):
        """Helper to save downloaded file."""
        path = os.path.join(self.download_dir, filename)
        download_obj.save_as(path)
        return path
