import uuid
import json
import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Quiz, Question, Material, Attempt, Learner
from app.schemas import (
    QuizGenerateRequest, QuizResponse, QuestionSchema,
    QuizSubmitRequest, AttemptResultResponse
)
from app.services.ai_service import ai_service
from app.services.diagnostic_engine import diagnostic_engine
from app.services.recsys_service import recsys_service

router = APIRouter(prefix="/api/quizzes", tags=["Quizzes & Assessments"])

def _question_to_schema(q_data: dict, q_id: str, review_status: str = "APPROVED", hide_answers: bool = True) -> QuestionSchema:
    extra = q_data.get("extra") or {}
    return QuestionSchema(
        question_id=q_id,
        competency_mapped=q_data.get("competency_mapped", "OSS-STAT-02"),
        bloom_taxonomy_level=q_data.get("bloom_taxonomy_level", "Application"),
        question_type=q_data.get("question_type", "mcq") or "mcq",
        scenario_text=q_data.get("scenario_text", ""),
        question_text=q_data.get("question_text"),
        options=q_data.get("options", {}),
        match_pairs=q_data.get("match_pairs") or extra.get("match_pairs"),
        allow_upload=q_data.get("allow_upload", False),
        correct_option=None if hide_answers else q_data.get("correct_option"),
        explanation=None if hide_answers else q_data.get("explanation"),
        distractor_analysis=None if hide_answers else q_data.get("distractor_analysis"),
        review_status=review_status,
    )

def _persist_question_row(quiz_id: str, q_id: str, q_data: dict) -> Question:
    extra = {
        "match_pairs": q_data.get("match_pairs"),
        "allow_upload": q_data.get("allow_upload", False),
    }
    return Question(
        quiz_id=quiz_id,
        question_id=q_id,
        competency_mapped=q_data.get("competency_mapped", "OSS-STAT-02"),
        bloom_taxonomy_level=q_data.get("bloom_taxonomy_level", "Application"),
        question_type=q_data.get("question_type", "mcq") or "mcq",
        question_text=q_data.get("question_text"),
        extra_json=json.dumps(extra),
        scenario_text=q_data.get("scenario_text", ""),
        options_json=json.dumps(q_data.get("options", {})),
        correct_option=q_data.get("correct_option", "A"),
        explanation=q_data.get("explanation", ""),
        distractor_analysis_json=json.dumps(q_data.get("distractor_analysis", {})),
        review_status="APPROVED"
    )

@router.post("/generate", response_model=QuizResponse)
async def generate_quiz(payload: QuizGenerateRequest, db: Session = Depends(get_db)):
    context_text = ""
    target_material_id = payload.material_id

    if payload.material_id:
        mat = db.query(Material).filter(Material.material_id == payload.material_id).first()
        if mat:
            context_text = mat.extracted_text
            if not payload.title or payload.title == "Statistical Scenario Assessment":
                payload.title = f"Assessment: {mat.title}"
    
    if payload.custom_text:
        extra = payload.custom_text.strip()
        if extra:
            context_text = f"{context_text}\n{extra}".strip() if context_text else extra
    
    if not context_text:
        # Fallback to standard NSSO material if none provided
        sample_mat = db.query(Material).first()
        if sample_mat:
            context_text = sample_mat.extracted_text
            target_material_id = sample_mat.material_id
        else:
            context_text = "Official statistical survey protocols and data validation rules."

    # Track recently seen question scenarios for the learner to ensure fresh questions on subsequent attempts
    excluded_pool_ids = []
    if payload.learner_id:
        recent_attempts = db.query(Attempt).filter(Attempt.learner_id == payload.learner_id).order_by(Attempt.completed_at.desc()).limit(3).all()
        for att in recent_attempts:
            past_questions = db.query(Question).filter(Question.quiz_id == att.quiz_id).all()
            for pq in past_questions:
                # Add scenario text signature to exclusion
                excluded_pool_ids.append(pq.scenario_text[:40])

    # Generate questions via AI engine with randomized option order and fresh selection
    raw_questions = await ai_service.generate_mcqs(
        context_text=context_text,
        num_questions=payload.number_of_questions,
        difficulty=payload.difficulty,
        role_target=payload.role_target,
        excluded_scenario_hashes=excluded_pool_ids,
        format_type=payload.format_type
    )

    quiz_id = f"QUIZ-{uuid.uuid4().hex[:8].upper()}"
    new_quiz = Quiz(
        quiz_id=quiz_id,
        material_id=target_material_id,
        title=payload.title or "Official Statistical Scenario Assessment",
        num_questions=len(raw_questions),
        difficulty=payload.difficulty,
        status="ready"
    )
    db.add(new_quiz)

    question_schemas = []
    for idx, q_data in enumerate(raw_questions):
        q_id = f"Q{idx + 1}"
        db.add(_persist_question_row(quiz_id, q_id, q_data))
        question_schemas.append(_question_to_schema(q_data, q_id, hide_answers=True))

    db.commit()

    return QuizResponse(
        quiz_id=quiz_id,
        title=new_quiz.title,
        material_id=new_quiz.material_id,
        num_questions=len(question_schemas),
        difficulty=new_quiz.difficulty,
        questions=question_schemas,
        created_at=new_quiz.created_at
    )

