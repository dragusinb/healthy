from cryptography.fernet import Fernet
import sys
import os

# quick hack to import backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import SessionLocal, engine, Base, SQL_ALCHEMY_DATABASE_URL
from backend.models import Provider

# Generate a key (In prod, load this from env)
# For this local running session, we'll generate one and print it, 
# or use a fixed one for dev convenience if acceptable (NOT SECURE but practical for dev task)
# Let's use a fixed key logic for this dev session so we can run the crawler next.
KEY_FILE = "secret.key"

def get_or_create_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        return key

def encrypt_password(password: str, key: bytes) -> str:
    f = Fernet(key)
    return f.encrypt(password.encode()).decode()

def decrypt_password(token: str, key: bytes) -> str:
    f = Fernet(key)
    return f.decrypt(token.encode()).decode()

def seed(username, password):
    print(f"Using database at: {SQL_ALCHEMY_DATABASE_URL}")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    key = get_or_create_key()
    encrypted_pw = encrypt_password(password, key)
    
    # Check if provider exists
    provider = db.query(Provider).filter(Provider.name == "regina_maria").first()
    if not provider:
        provider = Provider(name="regina_maria")
        db.add(provider)
    
    provider.username = username
    provider.encrypted_credentials = encrypted_pw
    
    db.commit()
    db.close()
    print("Credentials seeded successfully for Regina Maria.")

if __name__ == "__main__":
    if len(sys.path) > 1:
        # Args
        u = "dragusinb@gmail.com"
        p = "Vl@dut123" 
        seed(u, p)
