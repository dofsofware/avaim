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
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('small')"
RUN python -c "\
from pipecat.services.piper.tts import PiperTTSService, PiperTTSSettings; \
PiperTTSService(settings=PiperTTSSettings(voice='fr_FR-siwis-medium', language='fr'))"
RUN python -c "from pipecat.audio.vad.silero import SileroVADAnalyzer; SileroVADAnalyzer()"

COPY . .

EXPOSE 8765

CMD ["python", "main.py"]
