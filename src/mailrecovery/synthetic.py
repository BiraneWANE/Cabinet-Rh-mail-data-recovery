"""Générateur de boîtes mail 100 % fictives, pour la démo et les tests.

Reproduit les pièges rencontrés sur les vraies archives : CV envoyés en Word
puis en PDF, même pièce jointe présente dans plusieurs boîtes, CV anonymisés,
quittances et RIB mêlés aux candidatures, mails sans pièce jointe, contrats et
factures sur plusieurs années. Aucun nom, aucune société, aucun numéro réel.
"""

from __future__ import annotations

import io
import random
from datetime import date, datetime, timedelta
from email.message import EmailMessage
from email.utils import format_datetime
from pathlib import Path

FIRST = ["Lina", "Hugo", "Inès", "Nathan", "Yasmine", "Lucas", "Awa", "Théo", "Sofia", "Malik",
         "Chloé", "Adam", "Nora", "Jules", "Maëlle", "Karim", "Emma", "Bilal", "Léa", "Omar"]
LAST = ["Martin", "Bernard", "Diallo", "Lefèvre", "Moreau", "Benali", "Garnier", "Traoré",
        "Faure", "Rousseau", "Mercier", "Nguyen", "Blanc", "Haddad", "Fontaine", "Kone"]
FIRMS = ["Cabinet Alpha Conseil", "Beta Audit", "Gamma Expertise", "Delta Compta",
         "Epsilon Fiduciaire", "Zeta Associés", "Eta Gestion", "Theta Partenaires"]
JOBS = ["Collaborateur comptable", "Chef de mission", "Gestionnaire de paie",
        "Assistant comptable", "Responsable paie", "Assistante de direction"]
SOFT = ["Sage", "Cegid", "ACD", "Pennylane", "Silae", "Quadra", "Excel"]
OWN = "cabinet-demo.fr"


def _phone(rng: random.Random) -> str:
    return "06 " + " ".join(f"{rng.randint(0, 99):02d}" for _ in range(4))


def _cv_text(rng, first, last, anonymous=False) -> str:
    job = rng.choice(JOBS)
    contact = "" if anonymous else f"{first.lower()}.{last.lower()}@example.com | {_phone(rng)}\n"
    who = f"{first}" if anonymous else f"{last.upper()} {first}"
    return (
        f"{who}\n{job}\n{contact}Paris\n\n"
        f"EXPÉRIENCE PROFESSIONNELLE\n{rng.randint(2015, 2023)} - aujourd'hui : {job}, "
        f"{rng.choice(FIRMS)}. Tenue de portefeuille, révision, bilans, déclarations fiscales.\n\n"
        f"FORMATION\nDCG, {rng.randint(2010, 2020)}\n\n"
        f"COMPÉTENCES\nLogiciels : {', '.join(rng.sample(SOFT, 3))}\nLangues : anglais courant\n"
    )


def _pdf(text: str) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    y = 800
    for line in text.splitlines():
        c.drawString(50, y, line[:95])
        y -= 16
    c.save()
    return buf.getvalue()


def _docx(text: str) -> bytes:
    import docx

    d = docx.Document()
    for line in text.splitlines():
        d.add_paragraph(line)
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


def _mail(to_dir: Path, idx: int, d: date, sender: str, subject: str, files: list[tuple[str, bytes]]):
    m = EmailMessage()
    m["From"], m["To"], m["Subject"] = sender, f"contact@{OWN}", subject
    m["Date"] = format_datetime(datetime(d.year, d.month, d.day, 10, 0))
    m.set_content("Bonjour,\nVeuillez trouver ci-joint le document.\nCordialement")
    for name, data in files:
        maintype, subtype = ("application", "pdf") if name.endswith(".pdf") else ("application", "octet-stream")
        m.add_attachment(data, maintype=maintype, subtype=subtype, filename=name)
    (to_dir / f"{idx:05d}.eml").write_bytes(bytes(m))


