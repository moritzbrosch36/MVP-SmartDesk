import hashlib
from source.db.database import get_model, db


def calculate_file_hash(file_path: str):
    """Erzeugt einen eindeutigen Fingerabdruck der Datei."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Datei stückweise lesen (effizient auch für große PDFs)
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def save_file(user_id: int, filename: str, file_path: str, file_type: str):
    FileData = get_model("FileData")

    # 1. Den Hash der physischen Datei berechnen
    current_hash = calculate_file_hash(file_path)

    # 2. In der DB nach dem Hash suchen (NICHT nach dem Pfad)
    file_entry = FileData.query.filter_by(file_hash=current_hash).first()

    if not file_entry:
        file_entry = FileData(
            user_id=user_id,
            filename=filename,
            file_path=file_path,
            file_type=file_type,
            file_hash=current_hash # speichert den Hash für die Zukunft
        )

        db.session.add(file_entry)
    else:
        # Datei existiert schon, hat sich aber verschoben
        # Wir aktualisieren den Pfad, damit unser System weiß, wo sie jetzt ist.
        file_entry.file_path = file_path
        file_entry.filename = filename

    db.session.commit()
    return file_entry
