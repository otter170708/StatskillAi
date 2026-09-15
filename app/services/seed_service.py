import json
import os
from sqlalchemy.orm import Session
from app.models import Competency, Course, Learner, Material
from app.database import Base, engine

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED_DIR = os.path.join(BASE_DIR, "seed")

def init_db(db: Session):
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Seed Competencies
    if db.query(Competency).count() == 0:
        comp_file = os.path.join(SEED_DIR, "competencies.json")
        if os.path.exists(comp_file):
            with open(comp_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    comp = Competency(
                        competency_id=item["competency_id"],
                        competency_name=item["competency_name"],
                        description=item["description"],
                        level=item.get("level", "intermediate"),
                        domain=item.get("domain", "Functional")
                    )
                    db.add(comp)
            db.commit()

    # Seed Courses
    if db.query(Course).count() == 0:
        courses_file = os.path.join(SEED_DIR, "courses.json")
        if os.path.exists(courses_file):
            with open(courses_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    course = Course(
                        course_id=item["course_id"],
                        course_name=item["course_name"],
                        description=item["description"],
                        competency_ids=json.dumps(item.get("competency_ids", [])),
                        level=item.get("level", "intermediate"),
                        language=item.get("language", "English"),
                        duration_minutes=item.get("duration_minutes", 45),
                        provider=item.get("provider", "iGOT Karmayogi / NSSTA"),
                        course_url=item.get("course_url"),
                        igot_course_id=item.get("igot_course_id")
                    )
                    db.add(course)
            db.commit()

    # Seed Learners (Idempotent: adds missing learners)
    learners_file = os.path.join(SEED_DIR, "learners.json")
    if os.path.exists(learners_file):
        with open(learners_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data:
                existing = db.query(Learner).filter(Learner.learner_id == item["learner_id"]).first()
                if not existing:
                    learner = Learner(
                        learner_id=item["learner_id"],
                        name=item["name"],
                        role=item["role"],
                        department=item["department"],
                        experience_level=item.get("experience_level", "intermediate"),
                        preferred_language=item.get("preferred_language", "English")
                    )
                    db.add(learner)
        db.commit()

    # Seed Sample Materials
    if db.query(Material).count() == 0:
        sample_dir = os.path.join(SEED_DIR, "sample_materials")
        if os.path.exists(sample_dir):
            file1 = os.path.join(sample_dir, "nsso_79th_round_guidelines.txt")
            if os.path.exists(file1):
                with open(file1, "r", encoding="utf-8") as f:
                    text1 = f.read()
                mat1 = Material(
                    material_id="MAT-NSSO-79-SAMPLE",
                    title="NSS 79th Round - Field Scrutiny & Sampling Guidelines",
                    source_type="text",
                    language="English",
                    extracted_text=text1,
                    topic_tags=json.dumps(["Sampling", "Field Scrutiny", "NSSO", "Confidentiality"])
                )
                db.add(mat1)

            file2 = os.path.join(sample_dir, "data_quality_assurance_manual.txt")
            if os.path.exists(file2):
                with open(file2, "r", encoding="utf-8") as f:
                    text2 = f.read()
                mat2 = Material(
                    material_id="MAT-NSSTA-QA-SAMPLE",
                    title="NSSTA Handbook on Data Quality Assurance & Audit Trails",
                    source_type="text",
                    language="English",
                    extracted_text=text2,
                    topic_tags=json.dumps(["Data Quality", "CAPI Checks", "Audit Trails", "Imputation"])
                )
                db.add(mat2)
            db.commit()
