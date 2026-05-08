from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from flask import make_response
import io
from datetime import datetime


def generate_invoice(order):
    """Generate a PDF invoice for an order and return as Flask response."""

    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(buffer, pagesize=A4,
                               rightMargin=40, leftMargin=40,
                               topMargin=40,   bottomMargin=40)

    styles  = getSampleStyleSheet()
    content = []

    # ------ Title ------
    title_style = ParagraphStyle(
        'Title',
        parent    = styles['Heading1'],
        fontSize  = 24,
        textColor = colors.HexColor('#2c1810'),
        spaceAfter= 4
    )
    content.append(Paragraph('☕ CafeBliss', title_style))
    content.append(Paragraph('Your Favourite Cafe', styles['Normal']))
    content.append(Spacer(1, 0.2 * inch))

    # ------ Invoice Info ------
    content.append(Paragraph(f'<b>Invoice #INV-{order.id:04d}</b>', styles['Heading2']))
    content.append(Paragraph(
        f'Date: {order.created_at.strftime("%d %B %Y, %I:%M %p")}',
        styles['Normal']
    ))
    content.append(Paragraph(
        f'Customer: {order.customer.name}',
        styles['Normal']
    ))
    content.append(Paragraph(
        f'Email: {order.customer.email}',
        styles['Normal']
    ))
    content.append(Spacer(1, 0.3 * inch))

    # ------ Items Table ------
    table_data = [['#', 'Item', 'Qty', 'Unit Price', 'Total']]

    for i, item in enumerate(order.items, 1):
        table_data.append([
            str(i),
            item.menu_item.name,
            str(item.quantity),
            f'Rs.{item.price:.2f}',
            f'Rs.{item.price * item.quantity:.2f}'
        ])

    # Subtotal, Tax, Total rows
    subtotal = sum(i.price * i.quantity for i in order.items)
    tax      = round(subtotal * 0.05, 2)
    total    = round(subtotal + tax, 2)

    table_data.append(['', '', '', 'Subtotal:', f'Rs.{subtotal:.2f}'])
    table_data.append(['', '', '', 'Tax (5%):', f'Rs.{tax:.2f}'])
    table_data.append(['', '', '', 'TOTAL:',    f'Rs.{total:.2f}'])

    table = Table(table_data, colWidths=[0.4*inch, 3*inch, 0.6*inch, 1.2*inch, 1.2*inch])
    table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c1810')),
        ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
        ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0, 0), (-1, 0), 11),
        ('ALIGN',      (0, 0), (-1, 0), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        # Data rows
        ('FONTSIZE',   (0, 1), (-1, -4), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -4),
         [colors.white, colors.HexColor('#fdf6ec')]),
        ('GRID', (0, 0), (-1, -4), 0.5, colors.grey),
        # Summary rows
        ('FONTNAME',   (3, -3), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE',   (3, -1), (-1, -1), 12),
        ('TEXTCOLOR',  (3, -1), (-1, -1), colors.HexColor('#c8860a')),
        ('LINEABOVE',  (3, -3), (-1, -3), 1, colors.grey),
        ('ALIGN',      (3, -3), (-1, -1), 'RIGHT'),
        # General
        ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))

    content.append(table)
    content.append(Spacer(1, 0.3 * inch))

    # ------ Payment Info ------
    content.append(Paragraph(
        f'<b>Payment Method:</b> {order.payment_method.title()}',
        styles['Normal']
    ))
    content.append(Paragraph(
        f'<b>Payment Status:</b> {order.payment_status.title()}',
        styles['Normal']
    ))
    content.append(Spacer(1, 0.4 * inch))

    # ------ Footer ------
    footer_style = ParagraphStyle(
        'Footer',
        parent    = styles['Normal'],
        fontSize  = 9,
        textColor = colors.grey,
        alignment = 1  # Center
    )
    content.append(Paragraph(
        'Thank you for visiting CafeBliss! ☕',
        footer_style
    ))
    content.append(Paragraph(
        'For support: support@cafebliss.com | +91 99999 99999',
        footer_style
    ))

    # Build PDF
    doc.build(content)
    buffer.seek(0)

    # Return as downloadable file
    response = make_response(buffer.read())
    response.headers['Content-Type']        = 'application/pdf'
    response.headers['Content-Disposition'] = \
        f'attachment; filename=CafeBliss_Invoice_{order.id}.pdf'

    return response