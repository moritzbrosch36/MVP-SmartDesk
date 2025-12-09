from source.db.database import get_model, db
# Platzhalter: from source.services.gemini_client import ask_llm
from datetime import datetime


def get_or_create_user(name: str):
    User = get_model("User")

    user = User.query.filter_by(name=name).first()

    if not user:
        user = User(name=name)
        db.session.add(user)
        db.session.commit()

    return user


def save_file(user_id: int, filename: str, file_path: str, file_type: str):
    FileData = get_model("FileData")

    file_entry = FileData(
        user_id=user_id,
        filename=filename,
        file_path=file_path,
        file_type=file_type,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    db.session.add(file_entry)
    db.session.commit()

    return file_entry


def save_invoice(
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
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    db.session.add(invoice)
    db.session.commit()

    return invoice


def collect_llm_context(user_id: int):
    FileData = get_model("FileData")
    Invoice = get_model("Invoice")

    files = FileData.query.filter_by(user_id=user_id).all()
    invoices = Invoice.query.filter_ba(user_id=user_id).all()

    context = {
        "files": [
            {
                "filename": f.filename,
                "type": f.file_type,
                "path": f.file_path
            } for f in files
        ],
        "invoices": [
            {
                "company": i.company,
                "invoice_number": i.invoice_number,
                "amount": i.amount,
                "currency": i.currency,
                "due_date": str(i.due_date),
                "description": i.description
            } for i in invoices
        ]
    }

    return context


def process_user_message(username: str, message: str) -> dict:
    """
    DAS IST DIE ZENTRALE BUSINESS-FUNKTION VON SMARTDESK.
    """

    # User laden und erzeugen
    user = get_or_create_user(username)

    # Kontext sammeln
    context = collect_llm_context(user.id)

    # LLM fragen
    answer = ask_llm(message, context)

    return {
        "user": user.name,
        "question": message,
        "context": context,
        "answer": answer
    }
