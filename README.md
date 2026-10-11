# Bulk Certificate Generator

A FastAPI-based application that generates PDF certificates in bulk, validates recipient data, tracks jobs, and supports certificate downloads and verification.

## Features
- Bulk PDF certificate generation
- Individual recipient validation and error handling
- Job status tracking: `completed`, `partially_completed`, and `failed`
- Individual PDF and ZIP downloads
- QR-code-based certificate verification
- SQLite database for job and certificate records

## Tech Stack
Python, FastAPI, Pydantic, SQLAlchemy, SQLite, ReportLab, qrcode, and pytest.

## Setup

Clone the repository and enter the project directory:

```bash
git clone https://github.com/bandapallyvaishnavi/Bulk-certificate-generator.git
cd Bulk-certificate-generator
```

Create and activate a virtual environment on Windows:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run the Application

```bash
uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000/docs** to access Swagger UI.

## Generate Certificates

Use `POST /certificates/bulk` with a JSON request:

```json
{
  "recipients": [
    {
      "name": "Sample User",
      "email": "sample@example.com",
      "course": "Python"
    }
  ]
}
```

The response includes the job ID, status, generated certificates, and any failures. Invalid recipients are reported without stopping the processing of other recipients.

## Retrieve Certificates

Use these endpoints in Swagger UI:

- `GET /jobs` — list jobs
- `GET /jobs/{job_id}` — view job details
- `GET /certificates/download/{certificate_id}` — download a PDF
- `GET /certificates/bulk-download/{job_id}` — download a ZIP archive
- `GET /verify/{certificate_id}` — verify a certificate

## Run Tests

```bash
python -m pytest -q
```

## Design Decisions

- **Pydantic:** validates each recipient separately.
- **SQLite and SQLAlchemy:** store job and certificate metadata.
- **ReportLab:** creates PDF certificates.
- **QR codes:** provide certificate verification links.
- **Per-recipient error handling:** allows valid recipients to succeed even when others fail.
- **Job statuses:** distinguish complete success, partial success, and total failure.

Generated PDFs, QR images, local databases, and the virtual environment are excluded from version control.
