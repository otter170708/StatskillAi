from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# For SQLite, enable check_same_thread=False
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def ensure_schema_upgrades():
    """Add columns introduced after the original SQLite schema was created."""
    inspector = inspect(engine)
    if "questions" not in inspector.get_table_names():
        return
    existing = {col["name"] for col in inspector.get_columns("questions")}
    alters = []
    if "question_type" not in existing:
        alters.append("ALTER TABLE questions ADD COLUMN question_type VARCHAR(50) DEFAULT 'mcq'")
    if "question_text" not in existing:
        alters.append("ALTER TABLE questions ADD COLUMN question_text TEXT")
    if "extra_json" not in existing:
        alters.append("ALTER TABLE questions ADD COLUMN extra_json TEXT")
    if not alters:
        return
    with engine.begin() as conn:
        for stmt in alters:
            conn.execute(text(stmt))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
