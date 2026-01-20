import asyncio
import sys
import os
from cryptography.fernet import Fernet

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import SessionLocal
from backend.models import Provider
from backend.crawlers.regina_maria import ReginaMariaCrawler

KEY_FILE = "backend/secret.key" 

def get_key():
    # Adjust path if running from root
    if os.path.exists("secret.key"):
        with open("secret.key", "rb") as f:
            return f.read()
    # Try backend/secret.key
    if os.path.exists("backend/secret.key"):
         with open("backend/secret.key", "rb") as f:
            return f.read()
    raise Exception("Key file not found")

def decrypt_password(token: str, key: bytes) -> str:
    f = Fernet(key)
    return f.decrypt(token.encode()).decode()

async def main():
    db = SessionLocal()
    provider = db.query(Provider).filter(Provider.name == "regina_maria").first()
    db.close()
    
    if not provider:
        print("No provider found. Run seed_credentials.py first.")
        return

    key = get_key()
    password = decrypt_password(provider.encrypted_credentials, key)
    
    creds = {
        "username": provider.username,
        "password": password
    }
    
    crawler = ReginaMariaCrawler(headless=False) # Run headed to see what happens
    await crawler.run(creds)

if __name__ == "__main__":
    asyncio.run(main())
