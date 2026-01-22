from fastapi import FastAPI
from dotenv import load_dotenv
import os
import sys
import asyncio

# Fix for Windows Python 3.8+ subprocess in asyncio
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

load_dotenv() # Load .env file

# Force reload trigger 2
from fastapi.middleware.cors import CORSMiddleware
from backend_v2.routers import auth, users, dashboard, documents, health
from backend_v2.database import Base, engine, SessionLocal
from backend_v2.routers.auth import seed_default_user

# Create Tables
Base.metadata.create_all(bind=engine)

# Seed Data
db = SessionLocal()
seed_default_user(db)
db.close()

app = FastAPI(title="Healthy v2 API", version="2.0")

# CORS - configurable via environment
default_origins = [
    "http://localhost:5173",  # React Vite dev
    "http://localhost:3000",
    "http://localhost:4173",  # Vite preview
]
# Add production origins from env (comma-separated)
extra_origins = os.getenv("CORS_ORIGINS", "").split(",")
origins = default_origins + [o.strip() for o in extra_origins if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(dashboard.router)
app.include_router(documents.router)
app.include_router(health.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to Healthy v2 API"}
