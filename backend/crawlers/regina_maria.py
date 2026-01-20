import os
import asyncio
import datetime
from typing import Dict, Any, List
from playwright.async_api import Page
from .base import BaseCrawler

class ReginaMariaCrawler(BaseCrawler):
    def __init__(self, headless: bool = True):
        super().__init__("regina_maria", headless)
        self.login_url = "https://contulmeu.reginamaria.ro/#/login"
        self.dashboard_url = "https://contulmeu.reginamaria.ro/#/Pacient/Dashboard"

    async def login(self, page: Page, credentials: Dict[str, str]):
        self.log("Navigating to login page...")
        await page.goto(self.login_url)
        
        try:
            # Handle Cookie Consent
            # Wait a moment for it to appear
            await page.wait_for_timeout(2000)
            accept_button = page.get_by_text("Accept toate cookie-urile")
            if await accept_button.count() > 0:
                 await accept_button.click()
                 self.log("Clicked cookie accept.")
        except Exception as e:
            self.log(f"Cookie handling warning: {e}")

        self.log("Filling credentials...")
        # Strict clearing logic to prevent autocomplete duplication
        # Username
        await page.click("#input-username")
        await page.wait_for_timeout(500)
        await page.keyboard.press("Control+A")
        await page.keyboard.press("Backspace")
        await page.wait_for_timeout(500)
        await page.type("#input-username", credentials["username"], delay=100)
        
        # Password
        await page.click("#input-password")
        await page.wait_for_timeout(500)
        await page.keyboard.press("Control+A")
        await page.keyboard.press("Backspace")
        await page.wait_for_timeout(500)
        await page.type("#input-password", credentials["password"], delay=100)
        
        # Debug screenshot to see what was typed
        await page.screenshot(path=f"{self.download_dir}/pre_login_filled.png")
        self.log(f"Captured pre-login screenshot to {self.download_dir}/pre_login_filled.png")
        
        self.log("Clicking login...")
        # Use more specific selector
        try:
            async with page.expect_navigation(timeout=15000):
                # Try specific button text
                # Try fallback selector
                try:
                    await page.click("button.k-button-solid-primary", timeout=3000)
                except:
                    await page.get_by_text("Intra in cont").click()
        except Exception as e:
            self.log(f"Navigation timeout or click failed: {e}")
            
        self.log("Checking login status...")
        
        # Check for reCAPTCHA/Error/Success loop
        for i in range(24): # Wait up to 2 minutes (24 * 5s)
            current_url = page.url
            content = await page.content()
            
            # 1. Success
            if "dashboard" in current_url.lower() or "acasa" in current_url.lower():
                self.log("Login Successful (Dashboard detected).")
                return

            # 2. ReCAPTCHA Detection
            # Look for the iframe or specific text
            if "recaptcha" in content.lower():
                self.log("reCAPTCHA detected!")
                try:
                    # Try to find and click the checkbox if visible
                    # Note: often inside an iframe
                    frame = page.frame_locator("iframe[src*='recaptcha']").first
                    if await frame.locator(".recaptcha-checkbox-border").is_visible():
                        self.log("Attempting to click reCAPTCHA checkbox...")
                        await frame.locator(".recaptcha-checkbox-border").click()
                    else:
                         self.log("reCAPTCHA present but checkbox may be hidden or in different frame. Please SOLVE MANUALLY.")
                except Exception as e:
                    self.log(f"Auto-click reCAPTCHA failed: {e}. Please SOLVE MANUALLY.")
                
                # We do not raise exception yet, we allow the loop to continue so user can solve it
            
            # 3. Error Message
            if "Date de autentificare incorecte" in content or "Incercare de autentificare nereusita" in content:
                raise Exception("Invalid credentials detected on page.")
                
            # 4. 404 Recovery
            if "404" in current_url:
                 self.log("Detected 404 Page. Attempting to recover to Dashboard...")
                 try:
                     await page.goto(self.dashboard_url)
                     await page.wait_for_load_state("domcontentloaded")
                 except:
                     pass # connection error or whatever, loop will catch up
            
            self.log(f"Waiting for login... (Attempt {i+1}/24) URL: {current_url}")
            await page.wait_for_timeout(5000)
            
        # Final check
        if "dashboard" in page.url.lower():
             self.log("Login seemingly successful.")
        else:
             self.log(f"Stuck on URL: {page.url}")
             await page.screenshot(path=f"{self.download_dir}/login_stuck.png")
             raise Exception(f"Login failed - Timed out waiting for Dashboard. Stuck at {page.url}")

    def log(self, msg):
        with open(f"{self.download_dir}/crawler.log", "a") as f:
            f.write(msg + "\n")
        print(f"[{self.provider_name}] {msg}")

    async def navigate_to_records(self, page: Page):
        target_url = "https://contulmeu.reginamaria.ro/#/Pacient/Analize"
        self.log(f"Navigating directly to {target_url}...")
        
        # Use domcontentloaded instead of networkidle which can hang on tracking scripts
        await page.goto(target_url, wait_until="domcontentloaded")
        
        # Fixed wait to allow SPA to render
        self.log("Waiting for SPA to render...")
        await page.wait_for_timeout(8000) 
        self.log("Navigated to records list (timeout complete).")

    async def extract_documents(self, page: Page) -> List[Dict[str, Any]]:
        extracted = []
        self.log("Scanning for documents...")
        
        # Take a look at what we have
        await page.screenshot(path=f"{self.download_dir}/analize_page_load_top.png")

        # Scroll to bottom to trigger any lazy loading
        self.log("Scrolling to bottom to trigger lazy loading...")
        for _ in range(3):
            await page.mouse.wheel(0, 4000)
            await page.wait_for_timeout(2000)
        
        await page.screenshot(path=f"{self.download_dir}/analize_page_load_bottom.png")
        
        try:
             # Wait longer, and try finding ANY button to confirm we are not on a blank page
             await page.wait_for_selector("button", timeout=15000)
             self.log("Buttons detected on page.")
        except:
             self.log("No buttons detected after wait.")

        # Find all download buttons
        # User mentioned "Descarca Analize", subagent saw "Descarca buletin". using "Descarca" covers both.
        # We search for any button containing "Descarca"
        download_btns = await page.locator("button:has-text('Descarca')").all()
        
        self.log(f"Found {len(download_btns)} potential documents.")
        
        if len(download_btns) == 0:
             # Fallback debug: print all buttons
             self.log("DEBUG: No download buttons found. Listing all buttons:")
             all_btns = await page.locator("button").all()
             for b in all_btns[:10]:
                  txt = await b.text_content()
                  self.log(f" - {txt.strip()}")
        
        # Iterate over all found buttons
        for i, btn in enumerate(download_btns):
            try:
                self.log(f"Processing document {i+1}/{len(download_btns)}...")
                
                # Scroll carefully to the button
                await btn.scroll_into_view_if_needed()
                
                if not await btn.is_visible():
                    self.log(f"Button {i} not visible, skipping.")
                    continue

                # Trigger download
                # Increase timeout for generating PDF
                async with page.expect_download(timeout=120000) as download_info:
                    await btn.click()
                    
                download = await download_info.value
                filename = download.suggested_filename
                
                # Verify filename is not empty
                if not filename:
                    filename = f"document_{i}_{datetime.datetime.now().timestamp()}.pdf"

                # Force save to our data dir
                target_path = os.path.join(self.download_dir, filename)
                
                # Remove if exists to ensure overwrite
                if os.path.exists(target_path):
                    os.remove(target_path)
                    
                await download.save_as(target_path)
                
                self.log(f"Downloaded: {filename}")
                
                extracted.append({
                    "filename": filename,
                    "local_path": target_path,
                    "date": datetime.datetime.now(), 
                    "category": "Analize"
                })
                
                # Delay to prevent rate limiting or browser stutter
                await page.wait_for_timeout(3000)
                
            except Exception as e:
                self.log(f"Failed to download document {i}: {e}")
                # Continue to next document even if one fails
                continue
                
        return extracted