def generate(root: Path, n_mails: int = 300, seed: int = 42, n_boxes: int = 3) -> list[Path]:
    rng = random.Random(seed)
    boxes = [root / f"boite_{chr(65 + i)}" for i in range(n_boxes)]
    for b in boxes:
        b.mkdir(parents=True, exist_ok=True)
    shared: list[tuple[str, bytes]] = []   # pièces jointes recopiées d'une boîte à l'autre
    start = date(2012, 1, 1)

    for i in range(n_mails):
        box = rng.choice(boxes)
        d = start + timedelta(days=rng.randint(0, 5200))
        first, last = rng.choice(FIRST), rng.choice(LAST)
        kind = rng.choices(
            ["cv", "cv_word_pdf", "cv_anonyme", "contrat", "facture", "promesse", "offre",
             "quittance", "rib", "sans_pj", "partage"],
            weights=[30, 8, 6, 7, 9, 3, 4, 3, 2, 25, 6],
        )[0]
        sender = f"{first.lower()}.{last.lower()}@example.com"
        firm = rng.choice(FIRMS)

        if kind == "cv":
            files = [(f"CV {first} {last.upper()}.pdf", _pdf(_cv_text(rng, first, last)))]
        elif kind == "cv_word_pdf":   # même CV, deux formats : doublon de contenu
            t = _cv_text(rng, first, last)
            files = [(f"CV_{last}_{first}.docx", _docx(t)), (f"CV_{last}_{first}.pdf", _pdf(t))]
        elif kind == "cv_anonyme":
            files = [(f"CV anonyme {first}.pdf", _pdf(_cv_text(rng, first, last, anonymous=True)))]
        elif kind == "contrat":
            sender = "direction@example.org"
            files = [(f"Contrat {firm} {d.year}.pdf", _pdf(
                f"CONTRAT DE PRESTATION DE RECRUTEMENT\nEntre les soussignés : {firm} et le cabinet.\n"
                f"Il a été convenu ce qui suit. Objet du contrat : recrutement au succès.\n"
                f"Honoraires : pourcentage du salaire annuel brut. Fait en deux exemplaires, {d.year}."))]
        elif kind == "facture":
            sender = f"contact@{OWN}"
            files = [(f"Facture {firm} {d.year}-{rng.randint(1, 300):03d}.pdf", _pdf(
                f"FACTURE N {d.year}-{rng.randint(1, 300):03d}\nClient : {firm}\n"
                f"Montant HT : {rng.randint(3, 15)} 000 euros\nTVA non applicable, art. 293 B du CGI\n"
                f"Net à payer"))]
        elif kind == "promesse":
            files = [(f"Promesse embauche {firm}.pdf", _pdf(
                f"PROMESSE D'EMBAUCHE\n{firm}\nDate de prise de poste : {d.isoformat()}\n"
                f"Période d'essai : 4 mois\nPoste : {rng.choice(JOBS)}"))]
        elif kind == "offre":
            files = [(f"Fiche de poste {rng.choice(JOBS)}.pdf", _pdf(
                f"FICHE DE POSTE\nNous recherchons un(e) {rng.choice(JOBS)}.\nMissions principales : "
                f"tenue, révision, bilans.\nProfil recherché : DCG ou équivalent.\nType de contrat : CDI"))]
        elif kind == "quittance":
            files = [("quittance loyer.pdf", _pdf(f"QUITTANCE DE LOYER\nMois de {d.month}/{d.year}\n"
                                                  f"Locataire : {first} {last}"))]
        elif kind == "rib":
            files = [("RIB.pdf", _pdf("RELEVÉ D'IDENTITÉ BANCAIRE\nIBAN FR76 XXXX XXXX XXXX"))]
        elif kind == "partage" and shared:
            files = [rng.choice(shared)]
        else:
            files = []

        if files and rng.random() < 0.15:
            shared.append(files[0])
        _mail(box, i, d, sender, f"{kind} {first}", files)
    return boxes
