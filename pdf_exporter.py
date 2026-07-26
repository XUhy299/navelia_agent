from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from config import PATIENT_FIELDS, PDF_PATH


TITLE = "\u667a\u80fd\u95ee\u8bca\u75c5\u4f8b\u8868"
FIELD_HEADER = "\u5b57\u6bb5"
VALUE_HEADER = "\u5185\u5bb9"
GENERATED_AT = "\u751f\u6210\u65f6\u95f4"


def register_chinese_font() -> str:
    candidates = [
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
        Path(r"C:\Windows\Fonts\simsun.ttc"),
    ]
    for font_path in candidates:
        if font_path.exists():
            pdfmetrics.registerFont(TTFont("ChineseFont", str(font_path)))
            return "ChineseFont"
    return "Helvetica"


def export_patient_record_to_pdf(record: dict[str, str], pdf_path: Path = PDF_PATH) -> Path:
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    font_name = register_chinese_font()

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=48,
        leftMargin=48,
        topMargin=48,
        bottomMargin=48,
    )

    styles = getSampleStyleSheet()
    styles["Title"].fontName = font_name
    styles["Normal"].fontName = font_name

    table_data = [[FIELD_HEADER, VALUE_HEADER]]
    for field in PATIENT_FIELDS:
        table_data.append([field, record.get(field, "")])
    table_data.append([GENERATED_AT, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

    table = Table(table_data, colWidths=[100, 360])
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF2F8")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    doc.build([Paragraph(TITLE, styles["Title"]), Spacer(1, 16), table])
    return pdf_path
