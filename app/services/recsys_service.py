import json
from typing import List
from sqlalchemy.orm import Session
from app.models import Course
from app.schemas import DiagnosedGap, RecommendedCourse

class RecSysService:
    @staticmethod
    def get_recommendations_for_gaps(
        db: Session,
        gaps: List[DiagnosedGap],
        max_per_gap: int = 2
    ) -> List[RecommendedCourse]:
        
        all_courses = db.query(Course).all()
        recommended = []
        recommended_course_ids = set()

        for gap in gaps:
            gap_comp_id = gap.competency_id
            
            # Find courses mapped to this competency
            matched_courses = []
            for c in all_courses:
                try:
                    c_comps = json.loads(c.competency_ids) if isinstance(c.competency_ids, str) else c.competency_ids
                except Exception:
                    c_comps = []
                
                if gap_comp_id in c_comps:
                    matched_courses.append(c)

            for mc in matched_courses[:max_per_gap]:
                if mc.course_id not in recommended_course_ids:
                    recommended_course_ids.add(mc.course_id)
                    recommended.append(RecommendedCourse(
                        course_id=mc.course_id,
                        course_title=mc.course_name,
                        provider=mc.provider,
                        duration_minutes=mc.duration_minutes,
                        target_gap_addressed=gap.competency_name,
                        justification=f"Targeted to close {gap.severity.lower()}-severity gap in {gap.competency_name}. {mc.description}",
                        course_url=mc.course_url or f"https://igotkarmayogi.gov.in/course/{mc.course_id}"
                    ))

        # Fallback if no specific gap matched (e.g. perfect score or unmapped comp)
        if not recommended and all_courses:
            for c in all_courses[:2]:
                recommended.append(RecommendedCourse(
                    course_id=c.course_id,
                    course_title=c.course_name,
                    provider=c.provider,
                    duration_minutes=c.duration_minutes,
                    target_gap_addressed="Advanced Continuous Learning",
                    justification="Recommended for advanced continuous capacity building.",
                    course_url=c.course_url
                ))

        return recommended

recsys_service = RecSysService()
