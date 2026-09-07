"""Sérialiseur Pipecat sur mesure pour le protocole websocket du module FreeSWITCH
`mod_audio_stream` (https://github.com/amigniter/mod_audio_stream).

Il n'existe pas d'intégration Pipecat<->FreeSWITCH officielle (contrairement à Twilio/Daily),
donc ce fichier est la pièce de code "neuve" du POC — le reste du dépôt n'est que de la
configuration. Protocole tel que documenté par mod_audio_stream (non testé en conditions
réelles depuis cette session, faute d'accès au VPS) :

  FreeSWITCH -> Pipecat : trames binaires WebSocket contenant de l'audio PCM L16 brut,
                          mono, à SAMPLE_RATE Hz (8000 par défaut, cf. "mono 8k" dans
                          uuid_audio_stream côté dialplan Lua).
  Pipecat -> FreeSWITCH : trames texte WebSocket, JSON :
                          {"type": "streamAudio",
                           "data": {"audioDataType": "raw",
                                     "sampleRate": SAMPLE_RATE,
                                     "audioData": "<base64 PCM16>"}}

À valider dès le premier appel de test réel : si FreeSWITCH envoie aussi des messages
JSON de contrôle sur le même canal (ex. un message de démarrage), la branche
`isinstance(message, str)` ci-dessous les journalise sans planter, à affiner ensuite.
"""

import audioop
import base64
import json
import os
import time

from loguru import logger

from pipecat.frames.frames import Frame, InputAudioRawFrame, OutputAudioRawFrame
from pipecat.serializers.base_serializer import FrameSerializer

SAMPLE_RATE = 8000
NUM_CHANNELS = 1


class FreeswitchAudioStreamSerializer(FrameSerializer):
    """Traduit entre les Frames Pipecat et le protocole websocket de mod_audio_stream.

    pipecat-ai 1.8.1 : pas de propriété `type` fixe à déclarer (contrairement à d'anciennes
    versions) — le type de trame WebSocket envoyée (texte/binaire) est déduit du type Python
    retourné par `serialize()` (str -> texte, bytes -> binaire). Confirmé en inspectant
    `pipecat.serializers.base_serializer.FrameSerializer` réellement installé.

    Tentative d'une variante "buffer + flush sur TTSStoppedFrame" au premier test réel (via
    MicroSIP), pour tenter de contourner un possible manque de mise en file d'attente côté
    lecture de mod_audio_stream — abandonnée : logs à l'appui, `TTSStoppedFrame` n'atteint
    jamais `serialize()` (intercepté plus haut dans le transport pour son propre suivi interne
    "bot speaking"), donc le buffer ne se vidait jamais et aucun audio ne partait plus du tout.
    Retour à l'envoi immédiat par trame — confirmé atteindre FreeSWITCH (fichiers .tmp.r8 créés
    côté module), donc le vrai problème de "je n'entends rien" est ailleurs (à investiguer côté
    FreeSWITCH/mod_audio_stream : le fichier est-il seulement écrit sans jamais être joué ?).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._chunk_count = 0
        # Vidage brut de l'audio entrant, pour diagnostiquer la qualité réellement soumise au
        # STT (niveau, écrêtage, intelligibilité) plutôt que de la déduire des transcriptions.
        # Désactivé par défaut : n'activer que le temps d'un appel de test.
        self._dump = None
        if os.environ.get("DEBUG_DUMP_AUDIO"):
            path = f"/app/dump/in_{time.strftime('%H%M%S')}.raw"
            os.makedirs("/app/dump", exist_ok=True)
            self._dump = open(path, "wb")
            logger.info(f"[freeswitch_audio_stream] vidage audio entrant vers {path}")

    async def setup(self, setup) -> None:
        return None

    async def serialize(self, frame: Frame):
        if not isinstance(frame, OutputAudioRawFrame):
            return None

        payload = {
            "type": "streamAudio",
            "data": {
                "audioDataType": "raw",
                "sampleRate": SAMPLE_RATE,
                "audioData": base64.b64encode(frame.audio).decode("ascii"),
            },
        }
        return json.dumps(payload)

    async def deserialize(self, data) -> Frame | None:
        if isinstance(data, (bytes, bytearray)):
            self._chunk_count += 1
            if self._dump is not None:
                self._dump.write(bytes(data))
                self._dump.flush()
            if self._chunk_count % 50 == 0:
                try:
                    peak = audioop.max(bytes(data), 2)
                    rms = audioop.rms(bytes(data), 2)
                    logger.debug(
                        f"[freeswitch_audio_stream] audio entrant : {len(data)} octets, "
                        f"chunk#{self._chunk_count}, peak={peak}, rms={rms} (sur 32767 max)"
                    )
                except Exception as e:
                    logger.debug(f"[freeswitch_audio_stream] audio entrant : {len(data)} octets (analyse échouée: {e})")
            return InputAudioRawFrame(
                audio=bytes(data),
                sample_rate=SAMPLE_RATE,
                num_channels=NUM_CHANNELS,
            )

        if isinstance(data, str):
            try:
                message = json.loads(data)
                logger.debug(f"[freeswitch_audio_stream] message texte reçu (ignoré) : {message}")
            except json.JSONDecodeError:
                logger.warning(f"[freeswitch_audio_stream] message texte non-JSON ignoré : {data!r}")
            return None

        return None
