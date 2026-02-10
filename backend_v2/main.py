from fastapi import FastAPI
from dotenv import load_dotenv
import os
import sys
import asyncio

# Fix for Windows Python 3.8+ subprocess in asyncio
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

load_dotenv() # Load .env file

from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

# Support both local development (backend_v2.X) and production (X) imports
try:
    from backend_v2.routers import auth, users, dashboard, documents, health, admin, vault, notifications, subscription, payment, gdpr
    from backend_v2.database import Base, engine, SessionLocal
    from backend_v2.routers.auth import seed_default_user
    from backend_v2.services.scheduler import init_scheduler, shutdown_scheduler
except ImportError:
    from routers import auth, users, dashboard, documents, health, admin, vault, notifications, subscription, payment, gdpr
    from database import Base, engine, SessionLocal
    from routers.auth import seed_default_user
    from services.scheduler import init_scheduler, shutdown_scheduler

# Create Tables
Base.metadata.create_all(bind=engine)

# Seed Data
db = SessionLocal()
seed_default_user(db)
db.close()

app = FastAPI(title="Healthy v2 API", version="2.0")

# CORS - configurable via environment (no hardcoded production IPs)
default_origins = [
    "http://localhost:5173",  # React Vite dev
    "http://localhost:3000",
    "http://localhost:4173",  # Vite preview
]
# Add production origins from env (comma-separated) - REQUIRED for production
# Example: CORS_ORIGINS=https://analize.online,https://www.analize.online
extra_origins = os.getenv("CORS_ORIGINS", "").split(",")
origins = default_origins + [o.strip() for o in extra_origins if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Vault-Token"],
)

# Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(dashboard.router)
app.include_router(documents.router)
app.include_router(health.router)
app.include_router(admin.router)
app.include_router(vault.router)
app.include_router(notifications.router)
app.include_router(subscription.router)
app.include_router(payment.router)
app.include_router(gdpr.router)

# Prometheus metrics instrumentation for HTTP request tracking
# Exposes metrics at /api/metrics for Prometheus scraping
instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/health", "/metrics", "/api/metrics"],
    inprogress_name="http_requests_inprogress",
    inprogress_labels=True,
)
instrumentator.instrument(app).expose(app, endpoint="/api/metrics", include_in_schema=False)


# Initialize scheduler on startup
@app.on_event("startup")
def startup_event():
    init_scheduler()


@app.on_event("shutdown")
def shutdown_event():
    shutdown_scheduler()


@app.get("/")
def read_root():
    return {"message": "Welcome to Healthy v2 API"}


@app.get("/health")
def health_check():
    """
    Comprehensive health check endpoint for monitoring.

    Checks:
    - Database connectivity
    - Disk space (warns if > 80%, critical if > 90%)
    - Memory usage (warns if > 80%, critical if > 90%)
    - Vault status

    Returns overall status: "healthy", "degraded", or "unhealthy"
    """
    import psutil
    from datetime import datetime

    checks = {}
    issues = []

    # Check database connectivity
    try:
        from backend_v2.database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        checks["database"] = {"status": "ok", "message": "Connected"}
    except Exception as e:
        checks["database"] = {"status": "error", "message": str(e)[:100]}
        issues.append("database")

    # Check disk space
    try:
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        if disk_percent > 90:
            checks["disk"] = {"status": "critical", "percent_used": disk_percent, "message": "Disk space critically low"}
            issues.append("disk_critical")
        elif disk_percent > 80:
            checks["disk"] = {"status": "warning", "percent_used": disk_percent, "message": "Disk space running low"}
        else:
            checks["disk"] = {"status": "ok", "percent_used": disk_percent}
    except Exception as e:
        checks["disk"] = {"status": "error", "message": str(e)[:100]}

    # Check memory
    try:
        memory = psutil.virtual_memory()
        mem_percent = memory.percent
        if mem_percent > 90:
            checks["memory"] = {"status": "critical", "percent_used": mem_percent, "message": "Memory critically low"}
            issues.append("memory_critical")
        elif mem_percent > 80:
            checks["memory"] = {"status": "warning", "percent_used": mem_percent, "message": "Memory running low"}
        else:
            checks["memory"] = {"status": "ok", "percent_used": mem_percent}
    except Exception as e:
        checks["memory"] = {"status": "error", "message": str(e)[:100]}

    # Check vault status
    try:
        from backend_v2.services.vault import vault
        checks["vault"] = {
            "status": "ok" if vault.is_unlocked else "locked",
            "is_configured": vault.is_configured,
            "is_unlocked": vault.is_unlocked
        }
        if not vault.is_unlocked:
            issues.append("vault_locked")
    except Exception as e:
        checks["vault"] = {"status": "error", "message": str(e)[:100]}

    # Determine overall status
    if any("critical" in i or i == "database" for i in issues):
        overall_status = "unhealthy"
    elif issues:
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks,
        "issues": issues if issues else None
    }


