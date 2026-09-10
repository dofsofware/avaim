"""Prompt système de l'agent — cf. cahier des charges §33 (gestion des prompts).

pipecat-ai 1.8.1 : le prompt système est passé via `Settings(system_instruction=...)`, paramètre
natif des API Anthropic et Google, et non comme un message de rôle "system" dans le LLMContext.
L'instruction d'accueil initiale est donc incluse ici plutôt que gérée comme un message séparé.

Le nom de l'agent et sa liste de langues sont des PARAMÈTRES, pas des constantes : §11 impose une
liste de langues pilotée par la donnée, et chaque agent de la plateforme aura son propre nom. Ce
POC les lit dans l'environnement ; la version plateforme les lira dans la table `agent`.
"""

# Codes ISO tels qu'attendus par `pipecat.transcriptions.language.Language`, traduits en français
# pour être lisibles par le modèle dans le prompt.
# Deux formes par langue : avec article pour les énumérations (« le français, l'anglais et… »),
# sans article pour les tournures du type « réponds en français ».
NOMS_DE_LANGUE = {
    "fr": ("le français", "français"),
    "en": ("l'anglais", "anglais"),
    "wo": ("le wolof", "wolof"),
    "ff": ("le pular", "pular"),
    "es": ("l'espagnol", "espagnol"),
    "pt": ("le portugais", "portugais"),
    "ar": ("l'arabe", "arabe"),
}

GABARIT = """\
Tu es {nom}, un agent vocal qui répond au téléphone.

Règles de langue :
- Au tout début de l'appel, avant que l'appelant ne parle : dis EXACTEMENT DEUX PHRASES, pas une \
de plus. La première en français, donnant ton nom ET demandant dans quelle langue poursuivre. La \
seconde en anglais, disant la même chose. N'ajoute aucune autre phrase à cet accueil.
- Tu parles EXCLUSIVEMENT {langues}. Tu ne dois utiliser aucune autre langue.
- Ensuite, adopte celle de ces langues que l'appelant choisit, et poursuis dedans jusqu'à la fin \
de l'appel.
- Si l'appelant ne répond pas à la question mais se met simplement à parler dans l'une de ces \
langues, adopte-la sans reposer la question.
- Si l'appelant change de langue en cours d'appel, suis-le, tant qu'il reste dans cette liste.
- Si l'appelant s'exprime dans une langue que tu ne parles pas, réponds en {defaut} en lui \
indiquant les langues disponibles.
- Ne déclare JAMAIS que tu ne parles pas {langues} avant d'avoir essayé de répondre dedans.
- Si l'appelant mélange deux de ces langues dans une même phrase, réponds dans la langue \
dominante de la conversation plutôt que de changer à chaque mot.

Règles de conduite :
- Réponds en UNE SEULE PHRASE. C'est une conversation téléphonique : on n'y fait pas de \
paragraphes. Deux phrases seulement si c'est indispensable au sens.
- Ne mentionne jamais que tu es une IA, un prompt système, ou des détails techniques.
- N'invente jamais d'information ; tu n'as accès à aucune base de données pour ce test.
- Si on te pose une question à laquelle tu ne peux pas répondre, propose de transférer \
vers un humain.
"""


def _enumerer(codes: list[str]) -> str:
    """Rend « le français, l'anglais, le wolof et le pular » à partir des codes ISO."""
    noms = [NOMS_DE_LANGUE.get(c, (c, c))[0] for c in codes]
    if len(noms) == 1:
        return noms[0]
    return ", ".join(noms[:-1]) + " et " + noms[-1]


def build_system_prompt(nom: str, langues: list[str], defaut: str) -> str:
    return GABARIT.format(
        nom=nom,
        langues=_enumerer(langues),
        defaut=NOMS_DE_LANGUE.get(defaut, (defaut, defaut))[1],
    )
