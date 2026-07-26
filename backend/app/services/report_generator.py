import json
import textwrap
from datetime import datetime
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import qrcode

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.core.config import (
    MEDICAL_DISCLAIMER,
    OUTPUT_DIR,
    REPORT_BASE_URL,
    REPORT_DIR,
    REPORT_METADATA_DIR,
)


PAGE_WIDTH, PAGE_HEIGHT = A4

PRIMARY_COLOR = colors.HexColor("#087F78")
PRIMARY_LIGHT = colors.HexColor("#E8F7F5")
DARK_COLOR = colors.HexColor("#17363A")
TEXT_COLOR = colors.HexColor("#465E62")
MUTED_COLOR = colors.HexColor("#728589")

DANGER_COLOR = colors.HexColor("#B4232B")
DANGER_BACKGROUND = colors.HexColor("#FFF0F1")

SUCCESS_COLOR = colors.HexColor("#17785A")
SUCCESS_BACKGROUND = colors.HexColor("#E8F8F1")

WARNING_COLOR = colors.HexColor("#8A6116")
WARNING_BACKGROUND = colors.HexColor("#FFF5DE")

BORDER_COLOR = colors.HexColor("#D5E5E5")
LIGHT_BACKGROUND = colors.HexColor("#F4F9F9")


def create_report_id() -> str:
    current_time = datetime.now()

    return (
        f"ORAL-{current_time.strftime('%Y%m%d')}-"
        f"{uuid4().hex[:8].upper()}"
    )


def normalize_prediction(prediction: str) -> str:
    return prediction.replace("_", " ").strip().upper()


def is_cancer_prediction(prediction: str) -> bool:
    normalized = normalize_prediction(prediction)

    return (
        "CANCER" in normalized
        and "NON" not in normalized
    )


def format_optional_value(value, default: str = "Not provided") -> str:
    if value is None:
        return default

    cleaned_value = str(value).strip()

    return cleaned_value or default


def create_qr_code(
    verification_url: str,
    report_id: str,
) -> Path:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )

    qr.add_data(verification_url)
    qr.make(fit=True)

    qr_image = qr.make_image(
        fill_color="black",
        back_color="white",
    )

    qr_path = REPORT_METADATA_DIR / f"{report_id}_qr.png"
    qr_image.save(qr_path)

    return qr_path


def save_uploaded_image(
    image_bytes: bytes,
    report_id: str,
) -> Path:
    image = PILImage.open(
        BytesIO(image_bytes)
    ).convert("RGB")

    image_path = REPORT_METADATA_DIR / f"{report_id}_original.jpg"

    image.save(
        image_path,
        format="JPEG",
        quality=92,
    )

    return image_path


def resolve_gradcam_path(
    gradcam_filename: str,
) -> Path:
    safe_filename = Path(gradcam_filename).name
    gradcam_path = OUTPUT_DIR / safe_filename

    if not gradcam_path.exists():
        raise FileNotFoundError(
            f"Grad-CAM image not found: {safe_filename}"
        )

    return gradcam_path


def create_styles():
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=21,
            leading=25,
            textColor=PRIMARY_COLOR,
            alignment=TA_LEFT,
            spaceAfter=4,
        )
    )

    styles.add(
        ParagraphStyle(
            name="ReportSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=MUTED_COLOR,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionTitle",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=DARK_COLOR,
            spaceBefore=5,
            spaceAfter=9,
        )
    )

    styles.add(
        ParagraphStyle(
            name="BodyTextCustom",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8.8,
            leading=13.2,
            textColor=TEXT_COLOR,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SmallText",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=7.3,
            leading=10.5,
            textColor=MUTED_COLOR,
        )
    )

    styles.add(
        ParagraphStyle(
            name="TableLabel",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=11,
            textColor=MUTED_COLOR,
        )
    )

    styles.add(
        ParagraphStyle(
            name="TableValue",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=DARK_COLOR,
        )
    )

    styles.add(
        ParagraphStyle(
            name="ResultTitle",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=20,
        )
    )

    styles.add(
        ParagraphStyle(
            name="CenteredSmall",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=7,
            leading=9,
            alignment=TA_CENTER,
            textColor=MUTED_COLOR,
        )
    )

    return styles


