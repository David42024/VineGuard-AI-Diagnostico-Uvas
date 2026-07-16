import sys
import json
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.security import get_current_user, TokenData
from backend.database.session import get_db
from backend.database.models import DiagnosticModel
from backend.repositories.diagnostic_repository import DiagnosticRepository
from backend.repositories.user_repository import UserRepository

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.services.prediction_service import DISEASE_CLASSES, DISEASE_INFO

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])

REPORTS_OUTPUT_DIR = settings.STORAGE_DIR / "generated_reports"


def _generate_docx_report(diagnosis: DiagnosticModel) -> Path:
    try:
        from docx import Document
        from docx.shared import Inches, Pt
    except ImportError:
        raise HTTPException(status_code=500, detail="python-docx no instalado")

    REPORTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    doc = Document()
    doc.add_heading("VineGuard AI - Reporte de Diagnóstico", 0)

    doc.add_heading("Información General", level=1)
    doc.add_paragraph(f"ID del Diagnóstico: {diagnosis.id}")
    doc.add_paragraph(f"Fecha: {diagnosis.timestamp}")
    doc.add_paragraph(f"Archivo: {diagnosis.filename or 'N/A'}")

    doc.add_heading("Resultado", level=1)
    doc.add_paragraph(f"Clase Predicha: {diagnosis.result}")
    doc.add_paragraph(f"Confianza: {diagnosis.confidence:.2%}" if diagnosis.confidence else "Confianza: N/A")
    doc.add_paragraph(f"Modelo: {diagnosis.model_used or 'N/A'}")

    disease_info = DISEASE_INFO.get(diagnosis.result, {})
    if disease_info:
        doc.add_heading("Detalles de la Enfermedad", level=1)
        doc.add_paragraph(f"Nombre (ES): {disease_info.get('display_name_es', 'N/A')}")
        doc.add_paragraph(f"Nombre (EN): {disease_info.get('display_name_en', 'N/A')}")
        doc.add_paragraph(f"Nombre Científico: {disease_info.get('scientific_name', 'N/A')}")
        doc.add_paragraph(f"Estado: {disease_info.get('health_status', 'N/A')}")
        doc.add_paragraph(f"Riesgo: {disease_info.get('risk_level', 'N/A')}")

    if diagnosis.probabilities:
        doc.add_heading("Probabilidades", level=1)
        try:
            probs = json.loads(diagnosis.probabilities)
            if isinstance(probs, dict):
                for cls_name in DISEASE_CLASSES:
                    prob = probs.get(cls_name, 0)
                    doc.add_paragraph(f"{cls_name}: {prob:.4f}")
            elif isinstance(probs, list):
                for i, cls_name in enumerate(DISEASE_CLASSES):
                    if i < len(probs):
                        doc.add_paragraph(f"{cls_name}: {probs[i]:.4f}")
        except (json.JSONDecodeError, TypeError):
            doc.add_paragraph(str(diagnosis.probabilities))

    filename = f"diagnostico_{diagnosis.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
    output_path = REPORTS_OUTPUT_DIR / filename
    doc.save(str(output_path))
    return output_path


@router.get("")
def list_reports(current_user: TokenData = Depends(get_current_user)):
    REPORTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    files = []
    for f in REPORTS_OUTPUT_DIR.iterdir():
        if f.is_file() and f.suffix in {".docx", ".pdf", ".csv"}:
            files.append({
                "id": f.stem,
                "filename": f.name,
                "size_bytes": f.stat().st_size,
                "created_at": datetime.fromtimestamp(f.stat().st_ctime).isoformat(),
            })
    return {"reports": sorted(files, key=lambda x: x["created_at"], reverse=True)}


@router.post("/diagnosis/{diagnosis_id}")
def generate_report(
    diagnosis_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    diag_repo = DiagnosticRepository(db)
    diag = diag_repo.get_by_id(diagnosis_id)
    if not diag:
        raise HTTPException(status_code=404, detail="Diagnóstico no encontrado")

    user_repo = UserRepository(db)
    user = user_repo.get_by_username(current_user.sub)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if current_user.role != "admin" and diag.user_id != user.id:
        raise HTTPException(status_code=403, detail="No autorizado")

    output_path = _generate_docx_report(diag)
    return {
        "message": "Reporte generado exitosamente",
        "filename": output_path.name,
        "path": str(output_path),
        "download_url": f"/api/v1/reports/{output_path.stem}/download",
    }


@router.get("/{report_id}/download")
def download_report(report_id: str, current_user: TokenData = Depends(get_current_user)):
    REPORTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for f in REPORTS_OUTPUT_DIR.iterdir():
        if f.stem == report_id and f.is_file():
            return FileResponse(
                path=str(f),
                filename=f.name,
                media_type="application/octet-stream",
            )
    raise HTTPException(status_code=404, detail="Reporte no encontrado")
