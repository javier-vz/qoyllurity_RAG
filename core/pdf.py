"""Fichas PDF generadas desde campos estructurados del grafo, sin LLM."""
import io
from datetime import date
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from core.spanish import polish_spanish


def _text(value):
    return escape(str(value)).replace('\n', '<br/>')


def create_pdf(card: dict) -> bytes:
    out = io.BytesIO()
    doc = SimpleDocTemplate(out, pagesize=A4, rightMargin=2*cm,
                             leftMargin=2*cm, topMargin=1.7*cm, bottomMargin=1.7*cm,
                             title=f"Ficha patrimonial - {card['name']}")
    base = getSampleStyleSheet()
    heading = ParagraphStyle('head', parent=base['Heading1'], fontName='Helvetica-Bold',
                             fontSize=20, leading=24, textColor=colors.HexColor('#263745'), spaceAfter=12)
    sub = ParagraphStyle('sub', parent=base['Heading2'], fontSize=11, leading=16,
                         textColor=colors.HexColor('#8c661c'), spaceBefore=8, spaceAfter=5)
    body = ParagraphStyle('body', parent=base['BodyText'], fontSize=9.3, leading=12.6,
                          textColor=colors.HexColor('#24313a'), spaceAfter=3)
    small = ParagraphStyle('small', parent=body, fontSize=8, leading=12,
                           textColor=colors.HexColor('#52616b'), wordWrap='CJK')
    story = [Paragraph('QOYLLUR RIT\'I | FICHA PATRIMONIAL', small), Spacer(1, 8),
             Paragraph(_text(card['name']), heading),
             Paragraph('Tipo: ' + _text(', '.join(card['kinds']) or 'Sin clasificar'), body),
             HRFlowable(width='100%', color=colors.HexColor('#d9c7a6'), thickness=1),
             Paragraph('Descripción documental', sub),
             Paragraph(_text(polish_spanish(card.get('description') or 'Sin descripción registrada.')), body)]
    if card['properties']:
        story.append(Paragraph('Propiedades documentadas', sub))
        for f in card['properties']:
            story.append(Paragraph('<b>' + _text(f['predicate_label']) + ':</b> ' + _text(f['value']), body))
    if card['relations']:
        story.append(Paragraph('Relaciones salientes', sub))
        for f in card['relations']:
            story.append(Paragraph(_text(f['predicate_label']) + ' → ' + _text(f['value']), body))
    if card['incoming']:
        story.append(Paragraph('Relaciones entrantes', sub))
        for f in card['incoming']:
            story.append(Paragraph(_text(f['subject_label']) + ' → ' + _text(f['predicate_label']) + ' → ' + _text(card['name']), body))
    story.extend([Spacer(1, 12), HRFlowable(width='100%', color=colors.HexColor('#c2cad0')),
                  Spacer(1, 6), Paragraph('Identificador RDF: ' + _text(card['uri']), small),
                  Paragraph('Fuente de datos: qoyllurity.ttl | Generada el ' + str(date.today()), small),
                  Paragraph('Registro automatizado a partir del RDF. Revisar la evidencia y la procedencia antes de usos académicos o institucionales.', small)])

    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#71808c'))
        canvas.drawString(2*cm, 1.15*cm, "Qoyllur Rit'i Explorer 3.0 | Datos del grafo patrimonial")
        canvas.drawRightString(A4[0]-2*cm, 1.15*cm, f'Página {document.page}')
        canvas.restoreState()
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return out.getvalue()