def draw_page_footer(
    canvas: Canvas,
    document,
):
    canvas.saveState()

    canvas.setStrokeColor(BORDER_COLOR)
    canvas.setLineWidth(0.5)

    canvas.line(
        18 * mm,
        15 * mm,
        PAGE_WIDTH - 18 * mm,
        15 * mm,
    )

    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(MUTED_COLOR)

    canvas.drawString(
        18 * mm,
        10 * mm,
        "OralScan AI - Preliminary Screening Support",
    )

    canvas.drawRightString(
        PAGE_WIDTH - 18 * mm,
        10 * mm,
        f"Page {document.page}",
    )

    canvas.restoreState()


def build_patient_table(
    patient: dict,
    styles,
):
    rows = [
        [
            Paragraph("Patient name", styles["TableLabel"]),
            Paragraph(
                format_optional_value(patient.get("name")),
                styles["TableValue"],
            ),
            Paragraph("Age", styles["TableLabel"]),
            Paragraph(
                format_optional_value(patient.get("age")),
                styles["TableValue"],
            ),
        ],
        [
            Paragraph("Gender", styles["TableLabel"]),
            Paragraph(
                format_optional_value(patient.get("gender")),
                styles["TableValue"],
            ),
            Paragraph("Phone", styles["TableLabel"]),
            Paragraph(
                format_optional_value(patient.get("phone")),
                styles["TableValue"],
            ),
        ],
        [
            Paragraph("Patient ID", styles["TableLabel"]),
            Paragraph(
                format_optional_value(patient.get("patient_id")),
                styles["TableValue"],
            ),
            Paragraph("Referred by", styles["TableLabel"]),
            Paragraph(
                format_optional_value(patient.get("referred_by")),
                styles["TableValue"],
            ),
        ],
    ]

    table = Table(
        rows,
        colWidths=[
            30 * mm,
            55 * mm,
            25 * mm,
            57 * mm,
        ],
    )

    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BACKGROUND),
            ("BOX", (0, 0), (-1, -1), 0.7, BORDER_COLOR),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, BORDER_COLOR),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])
    )

    return table


def build_image_comparison(
    original_image_path: Path,
    gradcam_image_path: Path,
    styles,
):
    original_image = Image(
        str(original_image_path),
        width=78 * mm,
        height=58 * mm,
        kind="proportional",
    )

    gradcam_image = Image(
        str(gradcam_image_path),
        width=78 * mm,
        height=58 * mm,
        kind="proportional",
    )

    table = Table(
        [
            [
                Paragraph(
                    "Uploaded oral image",
                    styles["TableValue"],
                ),
                Paragraph(
                    "Grad-CAM explanation",
                    styles["TableValue"],
                ),
            ],
            [
                original_image,
                gradcam_image,
            ],
            [
                Paragraph(
                    "Original screening image",
                    styles["CenteredSmall"],
                ),
                Paragraph(
                    "Highlighted regions influenced the AI output",
                    styles["CenteredSmall"],
                ),
            ],
        ],
        colWidths=[84 * mm, 84 * mm],
    )

    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BACKGROUND),
            ("BOX", (0, 0), (-1, -1), 0.7, BORDER_COLOR),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, BORDER_COLOR),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 1), (-1, 1), 7),
            ("BOTTOMPADDING", (0, 1), (-1, 1), 7),
            ("TOPPADDING", (0, 2), (-1, 2), 5),
            ("BOTTOMPADDING", (0, 2), (-1, 2), 7),
        ])
    )

    return table


