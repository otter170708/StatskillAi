import datetime
from sqlalchemy import Column, String, Integer, Float, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Competency(Base):
    __tablename__ = "competencies"

    competency_id = Column(String(50), primary_key=True, index=True)
    competency_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    level = Column(String(50), default="intermediate")  # basic, intermediate, advanced
    domain = Column(String(50), default="Functional")   # Knowledge, Functional, Behavioral/Compliance

class Course(Base):
    __tablename__ = "courses"

    course_id = Column(String(50), primary_key=True, index=True)
    course_name = Column(String(250), nullable=False)
    description = Column(Text, nullable=False)
    competency_ids = Column(Text, nullable=False)  # Stored as JSON string or comma-separated list
    level = Column(String(50), default="intermediate")
    language = Column(String(50), default="English")
    duration_minutes = Column(Integer, default=45)
    provider = Column(String(100), default="iGOT Karmayogi / NSSTA")
    course_url = Column(String(500), nullable=True)
    igot_course_id = Column(String(100), nullable=True)

class Learner(Base):
    __tablename__ = "learners"

    learner_id = Column(String(50), primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    role = Column(String(150), nullable=False)
    department = Column(String(200), nullable=False)
    experience_level = Column(String(50), default="intermediate")
    preferred_language = Column(String(50), default="English")

class Material(Base):
    __tablename__ = "materials"

    material_id = Column(String(100), primary_key=True, index=True)
    title = Column(String(250), nullable=False)
    source_type = Column(String(50), default="pdf")  # pdf, text, circular
    language = Column(String(50), default="English")
    file_path = Column(String(500), nullable=True)
    extracted_text = Column(Text, nullable=False)
    topic_tags = Column(Text, nullable=True)  # JSON array
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Quiz(Base):
    __tablename__ = "quizzes"

    quiz_id = Column(String(100), primary_key=True, index=True)
    material_id = Column(String(100), ForeignKey("materials.material_id"), nullable=True)
    title = Column(String(250), nullable=False)
    num_questions = Column(Integer, default=5)
    difficulty = Column(String(50), default="medium")
    status = Column(String(50), default="ready")  # ready, in_review, archived
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    quiz_id = Column(String(100), ForeignKey("quizzes.quiz_id"), nullable=False)
    question_id = Column(String(50), nullable=False)
    competency_mapped = Column(String(100), nullable=False)
    bloom_taxonomy_level = Column(String(50), default="Application")  # Recall, Understanding, Application, Analysis
    question_type = Column(String(50), default="mcq")
    question_text = Column(Text, nullable=True)
    extra_json = Column(Text, nullable=True)
    scenario_text = Column(Text, nullable=False)
    options_json = Column(Text, nullable=False)  # JSON: {"A": "...", "B": "...", "C": "...", "D": "..."}
    correct_option = Column(String(10), nullable=False)
    explanation = Column(Text, nullable=False)
    distractor_analysis_json = Column(Text, nullable=False)  # JSON: {"A": "...", "B": "..."}
    review_status = Column(String(50), default="APPROVED")  # APPROVED, PENDING, NEEDS_REVISION
    reviewer_notes = Column(Text, nullable=True)

    quiz = relationship("Quiz", back_populates="questions")

class Attempt(Base):
    __tablename__ = "attempts"

    attempt_id = Column(String(100), primary_key=True, index=True)
    quiz_id = Column(String(100), ForeignKey("quizzes.quiz_id"), nullable=False)
    learner_id = Column(String(50), ForeignKey("learners.learner_id"), nullable=False)
    score = Column(Integer, default=0)
    total_questions = Column(Integer, default=0)
    percentage = Column(Float, default=0.0)
    answers_json = Column(Text, nullable=False)  # JSON array of selected answers & confidence
    gaps_json = Column(Text, nullable=False)     # JSON array of diagnosed gaps
    recommendations_json = Column(Text, nullable=False)  # JSON array of recommended iGOT courses
    completed_at = Column(DateTime, default=datetime.datetime.utcnow)
