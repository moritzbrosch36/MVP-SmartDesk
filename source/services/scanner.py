import os

def get_pdf_files(directory: str):
    """Sucht rekursiv nach PDF-Dateien."""
    return [os.path.join(root, f)
            for root, _, files in os.walk(directory)
            for f in files if f.lower().endswith('.pdf')]