def build_prediction_section(
    screening_result: dict,
    styles,
):
    prediction = normalize_prediction(
        screening_result.get(
            "prediction",
            "Unknown",
        )
    )

    cancer_prediction = is_cancer_prediction(
        prediction
    )

    if cancer_prediction:
        result_color = DANGER_COLOR
        result_background = DANGER_BACKGROUND
        recommendation = (
            "The AI model identified features associated with "
            "the cancer class. Prompt clinical examination by a "
            "qualified dentist, oral surgeon, or oral oncologist "
            "is strongly recommended."
        )
    else:
        result_color = SUCCESS_COLOR
        result_background = SUCCESS_BACKGROUND
        recommendation = (
            "The AI model classified the image as non-cancer. "
            "This does not rule out disease. Persistent ulcers, "
            "lesions, pain, bleeding, or other suspicious symptoms "
            "still require professional medical evaluation."
        )

    confidence_percent = screening_result.get(
        "confidence_percent",
        0,
    )

    confidence_level = screening_result.get(
        "confidence_level",
        "unknown",
    ).title()

    result_title_style = ParagraphStyle(
        name=f"ResultTitle{uuid4().hex}",
        parent=styles["ResultTitle"],
        textColor=result_color,
    )

    result_table = Table(
        [
            [
                Paragraph(
                    "AI screening result",
                    styles["TableLabel"],
                ),
                Paragraph(
                    "Confidence",
                    styles["TableLabel"],
                ),
                Paragraph(
                    "Confidence level",
                    styles["TableLabel"],
                ),
            ],
            [
                Paragraph(
                    prediction,
                    result_title_style,
                ),
                Paragraph(
                    f"{confidence_percent:.2f}%",
                    styles["ResultTitle"],
                ),
                Paragraph(
                    confidence_level,
                    styles["TableValue"],
                ),
            ],
        ],
        colWidths=[
            83 * mm,
            42 * mm,
            43 * mm,
        ],
    )

    result_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), result_background),
            ("BOX", (0, 0), (-1, -1), 0.8, result_color),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, result_color),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])
    )

    return result_table, recommendation


def build_probability_table(
    screening_result: dict,
    styles,
):
    probabilities = screening_result.get(
        "probabilities",
        {},
    )

    rows = [
        [
            Paragraph("Class", styles["TableLabel"]),
            Paragraph("Probability", styles["TableLabel"]),
        ]
    ]

    for class_name, probability in probabilities.items():
        rows.append([
            Paragraph(
                normalize_prediction(class_name),
                styles["TableValue"],
            ),
            Paragraph(
                f"{float(probability) * 100:.2f}%",
                styles["TableValue"],
            ),
        ])

    table = Table(
        rows,
        colWidths=[105 * mm, 63 * mm],
    )

    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_LIGHT),
            ("BOX", (0, 0), (-1, -1), 0.7, BORDER_COLOR),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, BORDER_COLOR),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ])
    )

    return table


def build_quality_table(
    screening_result: dict,
    styles,
):
    image_quality = screening_result.get(
        "image_quality",
        {},
    )

    issues = image_quality.get("issues", [])

    issue_text = (
        "<br/>".join(
            f"- {issue}"
            for issue in issues
        )
        if issues
        else "No major image-quality issue detected."
    )

    status = str(
        image_quality.get(
            "status",
            "unknown",
        )
    ).title()

    rows = [
        [
            Paragraph("Quality status", styles["TableLabel"]),
            Paragraph(status, styles["TableValue"]),
            Paragraph("Resolution", styles["TableLabel"]),
            Paragraph(
                (
                    f"{image_quality.get('width', 'N/A')} x "
                    f"{image_quality.get('height', 'N/A')}"
                ),
                styles["TableValue"],
            ),
        ],
        [
            Paragraph("Blur score", styles["TableLabel"]),
            Paragraph(
                str(
                    image_quality.get(
                        "blur_score",
                        "N/A",
                    )
                ),
                styles["TableValue"],
            ),
            Paragraph("Detected issues", styles["TableLabel"]),
            Paragraph(
                issue_text,
                styles["BodyTextCustom"],
            ),
        ],
    ]

    table = Table(
        rows,
        colWidths=[
            29 * mm,
            43 * mm,
            30 * mm,
            66 * mm,
        ],
    )

    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BACKGROUND),
            ("BOX", (0, 0), (-1, -1), 0.7, BORDER_COLOR),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, BORDER_COLOR),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])
    )

    return table


def build_signature_section(
    doctor_name: str,
    styles,
):
    doctor_display = format_optional_value(
        doctor_name,
        "Doctor / Medical Professional",
    )

    signature_table = Table(
        [
            [
                "",
                "",
            ],
            [
                Paragraph(
                    "______________________________",
                    styles["CenteredSmall"],
                ),
                Paragraph(
                    "______________________________",
                    styles["CenteredSmall"],
                ),
            ],
            [
                Paragraph(
                    doctor_display,
                    styles["CenteredSmall"],
                ),
                Paragraph(
                    "Patient / Attendant Signature",
                    styles["CenteredSmall"],
                ),
            ],
            [
                Paragraph(
                    "Doctor Signature and Stamp",
                    styles["CenteredSmall"],
                ),
                Paragraph(
                    "Acknowledgement",
                    styles["CenteredSmall"],
                ),
            ],
        ],
        colWidths=[84 * mm, 84 * mm],
        rowHeights=[
            15 * mm,
            5 * mm,
            5 * mm,
            5 * mm,
        ],
    )

    signature_table.setStyle(
        TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.7, BORDER_COLOR),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, BORDER_COLOR),
            ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BACKGROUND),
        ])
    )

    return signature_table


