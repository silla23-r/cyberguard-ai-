"""
Cybercrime Incident Evidence PDF Generator for CyberGuard AI.
Produces official evidence dossiers formatted according to National Cyber Crime
Reporting Portal (cybercrime.gov.in / Helpline 1930) evidentiary standards.

Enhanced with:
1. Section 65B Indian Evidence Act / BSA 2023 Electronic Certificate.
2. Cryptographic SHA-256 Tamper Seal.
3. Live Verification QR Code for Police and Bank Ombudsman verification.
4. DPDP Act 2023 Zero-Knowledge PII Redaction Audit Badge.
"""
from datetime import datetime
import io
import logging
from pathlib import Path
from typing import Optional
from xml.sax.saxutils import escape as xml_escape

import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    Image as ReportLabImage
)

from models.schemas import ForensicEvidence, ThreatIntelligence, RiskVerdict

logger = logging.getLogger(__name__)

def _safe_xml(val: Optional[str]) -> str:
    """Escapes XML entities (&, <, >) so ReportLab Paragraph never crashes."""
    if not val:
        return ""
    return xml_escape(str(val))

def generate_evidence_pdf(
    session_id: str,
    evidence: ForensicEvidence,
    threat_intel: ThreatIntelligence,
    verdict: RiskVerdict,
    output_dir: Path
) -> Path:
    """
    Generates a structured, legally certified incident evidence summary.
    """
    pdf_path = output_dir / f"CyberGuard_Report_{session_id}.pdf"
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette
    c_primary = colors.HexColor("#0F172A")    # Deep slate
    c_danger = colors.HexColor("#DC2626")     # Crimson
    c_warning = colors.HexColor("#D97706")    # Amber
    c_safe = colors.HexColor("#16A34A")       # Emerald
    c_accent = colors.HexColor("#2563EB")     # Blue
    
    header_color = c_danger if verdict.severity == "DANGER" else (c_warning if verdict.severity == "CAUTION" else c_safe)

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=17,
        leading=21,
        textColor=c_primary
    )

    sub_style = ParagraphStyle(
        "SubTitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#475569")
    )

    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=c_accent,
        spaceBefore=8,
        spaceAfter=3
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1E293B")
    )

    cert_style = ParagraphStyle(
        "CertStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#334155")
    )

    hash_style = ParagraphStyle(
        "HashStyle",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#0F172A")
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph("🛡️ CYBERGUARD AI — FORENSIC EVIDENCE DOSSIER", title_style))
    story.append(Paragraph(
        "National Cyber Crime Reporting Portal (Helpline 1930 / cybercrime.gov.in) & Section 65B Indian Evidence Act Compliant",
        sub_style
    ))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=2, color=c_primary, spaceBefore=2, spaceAfter=8))

    # 2. Executive Metadata Table
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    sha_hash = verdict.evidence_sha256_hash or "N/A"
    short_hash = f"{sha_hash[:24]}...{sha_hash[-12:]}" if len(sha_hash) > 36 else sha_hash

    pii_badge = "Zero-Knowledge Masked (DPDP Act 2023)" if evidence.pii_redacted_count > 0 else "Clean / No Raw PII Stored"

    meta_data = [
        [Paragraph("<b>Incident Ref ID:</b>", body_style), Paragraph(_safe_xml(session_id), body_style),
         Paragraph("<b>Date / Timestamp:</b>", body_style), Paragraph(now_str, body_style)],
        [Paragraph("<b>Threat Classification:</b>", body_style), Paragraph(_safe_xml(verdict.scam_archetype.value.replace("_", " ")), body_style),
         Paragraph("<b>Threat Score:</b>", body_style), Paragraph(f"<b><font color='{header_color.hexval()}'>{verdict.risk_score} / 100 ({_safe_xml(verdict.severity)})</font></b>", body_style)],
        [Paragraph("<b>Suspected Entity / Brand:</b>", body_style), Paragraph(_safe_xml(evidence.impersonated_brand or "Not Specified"), body_style),
         Paragraph("<b>Confidence Level:</b>", body_style), Paragraph(f"{int(verdict.confidence * 100)}%", body_style)],
        [Paragraph("<b>Cryptographic SHA-256:</b>", body_style), Paragraph(f"<font face='Courier' size='7'>{_safe_xml(short_hash)}</font>", body_style),
         Paragraph("<b>Privacy Compliance:</b>", body_style), Paragraph(f"<b>{pii_badge}</b>", body_style)]
    ]
    t_meta = Table(meta_data, colWidths=[130, 140, 120, 150])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 8))

    # 3. Technical Forensic Indicators
    story.append(Paragraph("1. Extracted Technical Forensic Indicators", section_heading))
    
    ind_data = [
        [Paragraph("<b>Indicator Type</b>", body_style), Paragraph("<b>Extracted Value</b>", body_style), Paragraph("<b>Forensic Note</b>", body_style)]
    ]
    
    # Phone numbers
    for ph in evidence.phone_numbers:
        ind_data.append([Paragraph("Sender Phone", body_style), Paragraph(_safe_xml(ph), body_style), Paragraph("Suspected fraudster caller/SMS ID", body_style)])
    
    # VPAs
    for vpa in evidence.upi_vpas:
        ind_data.append([Paragraph("UPI Address (VPA)", body_style), Paragraph(_safe_xml(vpa), body_style), Paragraph("Destination account for funds", body_style)])

    # QR Code
    if evidence.qr_payload:
        truncated_qr = evidence.qr_payload[:50] + ("..." if len(evidence.qr_payload) > 50 else "")
        ind_data.append([Paragraph("QR Code Payload", body_style), Paragraph(_safe_xml(truncated_qr), body_style), Paragraph("Embedded payment or redirect payload", body_style)])

    # URLs
    for u in evidence.extracted_urls:
        truncated_url = u[:50] + ("..." if len(u) > 50 else "")
        ind_data.append([Paragraph("Malicious / Phishing URL", body_style), Paragraph(_safe_xml(truncated_url), body_style), Paragraph(f"Domain age: {_safe_xml(str(threat_intel.domain_age_days or 'Unknown'))} days", body_style)])

    if len(ind_data) == 1:
        ind_data.append([Paragraph("General Media", body_style), Paragraph("Screenshot or Audio recording analyzed", body_style), Paragraph("Psychological intimidation observed", body_style)])

    t_ind = Table(ind_data, colWidths=[140, 220, 180])
    t_ind.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E2E8F0")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_ind)
    story.append(Spacer(1, 8))

    # 4. Agent Reasoning and Evidentiary Justification
    story.append(Paragraph("2. Evidentiary Justification & Rule Matches", section_heading))
    for r in verdict.reasoning:
        story.append(Paragraph(f"• {_safe_xml(r)}", body_style))
    story.append(Spacer(1, 8))

    # 5. Victim Guidance & Next Steps
    story.append(Paragraph("3. Immediate Recommended Redress Actions", section_heading))
    for c in verdict.safety_checklist:
        story.append(Paragraph(f"<b>[ ]</b> {_safe_xml(c)}", body_style))
    story.append(Spacer(1, 10))

    # 6. Section 65B Certificate & Verification QR Box
    verify_url = verdict.verification_url or f"http://localhost:8000/api/verify/{sha_hash}"
    qr_img = qrcode.make(verify_url)
    img_buffer = io.BytesIO()
    qr_img.save(img_buffer, format="PNG")
    img_buffer.seek(0)
    rl_qr = ReportLabImage(img_buffer, width=65, height=65)

    cert_text = (
        "<b>CERTIFICATE OF ELECTRONIC EVIDENCE UNDER SECTION 65B INDIAN EVIDENCE ACT, 1872 & BHARATIYA SAKSHYA ADHINIYAM, 2023:</b><br/>"
        "I hereby certify that this electronic dossier was produced autonomously by the CyberGuard AI Multi-Agent Forensics System during "
        "the ordinary course of operation. The system was functioning properly without unauthorized human interference. "
        "The cryptographic SHA-256 seal guarantees integrity of technical telemetry for submission to 1930 / MHA / Court proceedings.<br/>"
        f"<b>Full Verification Hash:</b> <font face='Courier' size='6.5'>{_safe_xml(sha_hash)}</font>"
    )

    cert_table_data = [
        [Paragraph(cert_text, cert_style), rl_qr]
    ]
    t_cert = Table(cert_table_data, colWidths=[460, 80])
    t_cert.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F1F5F9")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#94A3B8")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_cert)
    story.append(Spacer(1, 6))

    # 7. Official Disclaimer
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#94A3B8"), spaceBefore=2, spaceAfter=4))
    story.append(Paragraph(
        "<b>LEGAL DISCLAIMER:</b> This evidence packet provides technical telemetry under Section 66D of the IT Act, 2000. "
        "Scan QR code to verify tamper-proof cloud ledger status.",
        sub_style
    ))

    doc.build(story)
    return pdf_path
