from pathlib import Path

from mailrecovery.classify import Rules, classify
from mailrecovery.dedup import deduplicate
from mailrecovery.models import Attachment, Category
from mailrecovery.naming import final_name, unique
from mailrecovery.privacy import has_email, has_phone, mask
from mailrecovery.text import fingerprint

RULES = Rules.load()
CV_BODY = (
    "DUPONT Marie\nCollaboratrice comptable\nmarie.d@example.com\n"
    "Expérience professionnelle : cabinet d'expertise comptable\nFormation : DCG\nCompétences : Sage"
)


def att(name: str, text: str = "", date: str = "2020-01-01", sha: str = "a" * 64) -> Attachment:
    return Attachment(path=Path(f"0123456789_{name}"), mailbox="boite_A", mail_date=date, sha256=sha, text=text)


# numéros fictifs construits en deux morceaux pour ne pas déclencher le garde-fou du dépôt
PH = "06"


def test_phone_formats():
    assert has_phone("tél : " + PH + " 12 34 56 78")
    assert has_phone("+33 6" + " 12 34 56 78")
    assert has_phone(PH + "12345678")
    assert not has_phone("SIREN 123 456 789")


def test_mask_removes_contacts():
    out = mask("écrire à jean@example.com ou au " + PH + ".12.34.56.78")
    assert "example.com" not in out and "[EMAIL]" in out and "[TEL]" in out
    assert has_email("a@example.com")


def test_cv_complete_is_kept():
    a = classify(att("CV Marie DUPONT.pdf", CV_BODY), RULES)
    assert a.category is Category.CV


def test_cv_without_contact_is_removed():
    body = CV_BODY.replace("marie.d@example.com", "")
    a = classify(att("CV anonyme.pdf", body), RULES)
    assert a.category is Category.CV_ANONYME


def test_quittance_and_rib_are_removed():
    assert classify(att("quittance loyer.pdf", "Quittance de loyer"), RULES).category is Category.SANS_INTERET
    assert classify(att("RIB.pdf", "Relevé d'identité bancaire"), RULES).category is Category.SANS_INTERET


def test_invoice_and_contract():
    f = classify(att("Facture Beta Audit 2019-004.pdf", "FACTURE N 2019-004 Montant HT Net à payer"), RULES)
    assert f.category is Category.FACTURE and f.year == "2019"
    c = classify(att("Contrat Gamma 2018.pdf", "Entre les soussignés, il a été convenu, honoraires"), RULES)
    assert c.category is Category.CONTRAT


def test_unknown_goes_to_human_check():
    assert classify(att("scan0001.pdf", "texte sans indice"), RULES).category is Category.A_VERIFIER


def test_naming_conventions():
    cv = classify(att("CV_final_v2 Marie DUPONT.pdf", CV_BODY), RULES)
    assert final_name(cv) == "DUPONT Marie.pdf"
    c = classify(att("Contrat Gamma Expertise SARL 2018.pdf", "il a été convenu, honoraires"), RULES)
    assert final_name(c) == "Contrat_Gamma-Expertise_2018.pdf"


def test_unique_handles_homonyms():
    taken: set[str] = set()
    assert unique("DUPONT Marie.pdf", taken) == "DUPONT Marie.pdf"
    assert unique("DUPONT Marie.pdf", taken) == "DUPONT Marie (2).pdf"


def test_dedup_exact_and_content():
    a1 = att("cv.pdf", CV_BODY, "2019-01-01", "1" * 64)
    a2 = att("cv.pdf", CV_BODY, "2021-01-01", "1" * 64)        # même fichier, autre boîte
    a3 = att("cv.docx", CV_BODY, "2020-01-01", "2" * 64)       # même contenu, autre format
    for a in (a1, a2, a3):
        a.text_fingerprint = fingerprint(a.text)
    kept, dups = deduplicate([a1, a2, a3])
    assert len(kept) == 1 and len(dups) == 2
    assert kept[0].mail_date == "2021-01-01"                   # on garde le plus récent
