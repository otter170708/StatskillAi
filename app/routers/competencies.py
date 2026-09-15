from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Competency
from app.schemas import CompetencyResponse

router = APIRouter(prefix="/api/competencies", tags=["Competencies"])

@router.get("", response_model=List[CompetencyResponse])
def list_competencies(db: Session = Depends(get_db)):
    return db.query(Competency).all()

@router.get("/{competency_id}", response_model=CompetencyResponse)
def get_competency(competency_id: str, db: Session = Depends(get_db)):
    return db.query(Competency).filter(Competency.competency_id == competency_id).first()
