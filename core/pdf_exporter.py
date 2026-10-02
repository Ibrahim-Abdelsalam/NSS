from io import BytesIO
import pandas as pd
from typing import Dict, Any, List

def generate_full_report_pdf(results: Dict[str, Any], nurses_list: List[str]) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=0.5 * inch, leftMargin=0.5 * inch, topMargin=0.5 * inch, bottomMargin=0.5 * inch)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("CustomTitle", parent=styles["Heading1"], fontSize=20, textColor=colors.HexColor("#1a1a2e"), spaceAfter=12, alignment=1)
    heading_style = ParagraphStyle("CustomHeading", parent=styles["Heading2"], fontSize=14, textColor=colors.HexColor("#667eea"), spaceAfter=6, spaceBefore=12)

    story.append(Paragraph("NURSE SCHEDULING OPTIMIZATION REPORT", title_style))
    story.append(Paragraph(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("EXECUTIVE SUMMARY", heading_style))

    summary_data = [
        ["Model Type:", results['risk_metrics']['model_type']],
        ["Total Nurses:", str(len(nurses_list) if nurses_list else 0)],
        ["Planning Period:", f"{len(results['coverage_df']['day'].unique())} days"],
        ["Demand Scenarios:", str(results['risk_metrics']['num_scenarios'])]
    ]
    summary_table = Table(summary_data, colWidths=[2 * inch, 2.5 * inch])
    summary_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e6f2ff')), ('TEXTCOLOR', (0, 0), (-1, -1), colors.black), ('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, -1), 9), ('BOTTOMPADDING', (0, 0), (-1, -1), 6), ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)]))
    story.append(summary_table)
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("FINANCIAL SUMMARY", heading_style))

    financial_data = [
        ["Total Cost:", f"${results['cost_breakdown']['total_cost']:,.2f}"],
        ["Stage 1 Cost:", f"${results['cost_breakdown']['stage1_total']:,.2f}"],
        ["  Regular Wages:", f"${results['cost_breakdown']['stage1_regular_cost']:,.2f}"],
        ["  Overtime Wages:", f"${results['cost_breakdown']['stage1_overtime_cost']:,.2f}"],
        ["Stage 2 Recourse:", f"${results['cost_breakdown']['stage2_expected_cost']:,.2f}"],
        ["Cost per Nurse:", f"${results['cost_breakdown']['avg_cost_per_nurse']:,.2f}"]
    ]
    financial_table = Table(financial_data, colWidths=[2 * inch, 2.5 * inch])
    financial_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0fff4')), ('TEXTCOLOR', (0, 0), (-1, -1), colors.black), ('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, -1), 9), ('BOTTOMPADDING', (0, 0), (-1, -1), 6), ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)]))
    story.append(financial_table)
    
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("STAFFING & RISK SUMMARY", heading_style))
    
    staffing_data = [
        ["Total Regular Shifts:", str(int(results['cost_breakdown']['total_regular_shifts']))],
        ["Total Overtime Shifts:", str(int(results['cost_breakdown']['total_overtime_shifts']))],
        ["Total Shifts:", str(int(results['cost_breakdown']['total_regular_shifts'] + results['cost_breakdown']['total_overtime_shifts']))],
        ["Average Shortage:", f"{results['scenario_df']['shortage_shifts'].mean():.2f} shifts"],
        ["Maximum Shortage:", f"{results['scenario_df']['shortage_shifts'].max():.0f} shifts"]
    ]
    staffing_table = Table(staffing_data, colWidths=[2 * inch, 2.5 * inch])
    staffing_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#fff5f5')), ('TEXTCOLOR', (0, 0), (-1, -1), colors.black), ('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, -1), 9), ('BOTTOMPADDING', (0, 0), (-1, -1), 6), ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)]))
    story.append(staffing_table)

    doc.build(story)
    return pdf_buffer.getvalue()
