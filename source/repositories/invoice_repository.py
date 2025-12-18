from source.db.database import get_model, db
import hashlib
import json

def calculate_invoice_hash(data_dict: dict):
    """Erzeugt einen Hash aus den extrahierten Daten, um Inhaltsänderungen zu erkennen."""
    # Wir sortieren das Dictionary, damit der Hash immer gleich bleibt
    encoded_data = json.dumps(data_dict, sort_keys=True, default=str).encode()
    return hashlib.sha256(encoded_data).hexdigest()


def get_or_create_invoice(
        user_id: int,
        file_data_id: int,
        company: str,
        invoice_number: str,
        due_date,
        issue_date,
        amount: float,
        currency: str = "EUR",
        description: str = None
):
    Invoice = get_model("Invoice")

    # 1. Daten für Hash-Berechnung sammeln
    invoice_data = {
        "company": company,
        "invoice_number": invoice_number,
        "amount": amount,
        "currency": currency
    }
    current_hash = calculate_invoice_hash(invoice_data)

    # 2. Zuerst prüfen, ob die Rechnungsnummer bereits existiert
    invoice = Invoice.query.filter_by(invoice_number=invoice_number).first()

    if not invoice:
        # Rechnung ist neu
        invoice = Invoice(
            user_id=user_id,
            file_data_id=file_data_id,
            company=company,
            invoice_number=invoice_number,
            due_date=due_date,
            issue_date=issue_date,
            amount=amount,
            currency=currency,
            description=description,
            invoice_hash=current_hash
        )
        db.session.add(invoice)
    else:
        # Rechnung existiert bereits -> Daten aktualisieren (falls sich was geändert hat)
        invoice.company = company
        invoice.due_date = due_date
        invoice.issue_date = issue_date
        invoice.amount = amount
        invoice.description = description
        invoice.invoice_hash = current_hash
        # Wichtig: Wir verknüpfen sie mit der evtl. neuen file_data_id
        invoice.file_data_id = file_data_id

    db.session.commit()
    return invoice
