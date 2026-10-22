"""Ligne de commande.

    mailrecovery run --source boite_A=sauvegarde.pst --source boite_B=dossier_eml/ --out BASE/
    mailrecovery demo --out demo_output/
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from .classify import Rules
from .pipeline import Source, run


def _source(value: str) -> Source:
    name, _, path = value.partition("=")
    if not path:
        raise argparse.ArgumentTypeError("format attendu : nom_boite=chemin")
    return Source(name, Path(path))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="mailrecovery", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="traiter de vraies sauvegardes (.pst ou .eml)")
    p_run.add_argument("--source", type=_source, action="append", required=True)
    p_run.add_argument("--out", type=Path, required=True)
    p_run.add_argument("--rules", type=Path, default=None)
    p_run.add_argument("--own-domain", action="append", default=[],
                       help="domaine de l'entreprise, pour distinguer mails reçus et envoyés")
    p_run.add_argument("--no-convert", action="store_true")

    p_demo = sub.add_parser("demo", help="démonstration sur des données 100 %% fictives")
    p_demo.add_argument("--out", type=Path, default=Path("demo_output"))
    p_demo.add_argument("--n-mails", type=int, default=300)

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if args.cmd == "run":
        rules = Rules.load(args.rules) if args.rules else None
        stats = run(args.source, args.out, rules, set(args.own_domain), convert=not args.no_convert)
    else:
        from .synthetic import generate

        boxes = generate(args.out / "_sources_fictives", n_mails=args.n_mails)
        stats = run([Source(b.name, b) for b in boxes], args.out / "BASE_FUSIONNEE",
                    own_domains={"cabinet-demo.fr"})
    print(json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
