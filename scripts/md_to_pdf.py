#!/usr/bin/env python3
"""Convert markdown to PDF using reportlab - simplified version"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted, Table, TableStyle
from reportlab.lib import colors
import re
import sys

def escape_xml(text):
    """Escape XML special characters"""
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text

def md_to_pdf(md_file, pdf_file):
    # Read markdown
    with open(md_file, 'r') as f:
        content = f.read()

    # Setup document
    doc = SimpleDocTemplate(
        pdf_file,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    # Styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='Title1',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=20,
        textColor=colors.HexColor('#1a5f2a')
    ))
    styles.add(ParagraphStyle(
        name='Title2',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=15,
        spaceAfter=10,
        textColor=colors.HexColor('#2d7a3e')
    ))
    styles.add(ParagraphStyle(
        name='Title3',
        parent=styles['Heading3'],
        fontSize=12,
        spaceBefore=10,
        spaceAfter=8
    ))
    styles.add(ParagraphStyle(
        name='CodeBlock',
        fontName='Courier',
        fontSize=7,
        leftIndent=10,
        spaceBefore=5,
        spaceAfter=5,
        backColor=colors.HexColor('#f5f5f5')
    ))
    styles.add(ParagraphStyle(
        name='Body',
        parent=styles['Normal'],
        fontSize=10,
        spaceBefore=3,
        spaceAfter=3
    ))

    story = []
    lines = content.split('\n')
    i = 0
    in_code_block = False
    code_lines = []
    in_table = False
    table_rows = []

    while i < len(lines):
        line = lines[i]

        # Code blocks
        if line.strip().startswith('```'):
            if in_code_block:
                # End code block
                code_text = '\n'.join(code_lines)
                code_text = escape_xml(code_text)
                story.append(Preformatted(code_text, styles['CodeBlock']))
                story.append(Spacer(1, 10))
                code_lines = []
                in_code_block = False
            else:
                in_code_block = True
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # Tables
        if '|' in line and line.strip().startswith('|'):
            cells = [c.strip() for c in line.split('|')[1:-1]]
            if cells and not all(set(c) <= set('-| ') for c in cells):
                # Escape cells
                cells = [escape_xml(c) for c in cells]
                table_rows.append(cells)
            i += 1
            continue
        elif table_rows:
            # End table
            if table_rows:
                t = Table(table_rows, repeatRows=1)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d7a3e')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f9f9f9')),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ]))
                story.append(t)
                story.append(Spacer(1, 10))
            table_rows = []

        # Headers
        if line.startswith('# '):
            text = escape_xml(line[2:])
            story.append(Paragraph(text, styles['Title1']))
        elif line.startswith('## '):
            text = escape_xml(line[3:])
            story.append(Paragraph(text, styles['Title2']))
        elif line.startswith('### '):
            text = escape_xml(line[4:])
            story.append(Paragraph(text, styles['Title3']))
        elif line.strip() == '---':
            story.append(Spacer(1, 15))
        elif line.strip():
            # Simple text - escape and format
            text = line
            # Remove markdown formatting for simplicity
            text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # Bold -> plain
            text = re.sub(r'\*(.+?)\*', r'\1', text)      # Italic -> plain
            text = re.sub(r'`(.+?)`', r'\1', text)        # Code -> plain
            text = escape_xml(text)
            story.append(Paragraph(text, styles['Body']))
        else:
            story.append(Spacer(1, 5))

        i += 1

    # Handle any remaining table
    if table_rows:
        t = Table(table_rows, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d7a3e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(t)

    doc.build(story)
    print(f"PDF created: {pdf_file}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python md_to_pdf.py input.md output.pdf")
        sys.exit(1)
    md_to_pdf(sys.argv[1], sys.argv[2])
