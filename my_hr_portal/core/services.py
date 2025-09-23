# core/services.py
from django.db import transaction
from django.utils import timezone
from django.core.files.base import ContentFile
from .models import Invoice, InvoiceLineItem
from .utils import generate_invoice_pdf # Assuming this utility exists

# A utility to get the next invoice number (This helper function is correct)
def get_next_invoice_number():
    last_invoice = Invoice.objects.order_by('id').last()
    if not last_invoice:
        return f"INV-{timezone.now().year}-0001"
    
    # This logic is safe for single-threaded generation but can have race conditions under high load.
    # For production, consider a database sequence or a more robust method.
    last_num_str = last_invoice.invoice_number.split('-')[-1]
    last_num = int(last_num_str)
    new_num = last_num + 1
    return f"INV-{timezone.now().year}-{new_num:04d}"


# The single, combined function
@transaction.atomic
def create_invoice_for_client(client_object, issue_date, due_date, line_items_data):
    """
    Creates an Invoice, its line items for any client model, and attaches a PDF.

    :param client_object: An instance of EmployerProfile or EORClientProfile.
    :param issue_date: The date the invoice is issued.
    :param due_date: The date the invoice is due.
    :param line_items_data: A list of dictionaries, where each dict contains
                            keys for 'description', 'quantity', 'unit_price'.
                            e.g., [{'description': 'Dev hours', 'quantity': 10, 'unit_price': 50.00}]
    :return: The newly created Invoice instance with the PDF attached.
    """
    if not line_items_data:
        raise ValueError("Cannot create an invoice with no line items.")

    # Step 1: Create the main Invoice object in the database.
    # It must be created first so it has an ID to link line items to.
    invoice = Invoice.objects.create(
        client=client_object,
        invoice_number=get_next_invoice_number(),
        issue_date=issue_date,
        due_date=due_date,
        status=Invoice.InvoiceStatus.PENDING
    )

    # Step 2: Create the associated InvoiceLineItem objects in the database.
    line_items_to_create = []
    for item_data in line_items_data:
        line_items_to_create.append(
            InvoiceLineItem(
                invoice=invoice,
                description=item_data['description'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price']
            )
        )
    
    InvoiceLineItem.objects.bulk_create(line_items_to_create)

    # --- MERGED LOGIC STARTS HERE ---
    
    # Step 3: Generate the PDF in memory.
    # We do this *after* creating the line items, so the PDF template can access
    # all the invoice data, including the total amount.
    pdf_in_memory = generate_invoice_pdf(invoice)
    
    # Step 4: Save the generated PDF to the Invoice model's FileField.
    # This also saves the file to your MEDIA_ROOT storage.
    file_name = f'Invoice-{invoice.invoice_number}.pdf'
    invoice.pdf_file.save(file_name, ContentFile(pdf_in_memory.getvalue()), save=True)
    
    # The `save=True` in the line above handles saving the invoice model instance again.
    
    # --- MERGED LOGIC ENDS HERE ---

    # Step 5: Return the complete invoice object.
    return invoice