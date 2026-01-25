import asyncio
import traceback

try:
    from backend_v2.services.regina_maria_crawler import ReginaMariaCrawler, CaptchaRequiredError
    from backend_v2.services.synevo_crawler import SynevoCrawler
    from backend_v2.services import sync_status
except ImportError:
    from services.regina_maria_crawler import ReginaMariaCrawler, CaptchaRequiredError
    from services.synevo_crawler import SynevoCrawler
    from services import sync_status

async def run_regina_async(username, password, headless=True, user_id=None):
    """
    Run Regina Maria crawler with status updates.
    Auto-retries with visible browser if CAPTCHA is detected.

    Args:
        username: Regina Maria account username
        password: Regina Maria account password
        headless: If True (default), browser window will be hidden
        user_id: User ID for status tracking and file isolation (required for production)
    """
    provider = "Regina Maria"
    crawler = ReginaMariaCrawler(headless=headless, user_id=user_id)

    # Set up status callback
    if user_id:
        crawler.set_status_callback(lambda stage, msg: _update_status(user_id, provider, stage, msg))

    try:
        docs = await crawler.run({"username": username, "password": password})
        return {"status": "success", "message": f"Crawled {len(docs)} documents", "documents": docs}
    except CaptchaRequiredError:
        # CAPTCHA detected in headless mode - retry with visible browser
        if headless:
            print("CAPTCHA detected - retrying with visible browser for manual solving")
            if user_id:
                sync_status.set_status(user_id, provider, "captcha",
                    "CAPTCHA detected - opening browser for manual solving...")

            # Retry with visible browser
            crawler = ReginaMariaCrawler(headless=False, user_id=user_id)
            if user_id:
                crawler.set_status_callback(lambda stage, msg: _update_status(user_id, provider, stage, msg))

            try:
                docs = await crawler.run({"username": username, "password": password})
                return {"status": "success", "message": f"Crawled {len(docs)} documents", "documents": docs}
            except Exception as e:
                err = traceback.format_exc()
                print(f"Crawler Error (visible mode): {err}")
                return {"status": "error", "message": f"Regina Failed: {str(e)}"}
        else:
            return {"status": "error", "message": "CAPTCHA solving failed"}
    except Exception as e:
        err = traceback.format_exc()
        print(f"Crawler Error: {err}")
        return {"status": "error", "message": f"Regina Failed: {str(e)}"}

async def run_synevo_async(username, password, headless=True, user_id=None):
    """
    Run Synevo crawler with status updates.

    Args:
        username: Synevo account CNP (Romanian ID number)
        password: Synevo account password
        headless: If True (default), browser window will be hidden
        user_id: User ID for status tracking and file isolation (required for production)
    """
    provider = "Synevo"
    crawler = SynevoCrawler(headless=headless, user_id=user_id)

    # Set up status callback
    if user_id:
        crawler.set_status_callback(lambda stage, msg: _update_status(user_id, provider, stage, msg))

    try:
        docs = await crawler.run({"username": username, "password": password})
        return {"status": "success", "message": f"Crawled {len(docs)} documents", "documents": docs}
    except Exception as e:
        err = traceback.format_exc()
        print(f"Crawler Error: {err}")
        return {"status": "error", "message": f"Synevo Failed: {type(e).__name__} - {str(e)}"}


def _update_status(user_id: int, provider: str, stage: str, message: str):
    """Helper to update sync status."""
    if stage == "login":
        sync_status.status_logging_in(user_id, provider)
    elif stage == "logged_in":
        sync_status.status_logged_in(user_id, provider)
    elif stage == "navigating":
        sync_status.status_navigating(user_id, provider)
    elif stage == "scanning":
        sync_status.status_scanning(user_id, provider)
    elif stage == "downloading":
        # Parse progress from message if available
        sync_status.set_status(user_id, provider, "downloading", message)
    else:
        sync_status.set_status(user_id, provider, stage, message)

