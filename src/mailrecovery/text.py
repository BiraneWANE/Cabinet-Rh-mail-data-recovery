"""Étape 2 : lecture du contenu des documents (PDF, Word, texte)."""

from __future__ import annotations

import hashlib
import logging
import re
import unicodedata
from pathlib import Path

log = logging.getLogger(__name__)

MAX_CHARS = 20_000  # le début du document suffit pour classer


def read_text(path: Path) -> str:
    ext = path.suffix.lower()
    try:
        if ext == ".pdf":
            from pypdf import PdfReader

            reader = PdfReader(str(path))
            out = []
            for page in reader.pages[:5]:
                out.append(page.extract_text() or "")
            return "\n".join(out)[:MAX_CHARS]
        if ext == ".docx":
            import docx

            d = docx.Document(str(path))
            return "\n".join(p.text for p in d.paragraphs)[:MAX_CHARS]
        if ext in {".txt", ".csv", ".md", ".rtf"}:
            return path.read_text(errors="ignore")[:MAX_CHARS]
    except Exception as exc:
        log.warning("lecture impossible %s : %s", path.name, exc)
    return ""  # .doc, .xlsx, scans : classés sur le nom de fichier


def normalize(text: str) -> str:
    """Minuscules, sans accents, espaces compactés : base des comparaisons."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text.lower()).strip()


def fingerprint(text: str) -> str:
    """Empreinte du contenu, indépendante de la mise en page et du format.

    Deux versions d'un même CV (Word et PDF, ou renvoyé deux fois) donnent la
    même empreinte, alors que leur empreinte binaire (sha256) diffère.
    """
    norm = re.sub(r"[^a-z0-9 ]", "", normalize(text))
    if len(norm) < 80:
        return ""  # trop court pour être fiable
    return hashlib.sha1(norm.encode()).hexdigest()
