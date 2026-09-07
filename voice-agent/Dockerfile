FROM python:3.11-slim

# ffmpeg/libsndfile : dépendances audio courantes pour faster-whisper / piper-tts.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        libsndfile1 \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pré-téléchargement des modèles au build plutôt qu'au démarrage du conteneur : les
# téléchargements HuggingFace/Piper à chaud se sont montrés lents et parfois bloqués pendant
# cette session (plusieurs minutes, voire un blocage complet nécessitant un redémarrage du
# conteneur) — les figer dans l'image rend les démarrages/redémarrages instantanés et fiables.
# Modèle "small" en int8. Deux benchmarks successifs de cette session ont conclu à tort à "base" :
# le premier mesurait sur de la parole SYNTHÉTISÉE par Piper (sur-articulée, sans bruit ni codec),
# que tous les modèles réussissaient ; le second, sur de vrais appels, était faussé par le bug de
# rééchantillonnage corrigé dans main.py (Whisper recevait du 8 kHz pris pour du 16 kHz, ce qui
# le ralentissait d'un facteur 5 et faussait le classement). Une fois ce bug corrigé, "small"
# tient largement le temps réel sur ce processeur tout en étant nettement plus juste que "base"
# sur du français téléphonique. "medium" reste plus précis encore mais à ~2x le temps réel,
# inutilisable en conversation sans GPU. Voir RUNBOOK.md pour les tableaux de mesure.
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('small', compute_type='int8')"
RUN python -c "\
from pipecat.services.piper.tts import PiperTTSService, PiperTTSSettings; \
PiperTTSService(settings=PiperTTSSettings(voice='fr_FR-siwis-medium', language='fr'))"
RUN python -c "from pipecat.audio.vad.silero import SileroVADAnalyzer; SileroVADAnalyzer()"

COPY . .

EXPOSE 8765

CMD ["python", "main.py"]
