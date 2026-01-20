import os
import asyncio
import datetime
from typing import Dict, Any, List
from playwright.async_api import Page
from .base import BaseCrawler

class SynevoCrawler(BaseCrawler):
    def __init__(self, headless: bool = True):
        super().__init__("synevo", headless)
        self.login_url = "https://webresults.synevo.ro/Account/Login?defaultusertype=2"
        self.dashboard_url = "https://webresults.synevo.ro/ro-RO"

    async def login(self, page: Page, credentials: Dict[str, str]):
        self.log("Navigating to login page...")
        await page.goto(self.login_url)
        
        try:
            # Handle Cookie Consent if it appears (generic check)
            await page.wait_for_timeout(2000)
            accept_button = page.get_by_text("Accept")
            if await accept_button.count() > 0:
                 await accept_button.click()
                 self.log("Clicked cookie accept (if present).")
        except Exception as e:
            self.log(f"Cookie handling warning: {e}")

        self.log("Filling credentials...")
        
        # 1. Terms and Policy Checkboxes
        # Use more generic approach that worked for subagent or try specifically by id/class if known.
        # Error log didn't complain about these, but "Could not click ... by label" logic printed.
        # Let's use the first two checkboxes found.
        try:
            checkboxes = await page.locator("input[type='checkbox']").all()
            if len(checkboxes) >= 2:
                for i in range(2):
                    if not await checkboxes[i].is_checked():
                        await checkboxes[i].click()
                self.log("Clicked first two checkboxes (Termeni/Politica).")
            else:
                self.log("Less than 2 checkboxes found.")
        except Exception as e:
            self.log(f"Checkbox click failed: {e}")

        # 2. CNP Input
        # Subagent used index 2. Log showed "UserName" name failed.
        # Let's try finding by type 'text' and visibility or index.
        try:
             # Try generic text inputs
             text_inputs = await page.locator("input[type='text']").all()
             # usually index 0 is search or hidden, index 1 might be CNP? 
             # Subagent said index 2 overall.
             # Let's try to map them.
             
             # Targeted approach: Look for input near text "CNP" or "Codul Numeric Personal"
             # or just use the one that is visible and enabled.
             visible_inputs = [i for i in text_inputs if await i.is_visible()]
             
             if len(visible_inputs) > 0:
                 # Assume the first visible text input is CNP (common pattern)
                 await visible_inputs[0].click()
                 await visible_inputs[0].fill(credentials["username"])
                 self.log("Filled first visible text input with CNP.")
             else:
                 self.log("No visible text inputs found for CNP.")
                 
        except Exception as e:
             self.log(f"CNP fill failed: {e}")

        # 3. Password Input
        try:
            await page.click("input[type='password']")
            await page.fill("input[type='password']", credentials["password"])
        except Exception as e:
            self.log(f"Password fill failed: {e}")

        self.log("Clicking login...")
        # Fix for strict mode violation: found div, button, input.
        # Log said: <button ... class="d_button_contact_login btnAuth">
        try:
            await page.locator("button.btnAuth").click()
        except:
            # Fallback
            await page.get_by_role("button", name="Autentificare").click()
        
        self.log("Checking login status...")
        try:
            await page.wait_for_url(lambda u: "Account/Login" not in u, timeout=20000)
            self.log("Login URL changed, assuming success.")
        except:
            self.log("URL did not change, might be stuck or SPA.")

        # Final check
        await page.wait_for_timeout(5000)
        current_url = page.url
        if "webresults" in current_url and "Login" not in current_url:
             self.log("Login Successful (Dashboard detected).")
        else:
             self.log(f"Login outcome uncertain. URL: {current_url}")
             await page.screenshot(path=f"{self.download_dir}/login_outcome.png")

    async def navigate_to_records(self, page: Page):
        self.log("Verifying we are on the dashboard/records page...")
        # Synevo redirects to the records page automatically after login.
        # We'll just wait for the PDF buttons to ensure page is loaded.
        try:
             await page.wait_for_selector("a[href*='/Orders/ResultsPDF/']", timeout=10000)
             self.log("Records detected (Download buttons visible).")
        except:
             self.log("Download buttons not immediately visible. Attempting to ensure we are on the results page...")
             if "webresults" not in page.url:
                  self.log("Not on webresults, navigating manually...")
                  await page.goto(self.dashboard_url)
             await page.wait_for_timeout(3000)

    async def extract_documents(self, page: Page) -> List[Dict[str, Any]]:
        extracted = []
        self.log("Scanning for documents...")
        
        await page.wait_for_timeout(5000) # Wait for list to load
        
        # Selector identified by subagent: a[href*='/Orders/ResultsPDF/']
        pdf_links = await page.locator("a[href*='/Orders/ResultsPDF/']").all()
        
        self.log(f"Found {len(pdf_links)} potential PDF links.")
        
        if len(pdf_links) == 0:
            self.log("No PDF links found. Dumping DOM for debug.")
            await page.screenshot(path=f"{self.download_dir}/no_pdfs_found.png")
            return extracted

        for i, link in enumerate(pdf_links):
            try:
                self.log(f"Processing document {i+1}/{len(pdf_links)}...")
                
                if not await link.is_visible():
                     await link.scroll_into_view_if_needed()
                
                # Download
                async with page.expect_download(timeout=60000) as download_info:
                    await link.click()
                
                download = await download_info.value
                filename = download.suggested_filename
                if not filename:
                    filename = f"synevo_doc_{i}_{datetime.datetime.now().timestamp()}.pdf"
                
                target_path = os.path.join(self.download_dir, filename)
                
                if os.path.exists(target_path):
                    os.remove(target_path)
                    
                await download.save_as(target_path)
                self.log(f"Downloaded: {filename}")
                
                extracted.append({
                    "filename": filename,
                    "local_path": target_path,
                    "date": datetime.datetime.now(),
                    "category": "Analize Synevo"
                })
                
                await page.wait_for_timeout(2000)
                
            except Exception as e:
                self.log(f"Failed to download document {i}: {e}")
                continue
                
        return extracted
