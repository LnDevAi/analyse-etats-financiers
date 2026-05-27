"""
Génération de factures PDF au format UEMOA avec ReportLab.
"""
import io
from datetime import date
from decimal import Decimal
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT


BRAND_DARK = colors.HexColor("#1e293b")
BRAND_BLUE = colors.HexColor("#3b82f6")
GRAY_LIGHT = colors.HexColor("#f8fafc")
GRAY_BORDER = colors.HexColor("#e2e8f0")


def generate_invoice_pdf(
    invoice_number: str,
    issue_date: date,
    due_date: date,
    period_start: date,
    period_end: date,
    client_name: str,
    client_nif: str,
    client_address: str,
    plan_name: str,
    billing_cycle: str,
    amount_ht: Decimal,
    tax_rate: Decimal,
    tax_amount: Decimal,
    total_amount: Decimal,
    currency: str = "XOF",
) -> bytes:
    """Retourne les bytes du PDF de la facture."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    normal.fontName = "Helvetica"
    normal.fontSize = 9

    title_style = ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=22, textColor=BRAND_DARK)
    label_style = ParagraphStyle("label", fontName="Helvetica-Bold", fontSize=8, textColor=colors.HexColor("#64748b"))
    value_style = ParagraphStyle("value", fontName="Helvetica", fontSize=9, textColor=BRAND_DARK)
    bold_style = ParagraphStyle("bold", fontName="Helvetica-Bold", fontSize=9, textColor=BRAND_DARK)
    right_style = ParagraphStyle("right", fontName="Helvetica", fontSize=9, alignment=TA_RIGHT)
    right_bold = ParagraphStyle("right_bold", fontName="Helvetica-Bold", fontSize=10, alignment=TA_RIGHT, textColor=BRAND_DARK)

    story = []

    # ── En-tête ───────────────────────────────────────────────────────────────
    header_data = [
        [
            Paragraph("<b>E-DÉFENCE</b>", ParagraphStyle("brand", fontName="Helvetica-Bold", fontSize=16, textColor=BRAND_BLUE)),
            Paragraph(f"FACTURE", ParagraphStyle("inv_title", fontName="Helvetica-Bold", fontSize=20, textColor=BRAND_DARK, alignment=TA_RIGHT)),
        ],
        [
            Paragraph("Analyse Financière IA · Burkina Faso<br/>contact@edefence.tech", value_style),
            Paragraph(f"<b>{invoice_number}</b>", ParagraphStyle("inv_num", fontName="Helvetica-Bold", fontSize=12, textColor=BRAND_BLUE, alignment=TA_RIGHT)),
        ],
    ]
    header_table = Table(header_data, colWidths=[9 * cm, 8 * cm])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=2, color=BRAND_BLUE, spaceAfter=12))

    # ── Infos facture + client ────────────────────────────────────────────────
    meta_data = [
        [
            Table([
                [Paragraph("DATE D'ÉMISSION", label_style)],
                [Paragraph(issue_date.strftime("%d/%m/%Y"), bold_style)],
                [Spacer(1, 6)],
                [Paragraph("DATE D'ÉCHÉANCE", label_style)],
                [Paragraph(due_date.strftime("%d/%m/%Y"), ParagraphStyle("due", fontName="Helvetica-Bold", fontSize=9, textColor=colors.HexColor("#dc2626")))],
                [Spacer(1, 6)],
                [Paragraph("PÉRIODE", label_style)],
                [Paragraph(f"{period_start.strftime('%d/%m/%Y')} — {period_end.strftime('%d/%m/%Y')}", value_style)],
            ], colWidths=[8 * cm]),
            Table([
                [Paragraph("FACTURÉ À", label_style)],
                [Paragraph(f"<b>{client_name}</b>", bold_style)],
                [Paragraph(f"NIF/IFU : {client_nif or '—'}", value_style)],
                [Paragraph(client_address or "—", value_style)],
            ], colWidths=[8 * cm]),
        ]
    ]
    meta_table = Table(meta_data, colWidths=[9 * cm, 8 * cm])
    meta_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(meta_table)
    story.append(Spacer(1, 16))

    # ── Détail des prestations ────────────────────────────────────────────────
    cycle_label = "Mensuel" if billing_cycle == "MONTHLY" else "Annuel"
    detail_data = [
        [
            Paragraph("DÉSIGNATION", ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=8, textColor=colors.white)),
            Paragraph("QTÉ", ParagraphStyle("th_c", fontName="Helvetica-Bold", fontSize=8, textColor=colors.white, alignment=TA_CENTER)),
            Paragraph("P.U. HT", ParagraphStyle("th_r", fontName="Helvetica-Bold", fontSize=8, textColor=colors.white, alignment=TA_RIGHT)),
            Paragraph("TOTAL HT", ParagraphStyle("th_r", fontName="Helvetica-Bold", fontSize=8, textColor=colors.white, alignment=TA_RIGHT)),
        ],
        [
            Paragraph(f"Abonnement E-DÉFENCE — Plan {plan_name} ({cycle_label})", value_style),
            Paragraph("1", ParagraphStyle("c", fontSize=9, alignment=TA_CENTER)),
            Paragraph(f"{int(amount_ht):,} {currency}".replace(",", " "), right_style),
            Paragraph(f"{int(amount_ht):,} {currency}".replace(",", " "), right_style),
        ],
    ]
    detail_table = Table(detail_data, colWidths=[9.5 * cm, 1.5 * cm, 3 * cm, 3 * cm])
    detail_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_DARK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRAY_LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.5, GRAY_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(detail_table)
    story.append(Spacer(1, 10))

    # ── Totaux ────────────────────────────────────────────────────────────────
    totals_data = [
        ["", Paragraph("Montant HT", right_style), Paragraph(f"{int(amount_ht):,} {currency}".replace(",", " "), right_bold)],
        ["", Paragraph(f"TVA ({int(tax_rate)}%)", right_style), Paragraph(f"{int(tax_amount):,} {currency}".replace(",", " "), right_style)],
        ["", Paragraph("<b>TOTAL TTC</b>", ParagraphStyle("ttc", fontName="Helvetica-Bold", fontSize=10, alignment=TA_RIGHT, textColor=BRAND_DARK)),
         Paragraph(f"<b>{int(total_amount):,} {currency}</b>".replace(",", " "), ParagraphStyle("ttc_v", fontName="Helvetica-Bold", fontSize=11, alignment=TA_RIGHT, textColor=BRAND_BLUE))],
    ]
    totals_table = Table(totals_data, colWidths=[9.5 * cm, 4 * cm, 3.5 * cm])
    totals_table.setStyle(TableStyle([
        ("LINEABOVE", (1, 2), (-1, 2), 1.5, BRAND_BLUE),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (1, 2), (-1, 2), GRAY_LIGHT),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 24))

    # ── Pied de page ─────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY_BORDER, spaceBefore=8))
    story.append(Spacer(1, 6))
    footer_text = (
        "E-DÉFENCE SAS · Ouagadougou, Burkina Faso · RCCM BF-OUA-2024-B-12345 · NIF 12345678901 · "
        "Règlement : virement bancaire ou mobile money (Orange/Wave/Moov) · "
        "Tout retard de paiement entraîne des pénalités conformément à la réglementation UEMOA."
    )
    story.append(Paragraph(footer_text, ParagraphStyle("footer", fontName="Helvetica", fontSize=7, textColor=colors.HexColor("#94a3b8"), alignment=TA_CENTER)))

    doc.build(story)
    return buffer.getvalue()
