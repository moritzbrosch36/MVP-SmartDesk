# SmartDesk (DE)

**Intelligente Dokumentenverwaltung mit KI-gestützter Suche**

SmartDesk ist ein lokales Desktop-Tool, das private Dokumente (PDFs, Rechnungen, Verträge) 
automatisch analysiert, kategorisiert und durchsuchbar macht - komplett offline für 
maximalen Datenschutz.

---

## 🎯 Features

- ✅ **Automatische Rechnungserkennung** - Hybride Klassifizierung mit Keywords + KI
- ✅ **Intelligente Datenextraktion** - LLM-basierte Extraktion von Rechnungsdaten
(Betrag, Datum, Firma)
- ✅ **Natürlichsprachliche Suche** - Frag in deiner Sprache: "Zeig mir alle Rechnungen von Amazon"
- ✅ **100% Lokal** - Alle Daten bleiben auf deinem Rechner (Privacy by Design)
- ✅ **SQLite Datenbank** - Strukturierte Speicherung für schnelle Abfragen
- ✅ **Comprehensive Logging** - Performance-Tracking und Fehleranalyse

---

## 🚀 Technologie-Stack

- **Python 3.11+** - Hauptsprache
- **Ollama + Gemma 3:4b** - Lokales LLM für KI-Operationen
- **pdfplumber** - PDF-Text-Extraktion
- **SQLAlchemy + Flask** - Datenbank & Framework
- **Instructor + LiteLLM** - Strukturierte LLM-Outputs
- **Pydantic** - Datenvalidierung

---

## 📋 Voraussetzungen

### System
- **macOS** oder **Windows**
- **Python 3.11+**
- **Ollama** (für lokales LLM)

### Ollama installieren

**macOS:**
```bash
brew install ollama
ollama serve  # Startet Ollama-Server
```

