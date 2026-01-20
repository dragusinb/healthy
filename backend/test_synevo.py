import asyncio
import sys
import os

# Add backend parent dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.crawlers.synevo import SynevoCrawler

async def main():
    # Credentials from successful subagent run
    creds = {
        "username": "1840927284564",
        "password": "27090O2-" 
    }
    
    print("Starting Synevo Crawler Test...")
    # Using headless=True by default for speed, but user can change if debugging needed.
    # We will use False to see it work if we were watching, but since this is an agent, 
    # True is safer unless we want to screenshot. The crawler class has screenshot logic.
    crawler = SynevoCrawler(headless=True) 
    
    try:
        documents = await crawler.run(creds)
        print(f"Crawler finished. Found {len(documents)} documents.")
        for doc in documents:
            print(f" - {doc['filename']} ({doc['date']}) -> {doc['local_path']}")
    except Exception as e:
        print(f"Crawler failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
