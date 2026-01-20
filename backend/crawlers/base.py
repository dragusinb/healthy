from abc import ABC, abstractmethod
from typing import List, Dict, Any
from playwright.async_api import async_playwright, Page, Browser
import os
import asyncio
import datetime

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

    async def run(self, credentials: Dict[str, str]):
        """Main execution flow."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(accept_downloads=True)
            page = await context.new_page()
            
            try:
                self.log("Starting Login...")
                await self.login(page, credentials)
                self.log("Login Successful.")
                
                self.log("Navigating to documents...")
                await self.navigate_to_records(page)
                
                self.log("Extracting documents...")
                documents = await self.extract_documents(page)
                self.log(f"Found {len(documents)} documents.")
                return documents
                
            except Exception as e:
                self.log(f"Error: {e}")
                # Take screenshot on error
                await page.screenshot(path=f"{self.download_dir}/error_screenshot.png")
                raise e
            finally:
                await browser.close()

    @abstractmethod
    async def login(self, page: Page, credentials: Dict[str, str]):
        """Perform login actions."""
        pass

    @abstractmethod
    async def navigate_to_records(self, page: Page):
        """Navigate from dashboard to records/medical history page."""
        pass

    @abstractmethod
    async def extract_documents(self, page: Page) -> List[Dict[str, Any]]:
        """Find and download documents."""
        pass

    async def download_file(self, download_obj, filename: str):
        """Helper to save downloaded file."""
        path = os.path.join(self.download_dir, filename)
        await download_obj.save_as(path)
        return path
