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
    def __init__(self, provider_name: str, headless: bool = True):
        self.provider_name = provider_name
        self.headless = headless
        self.download_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), f"../../data/raw/{provider_name}"))
        os.makedirs(self.download_dir, exist_ok=True)

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
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                slow_mo=100,
                args=["--disable-blink-features=AutomationControlled", "--start-maximized"]
            )
            context = browser.new_context(
                accept_downloads=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080}
            )
            page = context.new_page()

            # Stealth: Remove webdriver property
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            try:
                self.log("Starting Login...")
                self.login_sync(page, credentials)
                self.log("Login Successful.")

                self.log("Navigating to documents...")
                self.navigate_to_records_sync(page)

                self.log("Extracting documents...")
                documents = self.extract_documents_sync(page)
                self.log(f"Found {len(documents)} documents.")
                return documents

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
