import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app.models import Question, Quiz
from app.schemas import QuestionReviewUpdateRequest

router = APIRouter(prefix="/api/sme-review", tags=["SME / Human-in-the-Loop Review"])

@router.get("/questions")
def get_questions_for_review(
    quiz_id: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(Question)
    if quiz_id:
        query = query.filter(Question.quiz_id == quiz_id)
    
    questions = query.all()
    results = []
    for q in questions:
        opts = json.loads(q.options_json) if isinstance(q.options_json, str) else q.options_json
        distractors = json.loads(q.distractor_analysis_json) if isinstance(q.distractor_analysis_json, str) else (q.distractor_analysis_json or {})
        results.append({
            "id": q.id,
            "quiz_id": q.quiz_id,
            "question_id": q.question_id,
            "competency_mapped": q.competency_mapped,
            "bloom_taxonomy_level": q.bloom_taxonomy_level,
            "scenario_text": q.scenario_text,
            "options": opts,
            "correct_option": q.correct_option,
            "explanation": q.explanation,
            "distractor_analysis": distractors,
            "review_status": q.review_status,
            "reviewer_notes": q.reviewer_notes
        })
    return results

@router.put("/questions/{question_db_id}")
def update_question_review(
    question_db_id: int,
    payload: QuestionReviewUpdateRequest,
    db: Session = Depends(get_db)
):
    q = db.query(Question).filter(Question.id == question_db_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    
    q.review_status = payload.review_status
    if payload.reviewer_notes is not None:
        q.reviewer_notes = payload.reviewer_notes
    if payload.edited_scenario_text:
        q.scenario_text = payload.edited_scenario_text
    if payload.edited_correct_option:
        q.correct_option = payload.edited_correct_option
    if payload.edited_explanation:
        q.explanation = payload.edited_explanation

    db.commit()
    return {"message": "Question review status successfully updated", "question_id": q.question_id, "status": q.review_status}
