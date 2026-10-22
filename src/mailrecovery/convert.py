"""Étape 6 : conversion en PDF.

Exigence de la cliente : aucun fichier Word dans la base finale. Les .doc,
.docx, .odt et .rtf sont convertis avec LibreOffice en mode sans interface.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)
TO_CONVERT = {".doc", ".docx", ".odt", ".rtf"}


def soffice() -> str | None:
    return shutil.which("soffice") or shutil.which("libreoffice")


def to_pdf(src: Path, out_dir: Path, timeout: int = 120) -> Path | None:
    """Convertit `src` en PDF dans `out_dir`. Renvoie le chemin du PDF, ou None."""
    if src.suffix.lower() == ".pdf":
        return src
    if src.suffix.lower() not in TO_CONVERT:
        return None
    exe = soffice()
    if exe is None:
        log.warning("LibreOffice absent : %s laissé tel quel", src.name)
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            [exe, "--headless", "--convert-to", "pdf", "--outdir", str(out_dir), str(src)],
            check=True, timeout=timeout, capture_output=True,
        )
    except (subprocess.SubprocessError, OSError) as exc:
        log.warning("conversion échouée %s : %s", src.name, exc)
        return None
    pdf = out_dir / f"{src.stem}.pdf"
    return pdf if pdf.exists() else None
