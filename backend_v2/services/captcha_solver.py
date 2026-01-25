"""
CAPTCHA Solver Service using 2captcha and anti-captcha APIs.
"""
import os
import time
import logging

logger = logging.getLogger(__name__)

# API Keys (from environment or hardcoded fallback)
TWOCAPTCHA_API_KEY = os.environ.get('TWOCAPTCHA_API_KEY', '1eeed9b49a149c676bb39825c9ecf904')
ANTICAPTCHA_API_KEY = os.environ.get('ANTICAPTCHA_API_KEY', '125b983f44ec1e87662ab3c3b9b49cd3')

# Preferred service order
PREFERRED_SERVICE = os.environ.get('CAPTCHA_SERVICE', '2captcha')  # '2captcha' or 'anticaptcha'


class CaptchaSolver:
    """Solves reCAPTCHA v2 using external services."""

    def __init__(self, service: str = None):
        self.service = service or PREFERRED_SERVICE
        self._2captcha_solver = None
        self._anticaptcha = None

    def _init_2captcha(self):
        """Initialize 2captcha solver."""
        if self._2captcha_solver is None:
            try:
                from twocaptcha import TwoCaptcha
                self._2captcha_solver = TwoCaptcha(TWOCAPTCHA_API_KEY)
                logger.info("2captcha solver initialized")
            except ImportError:
                logger.error("2captcha-python not installed")
                raise
        return self._2captcha_solver

    def _init_anticaptcha(self):
        """Initialize anti-captcha solver."""
        if self._anticaptcha is None:
            try:
                from anticaptchaofficial.recaptchav2proxyless import recaptchaV2Proxyless
                self._anticaptcha = recaptchaV2Proxyless()
                self._anticaptcha.set_verbose(0)  # Disable verbose output
                self._anticaptcha.set_key(ANTICAPTCHA_API_KEY)
                logger.info("anti-captcha solver initialized")
            except ImportError:
                logger.error("anticaptchaofficial not installed")
                raise
        return self._anticaptcha

    def get_balance(self) -> float:
        """Get account balance from the captcha service."""
        try:
            if self.service == '2captcha':
                solver = self._init_2captcha()
                balance = solver.balance()
                return float(balance)
            else:
                solver = self._init_anticaptcha()
                balance = solver.get_balance()
                return float(balance) if balance else 0.0
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return 0.0

    def solve_recaptcha_v2(self, site_url: str, site_key: str, invisible: bool = False) -> str:
        """
        Solve reCAPTCHA v2 and return the token.

        Args:
            site_url: The URL of the page with the CAPTCHA
            site_key: The reCAPTCHA site key (data-sitekey attribute)
            invisible: Whether this is an invisible reCAPTCHA

        Returns:
            The solved CAPTCHA token (g-recaptcha-response)
        """
        logger.info(f"Solving reCAPTCHA v2 for {site_url} using {self.service}")
        logger.info(f"Site key: {site_key[:20]}...")

        start_time = time.time()

        try:
            if self.service == '2captcha':
                token = self._solve_with_2captcha(site_url, site_key, invisible)
            else:
                token = self._solve_with_anticaptcha(site_url, site_key, invisible)

            elapsed = time.time() - start_time
            logger.info(f"CAPTCHA solved in {elapsed:.1f}s")
            return token

        except Exception as e:
            logger.error(f"CAPTCHA solving failed with {self.service}: {e}")

            # Try fallback service
            fallback = 'anticaptcha' if self.service == '2captcha' else '2captcha'
            logger.info(f"Trying fallback service: {fallback}")

            try:
                if fallback == '2captcha':
                    token = self._solve_with_2captcha(site_url, site_key, invisible)
                else:
                    token = self._solve_with_anticaptcha(site_url, site_key, invisible)

                elapsed = time.time() - start_time
                logger.info(f"CAPTCHA solved with fallback in {elapsed:.1f}s")
                return token
            except Exception as e2:
                logger.error(f"Fallback also failed: {e2}")
                raise Exception(f"All CAPTCHA services failed: {e}, {e2}")

    def _solve_with_2captcha(self, site_url: str, site_key: str, invisible: bool) -> str:
        """Solve using 2captcha service."""
        solver = self._init_2captcha()

        # Check balance first
        balance = solver.balance()
        logger.info(f"2captcha balance: ${balance}")
        if float(balance) < 0.01:
            raise Exception("2captcha balance too low")

        result = solver.recaptcha(
            sitekey=site_key,
            url=site_url,
            invisible=1 if invisible else 0
        )

        return result['code']

    def _solve_with_anticaptcha(self, site_url: str, site_key: str, invisible: bool) -> str:
        """Solve using anti-captcha service."""
        if invisible:
            from anticaptchaofficial.recaptchav2proxyless import recaptchaV2Proxyless
            solver = recaptchaV2Proxyless()
        else:
            from anticaptchaofficial.recaptchav2proxyless import recaptchaV2Proxyless
            solver = recaptchaV2Proxyless()

        solver.set_verbose(0)
        solver.set_key(ANTICAPTCHA_API_KEY)
        solver.set_website_url(site_url)
        solver.set_website_key(site_key)

        if invisible:
            solver.set_is_invisible(True)

        token = solver.solve_and_return_solution()

        if token == 0:
            error = solver.error_code
            raise Exception(f"anti-captcha failed: {error}")

        return token


