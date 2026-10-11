
from pathlib import Path
from reportlab.pdfgen import canvas
import qrcode
import socket


PROJECT_DIR = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_DIR / "generated_certificates"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def generate_certificate(
    name: str,
    course: str,
    certificate_id: str
) -> str:
    
    file_path = OUTPUT_DIR / f"{certificate_id}.pdf"

    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    verification_url = f"http://{local_ip}:8000/verify/{certificate_id}"
    qr = qrcode.make(verification_url)
    qr_path = OUTPUT_DIR / f"{certificate_id}_qr.png"
    qr.save(qr_path)

    page_width = 842
    page_height = 595

    pdf = canvas.Canvas(
        str(file_path),
        pagesize=(page_width, page_height)
    )

    # Certificate border
    pdf.setLineWidth(3)
    pdf.rect(35, 35, page_width - 70, page_height - 70)

    # Certificate title
    pdf.setFont("Times-Bold", 30)
    pdf.drawCentredString(
        page_width / 2, 465,
        "CERTIFICATE OF COMPLETION"
    )

    # Introduction
    pdf.setFont("Times-Roman", 18)
    pdf.drawCentredString(
        page_width / 2, 400,
        "This certificate is proudly presented to"
    )

    # Recipient name
    pdf.setFont("Times-Bold", 28)
    pdf.drawCentredString(
        page_width / 2, 345,
        name
    )

    # Course name
    pdf.setFont("Times-Roman", 18)
    pdf.drawCentredString(
        page_width / 2, 290,
        f"For successfully completing {course}"
    )

    # Certificate ID
    pdf.setFont("Times-Roman", 12)
    pdf.drawCentredString(
        page_width / 2, 90,
        f"Certificate ID: {certificate_id}"
    )

    pdf.drawImage(
    qr_path,
    page_width - 150,
    60,
    width=70,
    height=70
)

    pdf.save()

    return str(file_path)