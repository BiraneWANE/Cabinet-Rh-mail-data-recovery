"""Étape 5 : renommage normalisé, prêt pour la future base.

Conventions fixées par la cliente :
- CV : « NOM Prénom.pdf »
- contrats et conventions : « Contrat_<Société>_<Année>.pdf »
- factures et avoirs : « Facture_<Client>_<Année>.pdf »
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from .models import Attachment, Category

NOISE = {
    "cv", "curriculum", "vitae", "resume", "candidature", "final", "v2", "v3", "new",
    "version", "maj", "copie", "scan", "pdf", "docx", "doc", "de", "du", "mon",
    "contrat", "convention", "facture", "avoir", "fact", "cgv", "promesse", "embauche",
}
LEGAL = re.compile(r"\b(sarl|sas|sasu|sa|eurl|sci|selarl|scp)\b", re.I)
PREFIX = {
    Category.CONTRAT: "Contrat",
    Category.FACTURE: "Facture",
    Category.EMBAUCHE: "Embauche",
    Category.OFFRE: "Offre",
    Category.SUIVI: "Suivi",
    Category.TEST: "Test",
    Category.INTERNE: "Interne",
}


def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def _tokens(stem: str) -> list[str]:
    stem = re.sub(r"^[0-9a-f]{10}_", "", stem)          # préfixe technique d'extraction
    words = re.split(r"[\s_\-.()]+", stem)
    return [w for w in words if w and w.lower() not in NOISE and not w.isdigit()]


def person_name(att: Attachment) -> str:
    """Devine « NOM Prénom » depuis le nom de fichier, sinon depuis l'en-tête du CV."""
    toks = [t for t in _tokens(Path(att.path).stem) if t.isalpha()]
    if len(toks) < 2 and att.text:
        head = att.text.strip().splitlines()[:3]
        toks = [t for t in re.split(r"\s+", " ".join(head)) if t.isalpha()][:3]
    if len(toks) < 2:
        return ""
    # Le mot écrit en capitales est le nom ; sinon on suppose « Prénom Nom »
    upper = [t for t in toks[:3] if t.isupper() and len(t) > 1]
    if upper:
        last = upper[0]
        first = next((t for t in toks[:3] if t != last), "")
    else:
        first, last = toks[0], toks[1]
    return f"{last.upper()} {first.capitalize()}".strip()


def company_name(att: Attachment) -> str:
    toks = [t for t in _tokens(Path(att.path).stem) if not YEARLIKE.match(t)]
    name = LEGAL.sub("", " ".join(toks)).strip()
    return re.sub(r"\s+", "-", _strip_accents(name)).strip("-")[:40] or "Inconnu"


YEARLIKE = re.compile(r"^(19|20)\d{2}$")


def final_name(att: Attachment) -> str:
    if att.category is Category.CV:
        att.entity = person_name(att) or "A-RENOMMER"
        return f"{att.entity}.pdf"
    if att.category in PREFIX:
        att.entity = company_name(att)
        year = f"_{att.year}" if att.year else ""
        return f"{PREFIX[att.category]}_{att.entity}{year}.pdf"
    return Path(att.path).name.split("_", 1)[-1]


def unique(name: str, taken: set[str]) -> str:
    """Évite d'écraser un fichier : « NOM Prénom (2).pdf » en cas d'homonyme."""
    if name not in taken:
        taken.add(name)
        return name
    stem, ext = Path(name).stem, Path(name).suffix
    i = 2
    while f"{stem} ({i}){ext}" in taken:
        i += 1
    taken.add(f"{stem} ({i}){ext}")
    return f"{stem} ({i}){ext}"
