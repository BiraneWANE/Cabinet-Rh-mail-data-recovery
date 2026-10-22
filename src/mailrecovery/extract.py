"""Étape 1 : extraction.

Une sauvegarde Outlook (.pst) est convertie en fichiers .eml avec `readpst`
(paquet pst-utils), puis chaque mail est ouvert pour en sortir les pièces jointes
et leurs métadonnées. Le .pst d'origine n'est jamais modifié : on lit, on copie.
"""

from __future__ import annotations

import email
import hashlib
import logging
import re
import shutil
import subprocess
from collections.abc import Iterator
from email import policy
from email.utils import parsedate_to_datetime
from pathlib import Path

from .models import Attachment

log = logging.getLogger(__name__)

SAFE_CHARS = re.compile(r"[^\w.\- ]+", re.UNICODE)
IGNORED_EXT = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ics", ".vcf", ".p7s"}


def pst_to_eml(pst: Path, out_dir: Path) -> Path:
    """Convertit un .pst en arborescence de .eml (lecture seule sur le .pst)."""
    if shutil.which("readpst") is None:
        raise RuntimeError("readpst introuvable : installer pst-utils (apt install pst-utils)")
    out_dir.mkdir(parents=True, exist_ok=True)
    # -e : un fichier .eml par mail, -D : inclut les éléments supprimés, -q : silencieux
    subprocess.run(["readpst", "-e", "-D", "-q", "-o", str(out_dir), str(pst)], check=True)
    return out_dir


def iter_eml(root: Path) -> Iterator[Path]:
    for p in sorted(root.rglob("*")):
        if p.is_file() and (p.suffix.lower() == ".eml" or p.suffix == ""):
            yield p


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _domain(addr: str) -> str:
    m = re.search(r"@([\w.\-]+)", addr or "")
    return m.group(1).lower() if m else ""


def extract_attachments(
    eml_root: Path, out_dir: Path, mailbox: str, own_domains: set[str] | None = None
) -> tuple[list[Attachment], int]:
    """Sort toutes les pièces jointes utiles des .eml d'une boîte.

    Les mails sans pièce jointe sont seulement comptés : ils iront dans
    « à supprimer » côté Outlook, une fois la sauvegarde vérifiée.
    """
    own_domains = own_domains or set()
    out_dir.mkdir(parents=True, exist_ok=True)
    found: list[Attachment] = []
    seen: set[str] = set()
    n_mails = n_without = 0

    for eml_path in iter_eml(eml_root):
        try:
            msg = email.message_from_bytes(eml_path.read_bytes(), policy=policy.default)
        except Exception as exc:  # mail corrompu : on trace et on continue
            log.warning("mail illisible %s : %s", eml_path.name, exc)
            continue
        n_mails += 1
        sender = str(msg.get("From", ""))
        direction = "envoye" if _domain(sender) in own_domains else "recu"
        try:
            date = parsedate_to_datetime(msg["Date"]).date().isoformat() if msg["Date"] else ""
        except (TypeError, ValueError):
            date = ""

        parts = [p for p in msg.iter_attachments() if p.get_filename()]
        if not parts:
            n_without += 1
            continue
        for part in parts:
            name = SAFE_CHARS.sub("_", part.get_filename()).strip() or "piece_jointe"
            if Path(name).suffix.lower() in IGNORED_EXT:
                continue  # logos de signature, invitations agenda...
            data = part.get_payload(decode=True) or b""
            if not data:
                continue
            digest = sha256_bytes(data)
            if digest in seen:      # même fichier joint dans plusieurs mails du fil
                continue
            seen.add(digest)
            target = out_dir / f"{digest[:10]}_{name}"
            target.write_bytes(data)
            found.append(
                Attachment(
                    path=target,
                    mailbox=mailbox,
                    mail_date=date,
                    mail_subject=str(msg.get("Subject", ""))[:200],
                    sender_domain=_domain(sender),
                    direction=direction,
                    sha256=digest,
                )
            )

    log.info(
        "%s : %d mails lus, %d sans pièce jointe, %d pièces jointes uniques",
        mailbox, n_mails, n_without, len(found),
    )
    return found, n_mails
