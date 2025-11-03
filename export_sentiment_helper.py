"""
===========================================================
📦 export_sentiment_helper.py — Sentiment Export Utilities
===========================================================

Exports sentiment analysis results to CSV, Excel, PDF, and Word.
Compatible with Streamlit-based WhatsApp Chat Analyzer.

Dependencies:
    pip install reportlab pillow openpyxl python-docx
===========================================================
"""

import io
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from docx import Document
from datetime import datetime


# ==============================
# 1️⃣ CSV EXPORT
# ==============================
def export_sentiment_csv(sentiment_df: pd.DataFrame) -> bytes:
    csv_data = sentiment_df.to_csv(index=False).encode("utf-8")
    return csv_data


# ==============================
# 2️⃣ EXCEL EXPORT
# ==============================
def export_sentiment_excel(sentiment_summary: dict, sentiment_df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Summary Sheet
        summary_df = pd.DataFrame({
            "Metric": ["Positive", "Neutral", "Negative", "Average Sentiment"],
            "Value": [
                sentiment_summary["positive"],
                sentiment_summary["neutral"],
                sentiment_summary["negative"],
                round(sentiment_summary["avg_sentiment"], 3)
            ]
        })
        summary_df.to_excel(writer, index=False, sheet_name="Summary")

        # Messages Sheet
        sentiment_df.to_excel(writer, index=False, sheet_name="Messages")
    output.seek(0)
    return output.getvalue()


# ==============================
# 3️⃣ PDF EXPORT
# ==============================
def export_sentiment_pdf(selected_user: str, sentiment_summary: dict, sentiment_df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"<b>WhatsApp Sentiment Analysis Report</b>", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"<b>User:</b> {selected_user}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    data = [
        ["Sentiment", "Count"],
        ["😊 Positive", sentiment_summary["positive"]],
        ["😐 Neutral", sentiment_summary["neutral"]],
        ["😡 Negative", sentiment_summary["negative"]],
        ["📈 Avg Sentiment", round(sentiment_summary["avg_sentiment"], 3)],
    ]
    table = Table(data, colWidths=[150, 150])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 1, colors.grey)
    ]))
    elements.append(table)
    elements.append(Spacer(1, 18))

    elements.append(Paragraph("<b>Sample Messages:</b>", styles["Heading2"]))
    for _, row in sentiment_df.head(10).iterrows():
        msg = f"<b>{row['Sender']}</b>: {row['Message']} (<i>{row['Sentiment']}</i>, Polarity={row['Polarity']:.3f})"
        elements.append(Paragraph(msg, styles["Normal"]))
        elements.append(Spacer(1, 6))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


# ==============================
# 4️⃣ WORD EXPORT
# ==============================
def export_sentiment_word(selected_user: str, sentiment_summary: dict, sentiment_df: pd.DataFrame) -> bytes:
    doc = Document()
    doc.add_heading("WhatsApp Sentiment Analysis Report", level=1)
    doc.add_paragraph(f"User: {selected_user}")
    doc.add_paragraph(f"Date Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    doc.add_heading("Sentiment Summary", level=2)
    table = doc.add_table(rows=1, cols=2)
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'Sentiment'
    hdr_cells[1].text = 'Value'

    for key, value in sentiment_summary.items():
        row_cells = table.add_row().cells
        row_cells[0].text = key.capitalize()
        row_cells[1].text = str(round(value, 3) if isinstance(value, float) else value)

    doc.add_heading("Sample Messages", level=2)
    for _, row in sentiment_df.head(10).iterrows():
        doc.add_paragraph(f"{row['Sender']}: {row['Message']} "
                          f"({row['Sentiment']}, Polarity={row['Polarity']:.3f})")

    output = io.BytesIO()
    doc.save(output)
    output.seek(0)
    return output.getvalue()