def extract_recaptcha_sitekey(page) -> str:
    """
    Extract the reCAPTCHA site key from a Playwright page.

    Args:
        page: Playwright page object

    Returns:
        The site key string or None if not found
    """
    try:
        # Method 1: Look for data-sitekey attribute
        sitekey = page.evaluate("""
            () => {
                // Check for reCAPTCHA div
                const recaptchaDiv = document.querySelector('.g-recaptcha');
                if (recaptchaDiv && recaptchaDiv.getAttribute('data-sitekey')) {
                    return recaptchaDiv.getAttribute('data-sitekey');
                }

                // Check for iframe src
                const iframe = document.querySelector('iframe[src*="recaptcha"]');
                if (iframe) {
                    const src = iframe.src;
                    const match = src.match(/[?&]k=([^&]+)/);
                    if (match) return match[1];
                }

                // Check for script src
                const scripts = document.querySelectorAll('script[src*="recaptcha"]');
                for (const script of scripts) {
                    const match = script.src.match(/[?&]render=([^&]+)/);
                    if (match && match[1] !== 'explicit') return match[1];
                }

                // Check grecaptcha object
                if (window.grecaptcha && window.grecaptcha.enterprise) {
                    // Enterprise reCAPTCHA - harder to extract
                    return null;
                }

                return null;
            }
        """)

        if sitekey:
            logger.info(f"Found reCAPTCHA site key: {sitekey[:20]}...")
            return sitekey

        # Method 2: Search page content for site key pattern
        content = page.content()
        import re
        patterns = [
            r'data-sitekey="([^"]+)"',
            r"data-sitekey='([^']+)'",
            r'sitekey["\s:]+["\']([0-9A-Za-z_-]{40})["\']',
            r'render=([0-9A-Za-z_-]{40})',
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                sitekey = match.group(1)
                logger.info(f"Found reCAPTCHA site key via regex: {sitekey[:20]}...")
                return sitekey

        logger.warning("Could not find reCAPTCHA site key")
        return None

    except Exception as e:
        logger.error(f"Error extracting site key: {e}")
        return None


def inject_captcha_token(page, token: str) -> bool:
    """
    Inject the solved CAPTCHA token into the page.

    Args:
        page: Playwright page object
        token: The solved CAPTCHA token

    Returns:
        True if injection was successful
    """
    try:
        result = page.evaluate("""
            (token) => {
                let success = false;

                // 1. Find all reCAPTCHA textareas and set value
                const textareas = document.querySelectorAll('#g-recaptcha-response, [name="g-recaptcha-response"], textarea[id*="g-recaptcha-response"]');
                textareas.forEach(textarea => {
                    textarea.value = token;
                    textarea.innerHTML = token;
                    textarea.style.display = 'block';

                    // Dispatch events to notify frameworks
                    textarea.dispatchEvent(new Event('input', { bubbles: true }));
                    textarea.dispatchEvent(new Event('change', { bubbles: true }));
                    success = true;
                });

                // 2. Set in any hidden inputs
                const hiddenInputs = document.querySelectorAll('input[name="g-recaptcha-response"]');
                hiddenInputs.forEach(input => {
                    input.value = token;
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                });

                // 3. Try to find and call the callback
                const recaptchaDiv = document.querySelector('.g-recaptcha');
                if (recaptchaDiv) {
                    const callbackName = recaptchaDiv.getAttribute('data-callback');
                    if (callbackName) {
                        // Try different scopes for the callback
                        let callback = null;

                        // Try window scope
                        if (typeof window[callbackName] === 'function') {
                            callback = window[callbackName];
                        }
                        // Try nested paths (e.g., "app.recaptchaCallback")
                        else if (callbackName.includes('.')) {
                            let obj = window;
                            const parts = callbackName.split('.');
                            for (const part of parts) {
                                if (obj && obj[part]) {
                                    obj = obj[part];
                                } else {
                                    obj = null;
                                    break;
                                }
                            }
                            if (typeof obj === 'function') {
                                callback = obj;
                            }
                        }

                        if (callback) {
                            console.log('Calling reCAPTCHA callback:', callbackName);
                            try {
                                callback(token);
                                success = true;
                            } catch (e) {
                                console.error('Callback error:', e);
                            }
                        }
                    }
                }

                // 4. Try to trigger grecaptcha callback if available
                if (window.grecaptcha) {
                    try {
                        // Some sites use enterprise version
                        if (window.grecaptcha.enterprise && window.grecaptcha.enterprise.execute) {
                            console.log('Enterprise reCAPTCHA detected');
                        }

                        // Try to find the widget and trigger callback
                        const widgets = document.querySelectorAll('[data-widget-id]');
                        widgets.forEach(widget => {
                            const widgetId = widget.getAttribute('data-widget-id');
                            if (widgetId && window.grecaptcha.getResponse) {
                                // Override getResponse to return our token
                                const originalGetResponse = window.grecaptcha.getResponse;
                                window.grecaptcha.getResponse = function(id) {
                                    if (id === parseInt(widgetId) || id === undefined) {
                                        return token;
                                    }
                                    return originalGetResponse.call(this, id);
                                };
                            }
                        });
                    } catch (e) {
                        console.error('grecaptcha manipulation error:', e);
                    }
                }

                // 5. Look for Angular/React specific patterns
                try {
                    // Angular apps often use ng-model or formControl
                    const angularInputs = document.querySelectorAll('[ng-model*="captcha"], [formcontrolname*="captcha"]');
                    angularInputs.forEach(input => {
                        input.value = token;
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                    });
                } catch (e) {}

                // 6. Try to trigger any onsubmit handlers that might check CAPTCHA
                const forms = document.querySelectorAll('form');
                forms.forEach(form => {
                    // Create/update hidden input with token
                    let tokenInput = form.querySelector('input[name="g-recaptcha-response"]');
                    if (!tokenInput) {
                        tokenInput = document.createElement('input');
                        tokenInput.type = 'hidden';
                        tokenInput.name = 'g-recaptcha-response';
                        form.appendChild(tokenInput);
                    }
                    tokenInput.value = token;
                });

                return success || textareas.length > 0;
            }
        """, token)

        logger.info(f"CAPTCHA token injected: {result}")
        return result

    except Exception as e:
        logger.error(f"Error injecting CAPTCHA token: {e}")
        return False
