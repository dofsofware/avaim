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
# Modèle "base" et pas "small" : mesuré dans cette session sur cette machine (4 cœurs, pas de
# GPU), "small" transcrit à 4,15x le temps réel en float32 et 2,04x en int8 — inutilisable en
# conversation (35 s de latence constatés sur un appel réel, l'appelant raccroche avant la
# réponse). "base" en int8 tient 0,80x le temps réel, et transcrivait la phrase de test
# française aussi bien que "small". Voir RUNBOOK.md pour le tableau complet du benchmark.
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('base', compute_type='int8')"
RUN python -c "\
from pipecat.services.piper.tts import PiperTTSService, PiperTTSSettings; \
PiperTTSService(settings=PiperTTSSettings(voice='fr_FR-siwis-medium', language='fr'))"
RUN python -c "from pipecat.audio.vad.silero import SileroVADAnalyzer; SileroVADAnalyzer()"

COPY . .

EXPOSE 8765

CMD ["python", "main.py"]
