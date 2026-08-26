import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import settings
from backend.database.db import init_db, SessionLocal
from backend.database.seed import seed_database
from backend.routes import (
    workflows_router,
    approvals_router,
    failures_router,
    audit_logs_router,
    services_router,
    demo_router,
    settings_router,
    events_router
)
from backend.business_apis import (
    payment_router,
    inventory_router,
    order_router,
    delivery_router,
    notification_router
)

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database and seed sample data
    logger.info("Initializing database schemas...")
    init_db()
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    logger.info("Application startup complete. Ready to serve.")
    yield
    # Shutdown
    logger.info("Shutting down application...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Autonomous Business Workflow Recovery System powered by LangGraph AI Agent with Light 3D SaaS Interface.",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Core API Routes
app.include_router(workflows_router)
app.include_router(approvals_router)
app.include_router(failures_router)
app.include_router(audit_logs_router)
app.include_router(services_router)
app.include_router(demo_router)
app.include_router(settings_router)
app.include_router(events_router)

# Register Simulated Business Microservices APIs
app.include_router(payment_router)
app.include_router(inventory_router)
app.include_router(order_router)
app.include_router(delivery_router)
app.include_router(notification_router)

# Frontend Static Files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))
else:
    @app.get("/")
    async def root():
        return {"message": "AI Business Process Recovery Agent Backend API Active", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