def generate_screening_report(
    patient: dict,
    screening_result: dict,
    original_image_bytes: bytes,
    doctor_name: str = "",
    hospital_name: str = "OralScan AI",
) -> dict:
    report_id = create_report_id()

    generated_at = datetime.now()
    generated_at_iso = generated_at.isoformat()

    verification_url = (
        f"{REPORT_BASE_URL}/api/v1/reports/"
        f"{report_id}/verify"
    )

    pdf_filename = f"{report_id}.pdf"
    pdf_path = REPORT_DIR / pdf_filename

    original_image_path = save_uploaded_image(
        image_bytes=original_image_bytes,
        report_id=report_id,
    )

    gradcam_data = screening_result.get(
        "gradcam",
        {},
    )

    gradcam_filename = gradcam_data.get(
        "filename"
    )

    if not gradcam_filename:
        raise ValueError(
            "Grad-CAM filename is missing from the screening result."
        )

    gradcam_path = resolve_gradcam_path(
        gradcam_filename
    )

    qr_path = create_qr_code(
        verification_url=verification_url,
        report_id=report_id,
    )

    metadata = {
        "report_id": report_id,
        "generated_at": generated_at_iso,
        "patient": patient,
        "prediction": screening_result.get(
            "prediction"
        ),
        "confidence_percent": screening_result.get(
            "confidence_percent"
        ),
        "verification_url": verification_url,
        "pdf_filename": pdf_filename,
    }

    metadata_path = (
        REPORT_METADATA_DIR
        / f"{report_id}.json"
    )

    metadata_path.write_text(
        json.dumps(
            metadata,
            indent=2,
        ),
        encoding="utf-8",
    )

    styles = create_styles()

    document = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=17 * mm,
        bottomMargin=22 * mm,
        title=f"OralScan AI Report - {report_id}",
        author="OralScan AI",
        subject="AI-Assisted Oral Cancer Screening Report",
    )

    story = []

    qr_image = Image(
        str(qr_path),
        width=28 * mm,
        height=28 * mm,
    )

    header_text = [
        Paragraph(
            "ORALSCAN AI",
            styles["ReportTitle"],
        ),
        Paragraph(
            "AI-Assisted Preliminary Oral Cancer Screening Report",
            styles["ReportSubtitle"],
        ),
        Spacer(1, 4),
        Paragraph(
            f"<b>Healthcare facility:</b> "
            f"{format_optional_value(hospital_name)}",
            styles["SmallText"],
        ),
    ]

    header_table = Table(
        [
            [
                header_text,
                [
                    Paragraph(
                        f"<b>Report ID:</b><br/>{report_id}",
                        styles["SmallText"],
                    ),
                    Spacer(1, 3),
                    Paragraph(
                        (
                            "<b>Generated:</b><br/>"
                            f"{generated_at.strftime('%d %B %Y, %I:%M %p')}"
                        ),
                        styles["SmallText"],
                    ),
                ],
                qr_image,
            ]
        ],
        colWidths=[
            91 * mm,
            47 * mm,
            30 * mm,
        ],
    )

    header_table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (2, 0), (2, 0), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ("LINEBELOW", (0, 0), (-1, -1), 1.1, PRIMARY_COLOR),
        ])
    )

    story.append(header_table)
    story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            "Patient information",
            styles["SectionTitle"],
        )
    )

    story.append(
        build_patient_table(
            patient,
            styles,
        )
    )

    story.append(Spacer(1, 13))

    story.append(
        Paragraph(
            "Clinical images and AI visualization",
            styles["SectionTitle"],
        )
    )

    story.append(
        build_image_comparison(
            original_image_path=original_image_path,
            gradcam_image_path=gradcam_path,
            styles=styles,
        )
    )

    story.append(Spacer(1, 13))

    story.append(
        Paragraph(
            "AI screening outcome",
            styles["SectionTitle"],
        )
    )

    prediction_table, recommendation = (
        build_prediction_section(
            screening_result,
            styles,
        )
    )

    story.append(prediction_table)
    story.append(Spacer(1, 10))

    story.append(
        Paragraph(
            "Class probabilities",
            styles["SectionTitle"],
        )
    )

    story.append(
        build_probability_table(
            screening_result,
            styles,
        )
    )

    story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            "Image-quality assessment",
            styles["SectionTitle"],
        )
    )

    story.append(
        build_quality_table(
            screening_result,
            styles,
        )
    )

    story.append(PageBreak())

    ai_message = screening_result.get(
        "message",
        (
            "The AI model analyzed the supplied image and "
            "generated the screening result shown in this report."
        ),
    )

    explanation_box = Table(
        [
            [
                Paragraph(
                    "<b>AI explanation</b>",
                    styles["TableValue"],
                )
            ],
            [
                Paragraph(
                    ai_message,
                    styles["BodyTextCustom"],
                )
            ],
        ],
        colWidths=[168 * mm],
    )

    explanation_box.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_LIGHT),
            ("BACKGROUND", (0, 1), (-1, 1), LIGHT_BACKGROUND),
            ("BOX", (0, 0), (-1, -1), 0.7, BORDER_COLOR),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ])
    )

    story.append(
        Paragraph(
            "AI explanation",
            styles["SectionTitle"],
        )
    )

    story.append(explanation_box)
    story.append(Spacer(1, 13))

    recommendation_box = Table(
        [
            [
                Paragraph(
                    "<b>Clinical recommendation</b>",
                    styles["TableValue"],
                )
            ],
            [
                Paragraph(
                    recommendation,
                    styles["BodyTextCustom"],
                )
            ],
        ],
        colWidths=[168 * mm],
    )

    recommendation_box.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), WARNING_BACKGROUND),
            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#FFFDF7")),
            ("BOX", (0, 0), (-1, -1), 0.7, WARNING_COLOR),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ])
    )

    story.append(
        Paragraph(
            "Recommendation",
            styles["SectionTitle"],
        )
    )

    story.append(recommendation_box)
    story.append(Spacer(1, 13))

    disclaimer_box = Table(
        [
            [
                Paragraph(
                    "<b>Medical disclaimer</b>",
                    styles["TableValue"],
                )
            ],
            [
                Paragraph(
                    screening_result.get(
                        "disclaimer",
                        MEDICAL_DISCLAIMER,
                    ),
                    styles["BodyTextCustom"],
                )
            ],
        ],
        colWidths=[168 * mm],
    )

    disclaimer_box.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F2F4F5")),
            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#FAFBFB")),
            ("BOX", (0, 0), (-1, -1), 0.7, BORDER_COLOR),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ])
    )

    story.append(
        Paragraph(
            "Important medical notice",
            styles["SectionTitle"],
        )
    )

    story.append(disclaimer_box)
    story.append(Spacer(1, 18))

    story.append(
        Paragraph(
            "Authorization and acknowledgement",
            styles["SectionTitle"],
        )
    )

    story.append(
        build_signature_section(
            doctor_name,
            styles,
        )
    )

    story.append(Spacer(1, 16))

    verification_table = Table(
        [
            [
                Image(
                    str(qr_path),
                    width=22 * mm,
                    height=22 * mm,
                ),
                Paragraph(
                    (
                        "<b>Report verification</b><br/>"
                        f"Scan the QR code or verify using report ID "
                        f"<b>{report_id}</b>.<br/>"
                        f"{verification_url}"
                    ),
                    styles["SmallText"],
                ),
            ]
        ],
        colWidths=[28 * mm, 140 * mm],
    )

    verification_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BACKGROUND),
            ("BOX", (0, 0), (-1, -1), 0.7, BORDER_COLOR),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])
    )

    story.append(verification_table)

    document.build(
        story,
        onFirstPage=draw_page_footer,
        onLaterPages=draw_page_footer,
    )

    return {
        "report_id": report_id,
        "generated_at": generated_at_iso,
        "filename": pdf_filename,
        "url": f"/reports/{pdf_filename}",
        "download_url": f"/reports/{pdf_filename}",
        "verification_url": verification_url,
    }