@app.get("/metrics")
def metrics():
    """
    Prometheus-compatible metrics endpoint.

    Returns metrics in Prometheus text format for monitoring systems.
    """
    import psutil
    from fastapi.responses import PlainTextResponse

    lines = []

    # System metrics
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        lines.append(f"# HELP healthy_cpu_usage_percent CPU usage percentage")
        lines.append(f"# TYPE healthy_cpu_usage_percent gauge")
        lines.append(f"healthy_cpu_usage_percent {cpu_percent}")
    except Exception:
        pass

    try:
        memory = psutil.virtual_memory()
        lines.append(f"# HELP healthy_memory_usage_percent Memory usage percentage")
        lines.append(f"# TYPE healthy_memory_usage_percent gauge")
        lines.append(f"healthy_memory_usage_percent {memory.percent}")
        lines.append(f"# HELP healthy_memory_available_bytes Available memory in bytes")
        lines.append(f"# TYPE healthy_memory_available_bytes gauge")
        lines.append(f"healthy_memory_available_bytes {memory.available}")
    except Exception:
        pass

    try:
        disk = psutil.disk_usage('/')
        lines.append(f"# HELP healthy_disk_usage_percent Disk usage percentage")
        lines.append(f"# TYPE healthy_disk_usage_percent gauge")
        lines.append(f"healthy_disk_usage_percent {disk.percent}")
        lines.append(f"# HELP healthy_disk_free_bytes Free disk space in bytes")
        lines.append(f"# TYPE healthy_disk_free_bytes gauge")
        lines.append(f"healthy_disk_free_bytes {disk.free}")
    except Exception:
        pass

    # Database metrics
    try:
        from backend_v2.database import SessionLocal
        from backend_v2.models import User, Document, TestResult, HealthReport, LinkedAccount

        db = SessionLocal()
        user_count = db.query(User).count()
        doc_count = db.query(Document).count()
        biomarker_count = db.query(TestResult).count()
        report_count = db.query(HealthReport).count()
        account_count = db.query(LinkedAccount).count()
        db.close()

        lines.append(f"# HELP healthy_users_total Total number of users")
        lines.append(f"# TYPE healthy_users_total gauge")
        lines.append(f"healthy_users_total {user_count}")

        lines.append(f"# HELP healthy_documents_total Total number of documents")
        lines.append(f"# TYPE healthy_documents_total gauge")
        lines.append(f"healthy_documents_total {doc_count}")

        lines.append(f"# HELP healthy_biomarkers_total Total number of biomarkers")
        lines.append(f"# TYPE healthy_biomarkers_total gauge")
        lines.append(f"healthy_biomarkers_total {biomarker_count}")

        lines.append(f"# HELP healthy_reports_total Total number of health reports")
        lines.append(f"# TYPE healthy_reports_total gauge")
        lines.append(f"healthy_reports_total {report_count}")

        lines.append(f"# HELP healthy_linked_accounts_total Total number of linked accounts")
        lines.append(f"# TYPE healthy_linked_accounts_total gauge")
        lines.append(f"healthy_linked_accounts_total {account_count}")
    except Exception:
        pass

    # Vault status
    try:
        from backend_v2.services.vault import vault
        lines.append(f"# HELP healthy_vault_unlocked Vault unlock status (1=unlocked, 0=locked)")
        lines.append(f"# TYPE healthy_vault_unlocked gauge")
        lines.append(f"healthy_vault_unlocked {1 if vault.is_unlocked else 0}")
    except Exception:
        pass

    return PlainTextResponse("\n".join(lines) + "\n", media_type="text/plain")
