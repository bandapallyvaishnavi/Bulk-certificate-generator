
from sqlalchemy import Column, Integer, String
from app.database import Base


class CertificateJob(Base):
    __tablename__ = "certificate_jobs"

    id = Column(Integer, primary_key=True, index=True)
    total = Column(Integer, default=0)
    completed = Column(Integer, default=0)
    status = Column(String, default="pending")


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True)
    certificate_id = Column(
        String, unique=True, index=True, nullable=False
    )
    recipient_name = Column(String, nullable=False)
    recipient_email = Column(String, nullable=False)
    course = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    job_id = Column(Integer, nullable=True, index=True)