@router.get("/{quiz_id}", response_model=QuizResponse)
def get_quiz(quiz_id: str, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.quiz_id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    questions = db.query(Question).filter(Question.quiz_id == quiz_id).all()
    q_schemas = []
    for q in questions:
        opts = json.loads(q.options_json) if isinstance(q.options_json, str) else q.options_json
        extra = {}
        if q.extra_json:
            try:
                extra = json.loads(q.extra_json) if isinstance(q.extra_json, str) else (q.extra_json or {})
            except Exception:
                extra = {}
        q_schemas.append(_question_to_schema({
            "competency_mapped": q.competency_mapped,
            "bloom_taxonomy_level": q.bloom_taxonomy_level,
            "question_type": getattr(q, "question_type", None) or "mcq",
            "scenario_text": q.scenario_text,
            "question_text": getattr(q, "question_text", None),
            "options": opts,
            "match_pairs": extra.get("match_pairs"),
            "allow_upload": extra.get("allow_upload", False),
        }, q.question_id, review_status=q.review_status, hide_answers=True))

    return QuizResponse(
        quiz_id=quiz.quiz_id,
        title=quiz.title,
        material_id=quiz.material_id,
        num_questions=len(q_schemas),
        difficulty=quiz.difficulty,
        questions=q_schemas,
        created_at=quiz.created_at
    )

@router.post("/{quiz_id}/submit", response_model=AttemptResultResponse)
def submit_quiz_attempt(
    quiz_id: str,
    payload: QuizSubmitRequest,
    db: Session = Depends(get_db)
):
    quiz = db.query(Quiz).filter(Quiz.quiz_id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    learner = db.query(Learner).filter(Learner.learner_id == payload.learner_id).first()
    if not learner:
        learner = db.query(Learner).first()

    # Run Diagnostic Engine
    (
        score,
        total_questions,
        percentage,
        grade_message,
        competency_scores,
        diagnosed_gaps,
        question_reviews
    ) = diagnostic_engine.evaluate_quiz(db, quiz_id, payload.answers)

    # Get targeted iGOT recommendations for diagnosed gaps
    recommendations = recsys_service.get_recommendations_for_gaps(db, diagnosed_gaps)

    # Persist Attempt Record in Database
    attempt_id = f"ATT-{uuid.uuid4().hex[:8].upper()}"
    attempt = Attempt(
        attempt_id=attempt_id,
        quiz_id=quiz_id,
        learner_id=learner.learner_id if learner else payload.learner_id,
        score=score,
        total_questions=total_questions,
        percentage=percentage,
        answers_json=json.dumps([a.dict() for a in payload.answers]),
        gaps_json=json.dumps([g.dict() for g in diagnosed_gaps]),
        recommendations_json=json.dumps([r.dict() for r in recommendations]),
        completed_at=datetime.datetime.utcnow()
    )
    db.add(attempt)
    db.commit()

    # Calculate points and attempt history for charts
    points_earned = 50 + int(percentage * 0.5)
    all_attempts = db.query(Attempt).filter(Attempt.learner_id == attempt.learner_id).order_by(Attempt.completed_at.asc()).all()
    total_karma_points = sum(50 + int(a.percentage * 0.5) for a in all_attempts)

    # Calculate accurate consecutive calendar day streak (at most 1 increase per day)
    today = datetime.datetime.utcnow().date()
    yesterday = today - datetime.timedelta(days=1)
    unique_dates = sorted(list(set(a.completed_at.date() for a in all_attempts)), reverse=True)
    streak_days = 0

    if unique_dates:
        if unique_dates[0] == today:
            streak_days = 1
            curr = today - datetime.timedelta(days=1)
            for d in unique_dates[1:]:
                if d == curr:
                    streak_days += 1
                    curr -= datetime.timedelta(days=1)
                else:
                    break
        elif unique_dates[0] == yesterday:
            streak_days = 1
            curr = yesterday - datetime.timedelta(days=1)
            for d in unique_dates[1:]:
                if d == curr:
                    streak_days += 1
                    curr -= datetime.timedelta(days=1)
                else:
                    break
        else:
            streak_days = 0
    
    attempt_history = [
        {
            "attempt_number": idx + 1,
            "score": a.score,
            "total": a.total_questions,
            "percentage": a.percentage,
            "date": a.completed_at.strftime("%b %d, %H:%M")
        }
        for idx, a in enumerate(all_attempts)
    ]

    return AttemptResultResponse(
        attempt_id=attempt_id,
        quiz_id=quiz_id,
        learner_id=attempt.learner_id,
        score=score,
        total_questions=total_questions,
        percentage=percentage,
        grade_message=grade_message,
        points_earned=points_earned,
        total_karma_points=total_karma_points,
        learning_streak_days=streak_days,
        competency_breakdown=competency_scores,
        diagnosed_gaps=diagnosed_gaps,
        recommendations=recommendations,
        question_reviews=question_reviews,
        attempt_history=attempt_history,
        completed_at=attempt.completed_at
    )
