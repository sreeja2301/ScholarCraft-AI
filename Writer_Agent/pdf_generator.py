from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from datetime import datetime
import re

def sanitize_filename(text):
    # Remove invalid filename characters
    return re.sub(r'[^a-zA-Z0-9_\- ]', '', text).replace(' ', '_')

def save_article_to_pdf(title, content, output_dir="outputs"):
    from pathlib import Path
    Path(output_dir).mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{sanitize_filename(title)[:40]}_{timestamp}.pdf"
    filepath = Path(output_dir) / filename

    doc = SimpleDocTemplate(str(filepath), pagesize=A4)
    styles = getSampleStyleSheet()
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#2E4053"),
        spaceAfter=20,
        spaceBefore=10,
        fontName="Helvetica-Bold"
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=12,
        leading=16,
        spaceAfter=12,
        fontName="Helvetica"
    )
    # Add header
    elements = [Paragraph(title, header_style), Spacer(1, 12)]
    # Split content into paragraphs
    for para in content.split('\n'):
        if para.strip():
            elements.append(Paragraph(para.strip(), body_style))
            elements.append(Spacer(1, 6))
    doc.build(elements)
    return str(filepath)