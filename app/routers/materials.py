import uuid
import json
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Material
from app.schemas import MaterialUploadResponse, MaterialTextUploadRequest
from app.services.document_service import document_service

router = APIRouter(prefix="/api/materials", tags=["Materials"])

@router.get("")
def list_materials(db: Session = Depends(get_db)):
    materials = db.query(Material).all()
    results = []
    for m in materials:
        tags = json.loads(m.topic_tags) if m.topic_tags else []
        results.append({
            "material_id": m.material_id,
            "title": m.title,
            "source_type": m.source_type,
            "language": m.language,
            "character_count": len(m.extracted_text),
            "topic_tags": tags,
            "created_at": m.created_at
        })
    return results

@router.get("/{material_id}")
def get_material(material_id: str, db: Session = Depends(get_db)):
    m = db.query(Material).filter(Material.material_id == material_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Material not found")
    tags = json.loads(m.topic_tags) if m.topic_tags else []
    return {
        "material_id": m.material_id,
        "title": m.title,
        "source_type": m.source_type,
        "language": m.language,
        "extracted_text": m.extracted_text,
        "topic_tags": tags,
        "created_at": m.created_at
    }

@router.post("/upload", response_model=MaterialUploadResponse)
async def upload_material_file(
    file: UploadFile = File(...),
    title: str = Form(None),
    db: Session = Depends(get_db)
):
    material_id = f"MAT-{uuid.uuid4().hex[:8].upper()}"
    filename = file.filename or "uploaded_document"
    final_title = title or filename
    
    file_bytes = await file.read()
    
    lower_name = filename.lower()
    if lower_name.endswith(".pdf"):
        source_type = "pdf"
        extracted_text = document_service.extract_text_from_pdf(file_bytes)
    elif lower_name.endswith((".png", ".jpg", ".jpeg")):
        source_type = "image"
        extracted_text = document_service.extract_text_from_image(file_bytes, filename)
    else:
        source_type = "text"
        try:
            extracted_text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            extracted_text = file_bytes.decode("latin-1")

    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="Document appears to be empty or unreadable.")

    tags = document_service.extract_topics_and_tags(extracted_text)

    new_mat = Material(
        material_id=material_id,
        title=final_title,
        source_type=source_type,
        language="English",
        extracted_text=extracted_text,
        topic_tags=json.dumps(tags)
    )
    db.add(new_mat)
    db.commit()

    return MaterialUploadResponse(
        material_id=material_id,
        title=final_title,
        source_type=source_type,
        character_count=len(extracted_text),
        topic_tags=tags,
        status="ready",
        message="Material successfully uploaded and parsed for quiz generation."
    )

@router.post("/text", response_model=MaterialUploadResponse)
def upload_material_text(
    payload: MaterialTextUploadRequest,
    db: Session = Depends(get_db)
):
    material_id = f"MAT-{uuid.uuid4().hex[:8].upper()}"
    tags = document_service.extract_topics_and_tags(payload.text_content)

    new_mat = Material(
        material_id=material_id,
        title=payload.title,
        source_type="text",
        language=payload.language,
        extracted_text=payload.text_content,
        topic_tags=json.dumps(tags)
    )
    db.add(new_mat)
    db.commit()

    return MaterialUploadResponse(
        material_id=material_id,
        title=payload.title,
        source_type="text",
        character_count=len(payload.text_content),
        topic_tags=tags,
        status="ready",
        message="Text material successfully registered."
    )
