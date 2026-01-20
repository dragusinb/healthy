from backend_v2.services.regina_maria_crawler import ReginaMariaCrawler
from backend_v2.services.synevo_crawler import SynevoCrawler
import asyncio

import traceback

def trigger_crawl_regina(username, password):
    print(f"Starting Regina Maria crawl for {username}")
    try:
        crawler = ReginaMariaCrawler(headless=True)
        # Since we are likely in a synchronous endpoint context but crawlers are async,
        # we need to run them properly.
        # If this is called from a FastAPI async path, we should ideally await it.
        # But for now, using asyncio.run() creates a new event loop which might conflict if already running.
        # Better: make these trigger functions async and await them in the router.
        
        # However, for this simple wrapper:
        return {"status": "error", "message": "Crawler requires async execution. Please update router to call await crawler.run()"}
    except Exception as e:
        err = traceback.format_exc()
        print(err)
        return {"status": "error", "message": f"Setup Failed: {str(e)}"}

async def run_regina_async(username, password, headless=False):
    """
    Run Regina Maria crawler.

    Args:
        username: Regina Maria account username
        password: Regina Maria account password
        headless: If False (default), browser window will be visible for manual reCAPTCHA solving
    """
    crawler = ReginaMariaCrawler(headless=headless)
    try:
        docs = await crawler.run({"username": username, "password": password})
        return {"status": "success", "message": f"Crawled {len(docs)} documents", "documents": docs}
    except Exception as e:
        err = traceback.format_exc()
        print(f"Crawler Error: {err}")
        return {"status": "error", "message": f"Regina Failed: {str(e)}"}

async def run_synevo_async(username, password, headless=False):
    """
    Run Synevo crawler.

    Args:
        username: Synevo account CNP (Romanian ID number)
        password: Synevo account password
        headless: If False (default), browser window will be visible
    """
    crawler = SynevoCrawler(headless=headless)
    try:
        docs = await crawler.run({"username": username, "password": password})
        return {"status": "success", "message": f"Crawled {len(docs)} documents", "documents": docs}
    except Exception as e:
        err = traceback.format_exc()
        print(f"Crawler Error: {err}")
        return {"status": "error", "message": f"Synevo Failed: {type(e).__name__} - {str(e)}\nDetails: {err[:150]}..."}

