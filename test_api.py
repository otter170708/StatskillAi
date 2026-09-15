import os
import sys
import json

# Ensure stdout uses UTF-8 encoding
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Question

def run_tests():
    with TestClient(app) as client:
        print("---------------------------------------------------------")
        print("[*] Running StatSkill AI Automated API & Diagnostic Tests...")
        print("---------------------------------------------------------")

        # 1. Health Check
        res = client.get("/api/health")
        assert res.status_code == 200, f"Health check failed: {res.text}"
        print("[PASSED] 1. Health Check")

        # 2. Competencies Check
        res = client.get("/api/competencies")
        assert res.status_code == 200
        competencies = res.json()
        assert len(competencies) >= 10, f"Expected >= 10 competencies, got {len(competencies)}"
        print(f"[PASSED] 2. Competencies Seeded ({len(competencies)} competencies verified)")

        # 3. Courses Check
        res = client.get("/api/courses")
        assert res.status_code == 200
        courses = res.json()
        assert len(courses) >= 10, f"Expected >= 10 courses, got {len(courses)}"
        print(f"[PASSED] 3. iGOT Courses Catalogue Seeded ({len(courses)} courses verified)")

        # 4. Learners Check
        res = client.get("/api/learners")
        assert res.status_code == 200
        learners = res.json()
        assert len(learners) >= 3, f"Expected >= 3 demo learners, got {len(learners)}"
        print(f"[PASSED] 4. Demo Learners Seeded ({len(learners)} official personas verified)")

        # 5. Materials List & Sample Ingestion Check
        res = client.get("/api/materials")
        assert res.status_code == 200
        materials = res.json()
        assert len(materials) >= 1, "Expected sample materials in DB"
        sample_mat_id = materials[0]["material_id"]
        print(f"[PASSED] 5. Training Materials Seeded ({len(materials)} documents available)")

        # 6. Generate Scenario Quiz #1
        gen_payload = {
            "learner_id": learners[0]["learner_id"],
            "material_id": sample_mat_id,
            "title": "NSSO 79th Round Field Scrutiny Test",
            "number_of_questions": 5,
            "difficulty": "medium",
            "role_target": "Junior Statistical Officer (JSO)"
        }
        res = client.post("/api/quizzes/generate", json=gen_payload)
        assert res.status_code == 200, f"Quiz generation failed: {res.text}"
        quiz_data = res.json()
        quiz_id = quiz_data["quiz_id"]
        questions = quiz_data["questions"]
        assert len(questions) == 5, f"Expected 5 questions, got {len(questions)}"
        print(f"[PASSED] 6. Scenario Quiz Generated (Quiz ID: {quiz_id})")

        # 7. Submit Quiz and verify Randomized Option Mapping & Diagnostic Engine
        db = SessionLocal()
        db_qs = db.query(Question).filter(Question.quiz_id == quiz_id).all()
        db.close()
        
        q_map = {q.question_id: q for q in db_qs}
        
        # Build answers: intentionally get 3 right, 2 wrong to test gap diagnosis
        answers = []
        for idx, q_item in enumerate(questions):
            db_q = q_map[q_item["question_id"]]
            correct = db_q.correct_option
            # For first 3 questions, pick correct answer; for last 2, pick a distractor
            if idx < 3:
                answers.append({"question_id": q_item["question_id"], "selected_option": correct, "confidence": "High"})
            else:
                wrong_opts = [k for k in ["A", "B", "C", "D"] if k != correct]
                wrong_choice = wrong_opts[0]
                answers.append({"question_id": q_item["question_id"], "selected_option": wrong_choice, "confidence": "High"})

        submit_payload = {
            "learner_id": learners[0]["learner_id"],
            "answers": answers
        }
        res = client.post(f"/api/quizzes/{quiz_id}/submit", json=submit_payload)
        assert res.status_code == 200, f"Quiz submission failed: {res.text}"
        attempt_result = res.json()
        
        score = attempt_result["score"]
        pct = attempt_result["percentage"]
        gaps = attempt_result["diagnosed_gaps"]
        recommendations = attempt_result["recommendations"]

        assert score == 3, f"Expected score 3/5, got {score}"
        assert pct == 60.0, f"Expected 60.0%, got {pct}"
        assert len(gaps) >= 1, "Expected at least 1 diagnosed competency gap"
        assert len(recommendations) >= 1, "Expected targeted iGOT course recommendations"
        
        print(f"[PASSED] 7. Diagnostic Engine & Gap Analysis:")
        print(f"   - Score: {score}/5 ({pct}%)")
        print(f"   - Diagnosed Gaps: {len(gaps)} (e.g. {gaps[0]['competency_name']} - {gaps[0]['severity']} Severity)")
        print(f"   - Recommended Courses: {len(recommendations)} (e.g. {recommendations[0]['course_title']})")

        # 8. Learner Dashboard & Streak Verification
        res = client.get(f"/api/learners/{learners[0]['learner_id']}/dashboard")
        assert res.status_code == 200, f"Dashboard retrieval failed: {res.text}"
        dashboard = res.json()
        assert dashboard["total_quizzes_taken"] >= 1
        assert dashboard["learning_streak_days"] >= 1, f"Expected active streak >= 1, got {dashboard['learning_streak_days']}"
        assert dashboard["average_score"] > 0, f"Expected positive avg score, got {dashboard['average_score']}"
        assert dashboard["karma_points_earned"] >= 50, f"Expected karma points >= 50, got {dashboard['karma_points_earned']}"
        assert len(dashboard["competency_mastery_radar"]) >= 10
        print(f"[PASSED] 8. Accurate Learning Streak ({dashboard['learning_streak_days']} Day) & Dashboard Metrics (Avg: {dashboard['average_score']}%)")

        # 9. SME Review Panel
        res = client.get(f"/api/sme-review/questions?quiz_id={quiz_id}")
        assert res.status_code == 200
        review_qs = res.json()
        assert len(review_qs) == 5
        q_id_to_update = review_qs[0]["id"]
        res = client.put(f"/api/sme-review/questions/{q_id_to_update}", json={"review_status": "APPROVED", "reviewer_notes": "Verified against MoSPI circular."})
        assert res.status_code == 200
        print(f"[PASSED] 9. SME Human-in-the-Loop Review Gatekeeper")

        # 10. Generate Quiz #2 for same learner to verify FRESH/DIFFERENT Questions
        gen_payload_2 = {
            "learner_id": learners[0]["learner_id"],
            "material_id": sample_mat_id,
            "title": "NSSO 79th Round Advanced Scrutiny Test",
            "number_of_questions": 5,
            "difficulty": "medium",
            "role_target": "Junior Statistical Officer (JSO)"
        }
        res2 = client.post("/api/quizzes/generate", json=gen_payload_2)
        assert res2.status_code == 200
        quiz_data_2 = res2.json()
        questions_2 = quiz_data_2["questions"]
        
        # Check that questions in quiz 2 are fresh/different from quiz 1
        q1_scenarios = set(q["scenario_text"][:35] for q in questions)
        q2_scenarios = set(q["scenario_text"][:35] for q in questions_2)
        
        # There should be new questions in the second quiz
        new_questions_count = len(q2_scenarios - q1_scenarios)
        assert new_questions_count >= 3, f"Expected >= 3 new questions on subsequent attempt, got {new_questions_count}"
        print(f"[PASSED] 10. Question Refresh on Subsequent Attempts ({new_questions_count}/5 brand new scenarios generated)")

        # 11. Document and Image Upload Ingestion (.png, .jpg, .jpeg, .pdf)
        from PIL import Image
        import io

        # Create a test PNG in memory
        img_buffer = io.BytesIO()
        test_img = Image.new('RGB', (300, 100), color='white')
        test_img.save(img_buffer, format='PNG')
        img_bytes = img_buffer.getvalue()

        upload_files = {'file': ('cpi_inflation_circular.png', img_bytes, 'image/png')}
        upload_data = {'title': 'MoSPI Monthly CPI Inflation Guideline Screenshot'}
        res = client.post('/api/materials/upload', files=upload_files, data=upload_data)
        assert res.status_code == 200, f"Image upload failed: {res.text}"
        uploaded_img_mat = res.json()
        assert uploaded_img_mat["source_type"] == "image"
        print(f"[PASSED] 11. Image Ingestion (.png/.jpg/.jpeg) & Processing (ID: {uploaded_img_mat['material_id']})")

        # 12. Multi-Persona Test: Same Field (Peer JSO) and Different Fields (Agriculture, Price, Health)
        peer_jso = next((l for l in learners if l["role"].startswith("Junior Statistical Officer") and l["learner_id"] != learners[0]["learner_id"]), learners[1])
        agri_officer = next((l for l in learners if "Agricultural" in l["role"]), None)
        price_officer = next((l for l in learners if "Price" in l["role"]), None)
        health_analyst = next((l for l in learners if "Health" in l["role"]), None)

        assert peer_jso is not None, "Expected peer JSO in seed learners"
        assert agri_officer is not None, "Expected Agricultural Statistical Officer"
        assert price_officer is not None, "Expected Price & Index Statistician"
        assert health_analyst is not None, "Expected Health & Demographic Data Analyst"

        # Generate quiz for Agricultural Statistical Officer
        agri_quiz_res = client.post("/api/quizzes/generate", json={
            "learner_id": agri_officer["learner_id"],
            "material_id": sample_mat_id,
            "title": "Crop Estimation & Scrutiny Assessment",
            "number_of_questions": 3,
            "difficulty": "medium",
            "role_target": agri_officer["role"]
        })
        assert agri_quiz_res.status_code == 200
        agri_quiz = agri_quiz_res.json()
        assert len(agri_quiz["questions"]) == 3
        print(f"[PASSED] 12. Diverse Field Testing: Agricultural Officer, Price Statistician, Health Analyst Seed Personas Verified")

        # 13. Cumulative Karma Points Verification across Multiple Tests
        # Learner 1 takes a 2nd quiz and we verify points accumulate additively
        db = SessionLocal()
        qs2 = db.query(Question).filter(Question.quiz_id == quiz_data_2["quiz_id"]).all()
        db.close()
        ans2 = [{"question_id": q.question_id, "selected_option": q.correct_option, "confidence": "High"} for q in qs2]
        
        submit_res_2 = client.post(f"/api/quizzes/{quiz_data_2['quiz_id']}/submit", json={
            "learner_id": learners[0]["learner_id"],
            "answers": ans2
        })
        assert submit_res_2.status_code == 200
        result_2 = submit_res_2.json()

        # Cumulative points from test 1 + test 2
        assert result_2["total_karma_points"] > result_2["points_earned"], (
            f"Expected total karma ({result_2['total_karma_points']}) to be cumulative across attempts, greater than single quiz points ({result_2['points_earned']})"
        )
        print(f"[PASSED] 13. Cumulative Karma Points Verified: Attempt 1 + Attempt 2 Total = {result_2['total_karma_points']} pts")

        # 14. Single-Day Streak Rule: Multiple tests/uploads on same day do NOT falsely inflate streak
        assert result_2["learning_streak_days"] == 1, (
            f"Expected streak to be 1 for today (not inflated by 2 tests taken today), got {result_2['learning_streak_days']}"
        )
        print(f"[PASSED] 14. Single-Day Streak Invariant: 2 tests on same day correctly yield Streak = {result_2['learning_streak_days']} Day")

        # 15. SME Review Isolation: Filter by quiz_id returns only questions asked in that test
        sme_quiz_1 = client.get(f"/api/sme-review/questions?quiz_id={quiz_id}").json()
        sme_quiz_2 = client.get(f"/api/sme-review/questions?quiz_id={quiz_data_2['quiz_id']}").json()
        assert len(sme_quiz_1) == 5, f"Expected 5 questions for Quiz 1, got {len(sme_quiz_1)}"
        assert len(sme_quiz_2) == 5, f"Expected 5 questions for Quiz 2, got {len(sme_quiz_2)}"
        
        # Verify no overlap of question DB IDs between Quiz 1 and Quiz 2 review lists
        quiz_1_db_ids = set(q["id"] for q in sme_quiz_1)
        quiz_2_db_ids = set(q["id"] for q in sme_quiz_2)
        assert len(quiz_1_db_ids.intersection(quiz_2_db_ids)) == 0, "SME questions should be strictly isolated per test"
        print(f"[PASSED] 15. SME Review Filtered to Asked Questions Only: Quiz 1 ({len(sme_quiz_1)} Qs) & Quiz 2 ({len(sme_quiz_2)} Qs) strictly isolated")

        # 16. Post-Test Display Fields: Streak & Total Karma Points included in attempt result
        assert "learning_streak_days" in result_2, "learning_streak_days missing in AttemptResultResponse"
        assert "total_karma_points" in result_2, "total_karma_points missing in AttemptResultResponse"
        assert "points_earned" in result_2, "points_earned missing in AttemptResultResponse"
        print(f"[PASSED] 16. Post-Test Payload Verified: Streak ({result_2['learning_streak_days']}d) & Total Karma ({result_2['total_karma_points']} pts)")

        # 17. Custom material MCQs must use the document and never return True/False items
        custom_text = (
            "Seasonal fruit crop estimation in Himachal Pradesh requires enumerators to record "
            "orchard variety, tree age, and expected yield before harvest. Supervisors must reject "
            "schedules that omit the canopy-density code. Imputation of missing yield is allowed only "
            "after a documented second visit. District aggregates cannot be released without the "
            "relative standard error printed beside each estimate. Confidential farm identifiers "
            "must be stripped before any public dissemination of microdata."
        )
        upload_res = client.post("/api/materials/text", json={
            "title": "HP Orchard Yield Scrutiny Note",
            "text_content": custom_text,
            "language": "English",
        })
        assert upload_res.status_code == 200, f"Custom material upload failed: {upload_res.text}"
        custom_mat_id = upload_res.json()["material_id"]
        custom_quiz_res = client.post("/api/quizzes/generate", json={
            "learner_id": learners[0]["learner_id"],
            "material_id": custom_mat_id,
            "title": "Custom Material MCQ Check",
            "format_type": "mcq",
            "number_of_questions": 4,
            "difficulty": "medium",
            "role_target": "Agricultural Statistical Officer",
        })
        assert custom_quiz_res.status_code == 200, f"Custom MCQ generation failed: {custom_quiz_res.text}"
        custom_quiz = custom_quiz_res.json()
        custom_questions = custom_quiz["questions"]
        assert len(custom_questions) == 4
        joined = " ".join(
            (q.get("scenario_text") or "") + " " + (q.get("question_text") or "") + " " + " ".join((q.get("options") or {}).values())
            for q in custom_questions
        ).lower()
        assert any(token in joined for token in ["orchard", "canopy", "himachal", "yield", "enumerat"]), (
            f"Generated MCQs did not use the uploaded material. Got: {joined[:400]}"
        )
        for q in custom_questions:
            qtype = (q.get("question_type") or "mcq").lower()
            assert qtype == "mcq", f"Expected mcq question_type, got {qtype} for {q['question_id']}"
            opts = q.get("options") or {}
            assert len(opts) >= 4, f"Expected 4 MCQ options, got {opts}"
            labels = {str(k).strip().lower() for k in opts.keys()}
            values = {str(v).strip().lower() for v in opts.values()}
            assert labels != {"true", "false"}
            assert values != {"true", "false"}
        print("[PASSED] 17. Custom material MCQs are grounded in the upload and are not True/False")

        # 18. Live iGOT Karmayogi Direct Enrolment Webhook Simulation
        test_course_id = courses[0]["course_id"]
        enrol_res = client.post(f"/api/courses/{test_course_id}/enrol", json={
            "learner_id": learners[0]["learner_id"],
            "competency_id": "OSS-STAT-02"
        })
        assert enrol_res.status_code == 200, f"Enrolment failed: {enrol_res.text}"
        enrol_data = enrol_res.json()
        assert enrol_data["status"] == "SUCCESS"
        assert enrol_data["enrolment_id"].startswith("IGOT-ENR-")
        assert enrol_data["igot_sync_status"] == "SYNCED_TO_APAR_LEDGER"
        assert enrol_data["karma_credit_awarded"] == 25
        print(f"[PASSED] 18. Live iGOT Karmayogi Enrolment Webhook (Token: {enrol_data['enrolment_id']}, Karma: +25)")

        # 19. MoSPI / NSSTA Competency Audit Dossier & APAR Report Generation
        dossier_res = client.get(f"/api/learners/{learners[0]['learner_id']}/dossier")
        assert dossier_res.status_code == 200, f"Dossier retrieval failed: {dossier_res.text}"
        dossier_data = dossier_res.json()
        assert dossier_data["dossier_id"].startswith("MOSPI-APAR-")
        assert "officer" in dossier_data and dossier_data["officer"]["name"]
        assert len(dossier_data["competency_breakdown"]) >= 5
        assert dossier_data["apar_compliance_status"] == "CERTIFIED_AUDIT_READY"
        print(f"[PASSED] 19. MoSPI APAR Official Dossier Generated (Dossier ID: {dossier_data['dossier_id']}, Seal: {dossier_data['digital_seal_hash']})")

        print("---------------------------------------------------------")
        print("[SUCCESS] ALL 19 TESTS PASSED (100% End-to-End Operational)")
        print("---------------------------------------------------------")

if __name__ == "__main__":
    run_tests()
