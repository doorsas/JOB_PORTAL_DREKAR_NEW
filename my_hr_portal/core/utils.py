from io import BytesIO
from django.template.loader import render_to_string
from weasyprint import HTML

def generate_invoice_pdf(invoice):
    """Renders an invoice HTML template to a PDF file in memory."""
    context = {'invoice': invoice}
    html_string = render_to_string('invoicing/invoice_template.html', context)
    
    pdf_file = HTML(string=html_string).write_pdf()
    return BytesIO(pdf_file)