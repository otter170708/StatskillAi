from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime

# --- Competency Schemas ---
class CompetencyBase(BaseModel):
    competency_id: str
    competency_name: str
    description: str
    level: str = "intermediate"
    domain: str = "Functional"

class CompetencyResponse(CompetencyBase):
    class Config:
        from_attributes = True

# --- Course Schemas ---
class CourseBase(BaseModel):
    course_id: str
    course_name: str
    description: str
    competency_ids: List[str]
    level: str = "intermediate"
    language: str = "English"
    duration_minutes: int = 45
    provider: str = "iGOT Karmayogi / NSSTA"
    course_url: Optional[str] = None
    igot_course_id: Optional[str] = None

class CourseResponse(CourseBase):
    class Config:
        from_attributes = True

# --- Learner Schemas ---
class LearnerBase(BaseModel):
    learner_id: str
    name: str
    role: str
    department: str
    experience_level: str = "intermediate"
    preferred_language: str = "English"

class LearnerResponse(LearnerBase):
    karma_points: Optional[int] = 0
    streak_days: Optional[int] = 0
    total_quizzes: Optional[int] = 0
    class Config:
        from_attributes = True

# --- Material Schemas ---
class MaterialUploadResponse(BaseModel):
    material_id: str
    title: str
    source_type: str
    character_count: int
    topic_tags: List[str]
    status: str = "ready"
    message: str = "Material uploaded and extracted successfully"

class MaterialTextUploadRequest(BaseModel):
    title: str
    text_content: str
    language: str = "English"

# --- Question & Quiz Schemas ---
class QuestionSchema(BaseModel):
    question_id: str
    competency_mapped: str
    bloom_taxonomy_level: str
    question_type: str = "mcq"  # mcq, true_false, fill_blank, match, short_answer, essay
    scenario_text: str
    question_text: Optional[str] = None
    options: Optional[Dict[str, str]] = None
    match_pairs: Optional[Dict[str, str]] = None
    match_column_b: Optional[List[str]] = None
    fill_blank_prompt: Optional[str] = None
    essay_guidelines: Optional[str] = None
    allow_upload: Optional[bool] = False
    correct_option: Optional[str] = None  # May be hidden from quiz taker
    explanation: Optional[str] = None
    distractor_analysis: Optional[Dict[str, str]] = None
    review_status: str = "APPROVED"

class AssessmentCatalogItem(BaseModel):
    item_id: str  # quiz_1, quiz_2, quiz_3, mcq_1, mcq_2
    title: str
    format_type: str  # "mixed" or "mcq"
    set_number: int
    allocated_topic: str
    question_count: int
    duration_minutes: int
    question_types: List[str]
    description: str

class AssessmentCatalogResponse(BaseModel):
    material_id: Optional[str] = None
    allocated_topics: List[str]
    items: List[AssessmentCatalogItem]

class QuizGenerateRequest(BaseModel):
    learner_id: Optional[str] = None
    material_id: Optional[str] = None
    custom_text: Optional[str] = None
    title: Optional[str] = "Statistical Scenario Assessment"
    format_type: str = "mcq"  # "mcq" for uploaded custom material; "mixed" for Quiz 1/2/3
    set_number: int = 1         # 1, 2, 3
    number_of_questions: int = 6
    difficulty: str = "medium"
    role_target: str = "Junior Statistical Officer"
    duration_minutes: Optional[int] = None

class QuizResponse(BaseModel):
    quiz_id: str
    title: str
    material_id: Optional[str]
    format_type: str = "mixed"
    set_number: int = 1
    duration_seconds: int = 1500  # Default 25 mins
    allocated_topic: Optional[str] = None
    num_questions: int
    difficulty: str
    questions: List[QuestionSchema]
    created_at: datetime

# --- Attempt & Submission Schemas ---
class AnswerSubmission(BaseModel):
    question_id: str
    selected_option: Optional[str] = None
    text_answer: Optional[str] = None
    match_answers: Optional[Dict[str, str]] = None
    uploaded_file_name: Optional[str] = None
    uploaded_file_data: Optional[str] = None
    confidence: str = "High"  # High, Medium, Low / Guessing

class QuizSubmitRequest(BaseModel):
    learner_id: str
    answers: List[AnswerSubmission]

class CompetencyScore(BaseModel):
    competency_id: str
    competency_name: str
    correct: int
    total: int
    percentage: float
    status: str  # Strong, Proficient, Needs Attention, Critical Gap

class DiagnosedGap(BaseModel):
    competency_id: str
    competency_name: str
    gap_nature: str  # Conceptual (Knowledge), Procedural (Functional), Compliance (Behavioral)
    severity: str    # Low, Medium, High, Critical
    diagnostic_summary: str
    recommended_focus_area: str
    confidence_factor: str

class RecommendedCourse(BaseModel):
    course_id: str
    course_title: str
    provider: str
    duration_minutes: int
    target_gap_addressed: str
    justification: str
    course_url: Optional[str] = None

class AttemptResultResponse(BaseModel):
    attempt_id: str
    quiz_id: str
    learner_id: str
    score: int
    total_questions: int
    percentage: float
    grade_message: str
    points_earned: int = 50
    total_karma_points: int = 50
    learning_streak_days: int = 1
    competency_breakdown: List[CompetencyScore]
    diagnosed_gaps: List[DiagnosedGap]
    recommendations: List[RecommendedCourse]
    question_reviews: List[Dict[str, Any]]
    attempt_history: Optional[List[Dict[str, Any]]] = None
    completed_at: datetime

# --- SME Review Schema ---
class QuestionReviewUpdateRequest(BaseModel):
    review_status: str  # APPROVED, NEEDS_REVISION, REJECTED
    reviewer_notes: Optional[str] = None
    edited_scenario_text: Optional[str] = None
    edited_correct_option: Optional[str] = None
    edited_explanation: Optional[str] = None

# --- Dashboard & Department Analytics Schemas ---
class LearnerDashboardResponse(BaseModel):
    learner: LearnerResponse
    total_quizzes_taken: int
    average_score: float
    learning_streak_days: int
    karma_points_earned: int
    active_competency_gaps: List[DiagnosedGap]
    recent_attempts: List[Dict[str, Any]]
    recommended_courses: List[RecommendedCourse]
    competency_mastery_radar: List[Dict[str, Any]]

# --- iGOT Karmayogi Enrolment & Government APAR Dossier Schemas ---
class CourseEnrolmentRequest(BaseModel):
    learner_id: str
    competency_id: Optional[str] = None

class CourseEnrolmentResponse(BaseModel):
    status: str
    enrolment_id: str
    course_id: str
    course_name: str
    learner_id: str
    learner_name: str
    igot_sync_status: str
    apar_competency_linked: Optional[str] = None
    karma_credit_awarded: int
    message: str
    enrolled_at: str

class OfficialDossierResponse(BaseModel):
    dossier_id: str
    issued_at: str
    issuing_authority: str
    officer: Dict[str, Any]
    assessment_summary: Dict[str, Any]
    competency_breakdown: List[Dict[str, Any]]
    critical_misconceptions: List[Dict[str, Any]]
    mandated_igot_courses: List[Dict[str, Any]]
    digital_seal_hash: str
    apar_compliance_status: str
