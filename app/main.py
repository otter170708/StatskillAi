import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.database import SessionLocal, engine, Base, ensure_schema_upgrades
from app.services.seed_service import init_db
from app.routers import materials, quizzes, competencies, courses, learners, sme_review

# Guarantee table creation and seed data on import / startup
Base.metadata.create_all(bind=engine)
try:
    ensure_schema_upgrades()
except Exception as e:
    print(f"Schema upgrade warning: {e}")
try:
    _db = SessionLocal()
    init_db(_db)
    _db.close()
except Exception as e:
    print(f"DB init warning: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure fresh session seed check
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Enabled Learning & Assessment Platform for India's Official Statistical System (iGOT Karmayogi)",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(materials.router)
app.include_router(quizzes.router)
app.include_router(competencies.router)
app.include_router(courses.router)
app.include_router(learners.router)
app.include_router(sme_review.router)

# Static & Frontend Handling
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=FileResponse)
def serve_frontend():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "StatSkill AI Backend API Running", "docs": "/docs"}

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.ENV,
        "ai_provider": settings.AI_PROVIDER,
        "ocr_enabled": settings.ENABLE_OCR
    }
