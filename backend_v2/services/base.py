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
            # Use real Chrome if available (harder to detect than Playwright's Chromium)
            browser = p.chromium.launch(
                headless=self.headless,
                channel="chrome",  # Use installed Chrome instead of bundled Chromium
                slow_mo=150,  # Slightly slower to seem more human
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--start-maximized",
                    "--no-sandbox",
                    "--disable-infobars",
                    "--disable-dev-shm-usage",
                    "--disable-browser-side-navigation",
                    "--disable-gpu",
                    "--lang=en-US,en",
                ]
            )
            context = browser.new_context(
                accept_downloads=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080}
            )
            page = context.new_page()

            # Comprehensive stealth scripts to avoid headless detection
            page.add_init_script("""
                // Remove webdriver property
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});

                // Mock plugins (headless has none)
                Object.defineProperty(navigator, 'plugins', {
                    get: () => {
                        const plugins = [
                            {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format', length: 1},
                            {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '', length: 1},
                            {name: 'Native Client', filename: 'internal-nacl-plugin', description: '', length: 2}
                        ];
                        plugins.length = 3;
                        return plugins;
                    }
                });

                // Mock mimeTypes
                Object.defineProperty(navigator, 'mimeTypes', {
                    get: () => {
                        const mimeTypes = [
                            {type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format'},
                            {type: 'application/x-google-chrome-pdf', suffixes: 'pdf', description: 'Portable Document Format'}
                        ];
                        mimeTypes.length = 2;
                        return mimeTypes;
                    }
                });

                // Mock languages
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en', 'ro']});

                // Mock window.chrome
                window.chrome = {
                    runtime: {id: undefined},
                    loadTimes: function() { return {}; },
                    csi: function() { return {}; },
                    app: {isInstalled: false, InstallState: {DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed'}, RunningState: {CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running'}}
                };

                // Mock permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({state: Notification.permission}) :
                        originalQuery(parameters)
                );

                // CRITICAL: Fix headless-specific window properties
                Object.defineProperty(window, 'outerWidth', {get: () => 1920});
                Object.defineProperty(window, 'outerHeight', {get: () => 1080});
                Object.defineProperty(window, 'innerWidth', {get: () => 1920});
                Object.defineProperty(window, 'innerHeight', {get: () => 1040});
                Object.defineProperty(window, 'screenX', {get: () => 0});
                Object.defineProperty(window, 'screenY', {get: () => 0});
                Object.defineProperty(screen, 'availWidth', {get: () => 1920});
                Object.defineProperty(screen, 'availHeight', {get: () => 1040});
                Object.defineProperty(screen, 'width', {get: () => 1920});
                Object.defineProperty(screen, 'height', {get: () => 1080});
                Object.defineProperty(screen, 'colorDepth', {get: () => 24});
                Object.defineProperty(screen, 'pixelDepth', {get: () => 24});

                // Mock connection API (missing in headless)
                Object.defineProperty(navigator, 'connection', {
                    get: () => ({
                        effectiveType: '4g',
                        rtt: 50,
                        downlink: 10,
                        saveData: false
                    })
                });

                // Mock battery API
                navigator.getBattery = () => Promise.resolve({
                    charging: true,
                    chargingTime: 0,
                    dischargingTime: Infinity,
                    level: 1
                });

                // Hide automation indicators
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;

                // Override toString to hide modifications
                const originalFunction = Function.prototype.toString;
                Function.prototype.toString = function() {
                    if (this === navigator.permissions.query) {
                        return 'function query() { [native code] }';
                    }
                    return originalFunction.call(this);
                };

                // WebGL fingerprint spoofing (CRITICAL for headless detection)
                const getParameterProxyHandler = {
                    apply: function(target, thisArg, args) {
                        const param = args[0];
                        const gl = thisArg;
                        // UNMASKED_VENDOR_WEBGL
                        if (param === 37445) {
                            return 'Google Inc. (NVIDIA)';
                        }
                        // UNMASKED_RENDERER_WEBGL
                        if (param === 37446) {
                            return 'ANGLE (NVIDIA, NVIDIA GeForce GTX 1080 Direct3D11 vs_5_0 ps_5_0, D3D11)';
                        }
                        return Reflect.apply(target, thisArg, args);
                    }
                };

                // Apply to both WebGL contexts
                const originalGetContext = HTMLCanvasElement.prototype.getContext;
                HTMLCanvasElement.prototype.getContext = function(type, attributes) {
                    const context = originalGetContext.call(this, type, attributes);
                    if (context && (type === 'webgl' || type === 'webgl2' || type === 'experimental-webgl')) {
                        context.getParameter = new Proxy(context.getParameter, getParameterProxyHandler);
                    }
                    return context;
                };

                // Hardware info (headless often has wrong values)
                Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
                Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
                Object.defineProperty(navigator, 'maxTouchPoints', {get: () => 0});

                // Platform and vendor
                Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
                Object.defineProperty(navigator, 'vendor', {get: () => 'Google Inc.'});
                Object.defineProperty(navigator, 'product', {get: () => 'Gecko'});
                Object.defineProperty(navigator, 'productSub', {get: () => '20030107'});

                // Notification API
                if (!window.Notification) {
                    window.Notification = {
                        permission: 'default',
                        requestPermission: () => Promise.resolve('default')
                    };
                }

                // Media devices (headless has none)
                if (navigator.mediaDevices) {
                    navigator.mediaDevices.enumerateDevices = () => Promise.resolve([
                        {deviceId: 'default', kind: 'audioinput', label: '', groupId: 'default'},
                        {deviceId: 'default', kind: 'audiooutput', label: '', groupId: 'default'},
                        {deviceId: 'default', kind: 'videoinput', label: '', groupId: 'default'}
                    ]);
                }

                // Keyboard API
                if (navigator.keyboard) {
                    navigator.keyboard.getLayoutMap = () => Promise.resolve(new Map());
                }

                // Clipboard API behavior
                if (navigator.clipboard) {
                    const originalRead = navigator.clipboard.read;
                    navigator.clipboard.read = function() {
                        return Promise.reject(new DOMException('Document is not focused.'));
                    };
                }

                // Document visibility (headless is always hidden)
                Object.defineProperty(document, 'visibilityState', {get: () => 'visible'});
                Object.defineProperty(document, 'hidden', {get: () => false});

                // Focus detection
                Object.defineProperty(document, 'hasFocus', {value: () => true});

                // Iframe contentWindow detection
                const originalContentWindow = Object.getOwnPropertyDescriptor(HTMLIFrameElement.prototype, 'contentWindow');
                Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
                    get: function() {
                        const win = originalContentWindow.get.call(this);
                        if (win) {
                            try {
                                win.chrome = window.chrome;
                            } catch(e) {}
                        }
                        return win;
                    }
                });

                // Performance API (headless leaks timing info)
                const originalNow = Performance.prototype.now;
                Performance.prototype.now = function() {
                    return originalNow.call(this) + (Math.random() * 0.1);
                };

                // Block known headless detection scripts
                const originalFetch = window.fetch;
                window.fetch = function(...args) {
                    const url = args[0]?.url || args[0];
                    if (typeof url === 'string' && url.includes('detectHeadless')) {
                        return Promise.resolve(new Response('{}'));
                    }
                    return originalFetch.apply(this, args);
                };
            """)

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
