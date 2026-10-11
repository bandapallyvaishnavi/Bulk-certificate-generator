
import uuid
import re
from pathlib import Path

from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import Base , engine , SessionLocal
from app.models import Certificate, CertificateJob

from pydantic import ValidationError
from app.schemas import BulkCertificateRequest, RecipientInput

from app.services.certificate import generate_certificate

import zipfile
import tempfile

import io
import zipfile
from fastapi.responses import StreamingResponse



app = FastAPI(
    title="Bulk Certificate Generator",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1}
)
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@app.get("/jobs")
def list_jobs(db: Session = Depends(get_db)):
    jobs = db.query(CertificateJob).all()

    return [
        {
            "job_id": job.id,
            "total": job.total,
            "completed": job.completed,
            "status": job.status
        }
        for job in jobs
    ]


@app.get("/jobs/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = (
        db.query(CertificateJob)
        .filter(CertificateJob.id == job_id)
        .first()
    )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    return {
        "job_id": job.id,
        "total": job.total,
        "completed": job.completed,
        "status": job.status
    }





@app.post("/certificates/bulk")
def submit_bulk_request(
    request: BulkCertificateRequest,
    db: Session = Depends(get_db)
):
    job = CertificateJob(
        total=len(request.recipients),
        completed=0,
        status="pending"
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    generated_certificates = []
    failed_certificates = []

    
    for index, recipient_data in enumerate(request.recipients, start=1):
        try:
            recipient = RecipientInput.model_validate(recipient_data)
        except ValidationError as error:
            failed_certificates.append({
                "name": (
                    recipient_data.get("name", f"Recipient {index}")
                    if isinstance(recipient_data, dict)
                    else f"Recipient {index}"
                ),
                "error": error.errors(include_input=False)
            })
            continue

        certificate_id = f"CERT-{uuid.uuid4().hex[:12].upper()}"

        try:
            file_path = generate_certificate(
                name=recipient.name,
                course=recipient.course,
                certificate_id=certificate_id
            )

            db_certificate = Certificate(
                certificate_id=certificate_id,
                recipient_name=recipient.name,
                recipient_email=recipient.email,
                course=recipient.course,
                file_path=str(file_path),
                job_id=job.id
            )

            db.add(db_certificate)
            db.commit()
            db.refresh(db_certificate)

            generated_certificates.append({
                "name": recipient.name,
                "certificate_id": certificate_id,
                "file_path": str(file_path)
            })

            job.completed += 1
            db.commit()

        except Exception as error:
            db.rollback()

            failed_certificates.append({
                "name": recipient.name,
                "error": str(error)
            })

    if failed_certificates and generated_certificates:
        job.status = "partially_completed"
    elif failed_certificates:
        job.status = "failed"
    else:
        job.status = "completed"

    db.commit()
    db.refresh(job)

    return {
        "message": "Bulk certificate generation finished",
        "job_id": job.id,
        "total_recipients": job.total,
        "completed": job.completed,
        "status": job.status,
        "generated_certificates": generated_certificates,
        "failed_certificates": failed_certificates
    }



@app.get("/verify/{certificate_id}")
def verify_certificate(
    certificate_id: str,
    db: Session = Depends(get_db)
):
    if not re.fullmatch(r"CERT-[A-F0-9]{12}", certificate_id):
        return {
            "valid": False,
            "message": "Invalid certificate ID format"
        }

    certificate = db.query(Certificate).filter(
        Certificate.certificate_id == certificate_id
    ).first()

    if certificate is None:
        return {
            "valid": False,
            "certificate_id": certificate_id,
            "message": "Certificate not found"
        }

    certificate_path = Path(certificate.file_path)

    if not certificate_path.is_absolute():
        certificate_path = (
            Path(__file__).resolve().parent.parent / certificate_path
        )

    if not certificate_path.is_file():
        return {
            "valid": False,
            "certificate_id": certificate_id,
            "message": "Certificate record exists, but PDF file is missing"
        }

    return {
        "valid": True,
        "certificate_id": certificate.certificate_id,
        "recipient_name": certificate.recipient_name,
        "course": certificate.course,
        "message": "Certificate is valid"
    }


@app.get("/certificates/download/{certificate_id}")
def download_certificate(
    certificate_id: str,
    db: Session = Depends(get_db)
):
    if not re.fullmatch(r"CERT-[A-F0-9]{12}", certificate_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid certificate ID format"
        )

    certificate = db.query(Certificate).filter(
        Certificate.certificate_id == certificate_id
    ).first()

    if certificate is None:
        raise HTTPException(
            status_code=404,
            detail="Certificate not found"
        )

    certificate_path = Path(certificate.file_path)

    if not certificate_path.is_absolute():
        certificate_path = (
            Path(__file__).resolve().parent.parent / certificate_path
        )

    if not certificate_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Certificate PDF file not found"
        )

    return FileResponse(
        path=str(certificate_path),
        media_type="application/pdf",
        filename=f"{certificate_id}.pdf"
    )


@app.get("/certificates/bulk-download/{job_id}")
def download_bulk_certificates(job_id: int, db: Session = Depends(get_db)):
    job = db.query(CertificateJob).filter(
        CertificateJob.id == job_id
    ).first()

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    certificates = db.query(Certificate).filter(
        Certificate.job_id == job_id
    ).all()

    if not certificates:
        raise HTTPException(
            status_code=404,
            detail="No certificates found for this job"
        )

    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        added = 0

        for certificate in certificates:
            pdf_path = Path(certificate.file_path)

            if not pdf_path.is_absolute():
                pdf_path = Path(__file__).resolve().parent.parent / pdf_path

            if pdf_path.is_file():
                archive.write(
                    pdf_path,
                    arcname=f"{certificate.certificate_id}.pdf"
                )
                added += 1

    if added == 0:
        raise HTTPException(
            status_code=404,
            detail="No certificate PDF files found for this job"
        )

    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition":
                f'attachment; filename="certificates_job_{job_id}.zip"'
        }
    )

