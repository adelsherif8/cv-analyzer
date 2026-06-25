import csv
import io
import os
from typing import List
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch

from app.schemas import AnalyzeResponse, JobProfile
from app.config import settings

def export_to_csv(results: AnalyzeResponse) -> str:
    """Export analysis results to CSV format"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    headers = [
        "candidate_id",
        "file_name", 
        "fit_score",
        "last_role",
        "years_experience",
        "why",
        "cv_summary",
        "suggested_roles",
        "red_flags"
    ]
    writer.writerow(headers)
    
    # Write data rows
    for result in results.results:
        row = [
            result.candidate_id,
            result.file_name,
            result.fit_score,
            getattr(result, 'last_role', 'Unknown'),
            getattr(result, 'years_experience', 0),
            "; ".join(result.why),
            result.cv_summary.replace('\n', ' ').replace('\r', ' '),
            "; ".join(result.suggested_roles),
            "; ".join(result.red_flags) if result.red_flags else ""
        ]
        writer.writerow(row)
    
    return output.getvalue()

def export_to_pdf(results: AnalyzeResponse, job_profile: JobProfile, role_id: str) -> str:
    """Export analysis results to PDF format"""
    
    # Create PDF file path
    pdf_filename = f"analysis_{role_id}.pdf"
    pdf_path = os.path.join(settings.DATA_DIR, pdf_filename)
    
    # Create PDF document
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    elements = []
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        textColor=colors.black
    )
    
    # Title
    title = Paragraph(f"CV Analysis Report - {job_profile.title}", title_style)
    elements.append(title)
    
    # Job profile summary
    job_summary = f"""
    <b>Job Description:</b><br/>
    {job_profile.description}<br/><br/>
    <b>Required Skills:</b><br/>
    {', '.join([f"{skill.name} ({skill.weight})" for skill in job_profile.required_skills])}<br/><br/>
    <b>Analysis Date:</b> {results.analyzed_at.strftime('%Y-%m-%d %H:%M')}<br/>
    <b>Total Candidates:</b> {len(results.results)}
    """
    
    job_para = Paragraph(job_summary, styles['Normal'])
    elements.append(job_para)
    elements.append(Spacer(1, 20))
    
    # Results table
    table_data = [
        ['Rank', 'Name', 'Score', 'Last Role', 'Years Exp', 'Summary']
    ]
    
    # Add top 10 candidates
    top_candidates = results.results[:10]
    
    for idx, result in enumerate(top_candidates, 1):
        # Truncate summary for table
        summary = result.cv_summary
        if len(summary) > 100:
            summary = summary[:97] + "..."
        
        last_role = getattr(result, 'last_role', 'Unknown')
        years_exp = getattr(result, 'years_experience', 0)
        
        row = [
            str(idx),
            result.file_name,
            str(result.fit_score),
            last_role,
            str(years_exp),
            summary
        ]
        table_data.append(row)
    
    # Create table
    table = Table(table_data, colWidths=[0.5*inch, 1.5*inch, 0.8*inch, 1.5*inch, 0.8*inch, 3*inch])
    
    # Style table
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    elements.append(table)
    
    # Add detailed breakdown for top 3
    if len(top_candidates) > 0:
        elements.append(Spacer(1, 30))
        
        detail_title = Paragraph("Top 3 Candidates - Detailed Analysis", styles['Heading2'])
        elements.append(detail_title)
        elements.append(Spacer(1, 20))
        
        for idx, result in enumerate(top_candidates[:3], 1):
            # Candidate header
            candidate_header = f"#{idx}. {result.file_name} (Score: {result.fit_score})"
            header_para = Paragraph(candidate_header, styles['Heading3'])
            elements.append(header_para)
            
            # Why section
            why_text = "<b>Rationale:</b><br/>" + "<br/>".join([f"• {reason}" for reason in result.why])
            why_para = Paragraph(why_text, styles['Normal'])
            elements.append(why_para)
            elements.append(Spacer(1, 10))
            
            # Suggested roles
            roles_text = f"<b>Suggested Roles:</b> {', '.join(result.suggested_roles)}"
            roles_para = Paragraph(roles_text, styles['Normal'])
            elements.append(roles_para)
            
            # Red flags if any
            if result.red_flags:
                flags_text = f"<b>Red Flags:</b> {', '.join(result.red_flags)}"
                flags_para = Paragraph(flags_text, styles['Normal'])
                elements.append(flags_para)
            
            elements.append(Spacer(1, 20))
    
    # Build PDF
    doc.build(elements)
    
    return pdf_path

def create_sample_export(role_id: str = "sample") -> str:
    """Create a sample export for testing"""
    from app.schemas import CandidateResult, AnalyzeResponse
    from datetime import datetime
    
    # Sample data
    sample_results = [
        CandidateResult(
            candidate_id="sample1",
            file_name="john_doe.pdf",
            fit_score=8.5,
            why=["Strong React and TypeScript skills", "5+ years experience", "Portfolio demonstrates impact"],
            cv_summary="Senior frontend developer with extensive React experience and proven track record in e-commerce.",
            suggested_roles=["Senior Frontend Developer", "React Developer"],
            red_flags=None,
            years_experience=5.5,
            last_role="Senior Developer"
        ),
        CandidateResult(
            candidate_id="sample2", 
            file_name="jane_smith.pdf",
            fit_score=6.2,
            why=["Good HTML/CSS foundation", "Limited React experience", "Strong design sense"],
            cv_summary="Frontend developer transitioning from design background with solid fundamentals.",
            suggested_roles=["Frontend Developer", "UI Developer"],
            red_flags=["Limited framework experience"],
            years_experience=2.0,
            last_role="UI Developer"
        )
    ]
    
    sample_response = AnalyzeResponse(
        role_id=role_id,
        results=sample_results,
        analyzed_at=datetime.now()
    )
    
    return export_to_csv(sample_response)
