# Confidentialité et RGPD

Les archives traitées contiennent des données personnelles de milliers de candidats et de contacts clients. Le projet a été conçu pour que **ces données ne quittent jamais le poste de la cliente**, et pour que ce dépôt public n'en contienne aucune trace.

## Ce qui est publié

- le code du pipeline ;
- les règles de classification (mots‑clés métier, sans aucun nom) ;
- des chiffres **agrégés** (nombre de CV, de contrats, de doublons...) ;
- un générateur de données **entièrement fictives** (noms inventés, sociétés « Alpha », « Beta »..., adresses en `example.com`).

## Ce qui n'est jamais publié

CV, noms de candidats ou de clients, adresses mail, numéros de téléphone, contrats, factures, recensements, portefeuille clients, sauvegardes .pst, noms des titulaires des boîtes.

## Garde‑fous techniques

| Niveau | Mécanisme |
|---|---|
| 1. Fichiers | `.gitignore` exclut tous les formats de données |
| 2. Avant commit | hook `.githooks/pre-commit` qui lance `scripts/check_no_pii.py` |
| 3. Après push | GitHub Actions relance le même contrôle ; l'intégration échoue si une donnée apparaît |
| 4. Dans le pipeline | seul le domaine de l'expéditeur est conservé ; les boîtes sont pseudonymisées |
| 5. IA | texte masqué (`[EMAIL]`, `[TEL]`) avant tout appel à un modèle de langage |

## Principes RGPD appliqués

| Principe | Application |
|---|---|
| Minimisation | les CV anonymes, quittances, RIB, diplômes et documents privés sortent de la base |
| Finalité | la base sert uniquement à recontacter des candidats et clients du cabinet |
| Exactitude | en cas de versions multiples d'un CV, la plus récente est conservée |
| Sécurité | traitement local, sources conservées en lecture seule |
| Limitation de conservation | les documents retirés sont isolés pour que la cliente décide de leur suppression |

## Durée de conservation des CV

Recommandation de la CNIL : un CV peut rester dans la base active **2 ans après le dernier contact** avec le candidat (et non 2 ans après la date du CV). Au‑delà, il sort de la base active.

Application dans ce projet :

| Règle | Mise en œuvre |
|---|---|
| Point de départ des 2 ans | le dernier contact avec le candidat ; les candidats de la base ont été recontactés par mailing il y a moins de 2 ans |
| Preuve | la date d'envoi et la liste des destinataires du mailing sont conservées |
| Droit de refus | chaque nouveau message indique comment demander la suppression de son CV ; les demandes sont appliquées |
| Candidats sans contact depuis plus de 2 ans | leur CV ne sert plus au recrutement |
| Outil | le pipeline enregistre la date du mail d'origine de chaque CV (`mail_date`), ce qui permet de repérer les CV proches de la limite |

Prochaine étape (CRM de novembre 2026) : suivre pour chaque candidat la date du dernier contact et son accord, avec une alerte avant l'échéance des 2 ans.