**Windows:**
Download von [ollama.com](https://ollama.com/download)

### Gemma 3 Modell herunterladen
```bash
ollama pull gemma3:4b
```

---

## 🔧 Installation

### 1. Repository klonen
```bash
git clone https://github.com/moritzbrosch36/MVP-SmartDesk.git
cd smartdesk
```

### 2. Virtual Environment erstellen
```bash
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# oder
.venv\Scripts\activate  # Windows
```

### 3. Dependencies installieren
```bash
pip install -r requirements.txt
```


## 🎮 Verwendung

### Starten
```bash
python main.py
```

### Workflow

**1. Initial-Scan**
SmartDesk scannt automatisch `source/Test_Invoices/` nach PDFs:
```
--- SCHRITT 1: SCANNE ORDNER NACH NEUEN RECHNUNGEN ---
Gefunden: 5 PDF-Dateien.
[Extraktion] Analysiere rechnung_001.pdf mit Gemma3...
[Erfolg] Datenbank-Eintrag erstellt: INV-2024-001 (Amazon)
```

**2. Interaktiver Chat**
```
SMARTDESK KI-ASSISTENT BEREIT
==================================================

Deine Frage: Zeig mir alle Rechnungen
🤖 ASSISTANT:
Du hast 5 Rechnungen gespeichert:
- Amazon: 49.99 EUR
- Stadtwerke: 156.42 EUR
...

Deine Frage: Wie viel habe ich insgesamt bezahlt?
🤖 ASSISTANT:
Gesamtbetrag: 823.67 EUR

Deine Frage: exit
👋 Auf Wiedersehen!
```

---

## 📂 Projektstruktur

```
smartdesk/
├── main.py                      # Haupteinstiegspunkt
├── source/
│   ├── config/
│   │   └── rules.json           # Klassifizierungs-Regeln
│   ├── db/
│   │   ├── database.py          # Datenbank-Setup
│   │   └── db_schema.json       # Dynamisches Schema
│   ├── models/                  # SQLAlchemy Models
│   ├── repositories/            # Datenbank-Zugriff
│   ├── schemas/                 # Pydantic Schemas
│   ├── services/
│   │   ├── classifier.py        # PDF-Klassifizierung
│   │   ├── extractor.py         # Datenextraktion
│   │   ├── processor.py         # Import-Workflow
│   │   ├── scanner.py           # Datei-Scanner
│   │   └── manager.py           # Chat-Orchestrator
│   ├── utils/
│   │   └── logger.py            # Logging-System
│   └── Test_Invoices/           # Test-PDFs (nicht in Git)
├── logs/                        # Log-Dateien
├── requirements.txt             # Python Dependencies
└── README.md                    # Diese Datei
```

---

## 🔍 Logging

SmartDesk erstellt detaillierte Logs in `logs/smartdesk_YYYYMMDD.log`:

```log
2026-01-29 10:30:00 - smartdesk.system - INFO - SmartDesk wird gestartet...
2026-01-29 10:30:01 - smartdesk.agent - INFO - PDF-Scan abgeschlossen: 5 PDFs gefunden
2026-01-29 10:30:03 - smartdesk.classifier - INFO - Klassifizierung abgeschlossen: rechnung1.pdf | Ergebnis: True | Zeit: 2.1s
2026-01-29 10:30:06 - smartdesk.llm - INFO - LLM-Extraktion erfolgreich: rechnung1.pdf | Zeit: 2.8s
```

**Log-Kategorien:**
- `smartdesk.system` - System-Events (Startup, Shutdown)
- `smartdesk.agent` - Workflow und Scanner
- `smartdesk.classifier` - Dokumenten-Klassifizierung
- `smartdesk.pdf` - PDF-Verarbeitung
- `smartdesk.llm` - LLM-Operationen
- `smartdesk.database` - Datenbank-Queries

---

## ⚙️ Konfiguration

### Klassifizierungs-Regeln anpassen
Bearbeite `source/config/rules.json`:

```json
{
  "invoice_indicators": [
    "rechnung", "invoice", "quittung", "beleg",
    "rechnungsnummer", "ust-id", "faktura"
  ],
  "exclusion_keywords": [
    "angebot", "bestellung", "lieferschein", "entwurf"
  ]
}
```

### Datenbank-Schema erweitern
Bearbeite `source/db/db_schema.json` für zusätzliche Felder.

---

## 🐛 Bekannte Probleme & Lösungen

### Problem: PDFs werden nicht erkannt
**Ursachen:**
- PDF ist gescannt (Bild statt Text) → OCR nötig
- Komplexes Layout → pdfplumber kann Text nicht extrahieren

### Problem: LLM extrahiert keine Daten
**Lösung:** Prüfe Logs:
```bash
grep "Extraktion fehlgeschlagen" logs/smartdesk_*.log
```

### Problem: Ollama nicht erreichbar
**Lösung:**
```bash
ollama serve  # Starte Ollama-Server neu
ollama list   # Prüfe installierte Modelle
```

---

## 🚧 Roadmap (Post-MVP)

- [ ] **Weitere Dokumenttypen:** Verträge, Briefe, E-Mails
- [ ] **Vektordatenbank:** Semantische Suche mit Embeddings
- [ ] **GUI:** Moderne Desktop-Oberfläche (Tauri/Electron)
- [ ] **Quellenangaben:** Zeige welche Dokumente zur Antwort führten
- [ ] **Export-Funktionen:** CSV, Excel, PDF-Reports
- [ ] **Multi-User Support:** Mehrere Nutzer pro Instanz

---

## 📊 Performance

**Typische Verarbeitungszeiten (MacBook Pro M1):**
- PDF-Scan (100 Dateien): ~0.5s
- Klassifizierung pro PDF: ~2-3s
- Datenextraktion pro PDF: ~3-5s
- Chat-Antwort: ~2-4s

---

## 🔒 Datenschutz

SmartDesk verarbeitet **alle Daten lokal**:
- ✅ Keine Cloud-Verbindung
- ✅ Keine Daten-Upload
- ✅ Ollama läuft lokal auf deinem Rechner
- ✅ SQLite-Datenbank lokal gespeichert

---

## 🤝 Beitragen

Dieses Projekt ist ein MVP für akademische Zwecke. Feedback und Verbesserungsvorschläge sind willkommen!

---

## 📄 Lizenz

[MIT License](LICENSE) - Frei verwendbar für akademische und private Projekte.

---

## 👤 Autor

**Moritz Brosch**
- GitHub: [@moritzbrosch36](https://github.com/moritzbrosch36)
- Email: moritz.brosch23@googlemail.com

---

## 🙏 Danksagungen

- [Ollama](https://ollama.com/) - Lokales LLM-Framework
- [Instructor](https://github.com/jxnl/instructor) - Strukturierte LLM-Outputs
- [pdfplumber](https://github.com/jsvine/pdfplumber) - PDF-Extraktion

---

**Status:** 🚧 MVP (Minimum Viable Product) - Aktiv in Entwicklung

**Version:** 0.1.0 (Januar 2026)