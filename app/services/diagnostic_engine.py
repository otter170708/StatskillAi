import json
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models import Question, Competency
from app.schemas import AnswerSubmission, CompetencyScore, DiagnosedGap

class DiagnosticEngine:
    @staticmethod
    def evaluate_quiz(
        db: Session,
        quiz_id: str,
        answers: List[AnswerSubmission]
    ) -> Tuple[int, int, float, str, List[CompetencyScore], List[DiagnosedGap], List[Dict[str, Any]]]:
        
        # Load questions for this quiz
        db_questions = db.query(Question).filter(Question.quiz_id == quiz_id).all()
        q_map = {q.question_id: q for q in db_questions}
        
        # Load all competencies for fast metadata lookup
        all_comps = {c.competency_id: c for c in db.query(Competency).all()}

        total_questions = len(answers)
        score = 0
        
        # Tracking by competency
        comp_stats = {} # comp_id -> {"total": 0, "correct": 0, "wrong_high_conf": 0, "mistakes": []}
        question_reviews = []

        for ans in answers:
            q = q_map.get(ans.question_id)
            if not q:
                continue
            
            comp_id = q.competency_mapped
            if comp_id not in comp_stats:
                comp_stats[comp_id] = {"total": 0, "correct": 0, "wrong_high_conf": 0, "mistakes": []}
            
            comp_stats[comp_id]["total"] += 1
            is_correct = (ans.selected_option.strip().upper() == q.correct_option.strip().upper())
            
            options_dict = json.loads(q.options_json) if isinstance(q.options_json, str) else q.options_json
            distractor_dict = json.loads(q.distractor_analysis_json) if isinstance(q.distractor_analysis_json, str) else (q.distractor_analysis_json or {})

            if is_correct:
                score += 1
                comp_stats[comp_id]["correct"] += 1
            else:
                distractor_reason = distractor_dict.get(ans.selected_option, "Incorrect choice violates standard operating procedure.")
                comp_stats[comp_id]["mistakes"].append({
                    "question_id": q.question_id,
                    "selected": ans.selected_option,
                    "correct": q.correct_option,
                    "reason": distractor_reason,
                    "confidence": ans.confidence
                })
                if ans.confidence.lower() in ["high", "certain"]:
                    comp_stats[comp_id]["wrong_high_conf"] += 1

            question_reviews.append({
                "question_id": q.question_id,
                "competency_mapped": comp_id,
                "scenario_text": q.scenario_text,
                "options": options_dict,
                "selected_option": ans.selected_option,
                "correct_option": q.correct_option,
                "is_correct": is_correct,
                "confidence": ans.confidence,
                "explanation": q.explanation,
                "distractor_feedback": distractor_dict.get(ans.selected_option, "") if not is_correct else ""
            })

        percentage = round((score / total_questions) * 100, 1) if total_questions > 0 else 0.0

        if percentage >= 80:
            grade_message = "Outstanding! Demonstrates strong mastery of official statistical standards."
        elif percentage >= 60:
            grade_message = "Good performance. Target specific procedural gaps identified below."
        elif percentage >= 40:
            grade_message = "Needs Improvement. Review the recommended iGOT training modules."
        else:
            grade_message = "Foundational reinforcement required. Prioritize the prescribed learning path."

        # Build Competency Breakdown
        competency_scores = []
        diagnosed_gaps = []

        for comp_id, stats in comp_stats.items():
            comp_obj = all_comps.get(comp_id)
            comp_name = comp_obj.competency_name if comp_obj else comp_id
            comp_domain = comp_obj.domain if comp_obj else "Functional"
            
            c_pct = round((stats["correct"] / stats["total"]) * 100, 1) if stats["total"] > 0 else 0.0
            
            if c_pct >= 80:
                status = "Strong"
            elif c_pct >= 60:
                status = "Proficient"
            elif c_pct >= 40:
                status = "Needs Attention"
            else:
                status = "Critical Gap"

            competency_scores.append(CompetencyScore(
                competency_id=comp_id,
                competency_name=comp_name,
                correct=stats["correct"],
                total=stats["total"],
                percentage=c_pct,
                status=status
            ))

            # Detect Gaps
            if c_pct < 70 or stats["wrong_high_conf"] > 0:
                if stats["wrong_high_conf"] > 0 or c_pct < 40:
                    severity = "Critical"
                elif c_pct < 60:
                    severity = "High"
                else:
                    severity = "Medium"

                mistake_reasons = [m["reason"] for m in stats["mistakes"]]
                diag_summary = " ".join(mistake_reasons[:2]) if mistake_reasons else f"Low accuracy in {comp_name} protocols."

                diagnosed_gaps.append(DiagnosedGap(
                    competency_id=comp_id,
                    competency_name=comp_name,
                    gap_nature=comp_domain,
                    severity=severity,
                    diagnostic_summary=diag_summary,
                    recommended_focus_area=f"Practical field rules & case studies for {comp_name}",
                    confidence_factor="High Misconception" if stats["wrong_high_conf"] > 0 else "Uncertain Application"
                ))

        return score, total_questions, percentage, grade_message, competency_scores, diagnosed_gaps, question_reviews

diagnostic_engine = DiagnosticEngine()
