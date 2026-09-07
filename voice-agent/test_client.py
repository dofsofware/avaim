"""Client de test qui simule mod_audio_stream pour valider le pipeline Pipecat en local,
sans FreeSWITCH ni Twilio ni téléphone réel (cf. demande explicite de tester en local d'abord).

Usage :
    python test_client.py --host voice-agent --port 8765 \\
        --input /data/caller_8k.wav --output /data/conversation_out.wav

Comportement :
  1. Se connecte en websocket au service Pipecat (qui, au connect, déclenche déjà l'accueil
     de l'agent via on_client_connected dans main.py).
  2. Écoute en tâche de fond tous les messages JSON `{"type":"streamAudio", ...}` reçus et
     accumule l'audio décodé (accueil + réponses).
  3. Attend quelques secondes pour laisser l'accueil se jouer, puis envoie le fichier WAV
     d'entrée (simulant la voix de l'appelant) en trames binaires, par paquets de 20ms,
     comme le ferait FreeSWITCH.
  4. Attend encore un peu pour laisser le temps à STT->LLM->TTS de répondre, puis écrit tout
     l'audio reçu (accueil + réponse) dans un fichier WAV pour écoute.
"""

import argparse
import asyncio
import base64
import json
import wave

import websockets
from loguru import logger

CHUNK_MS = 20
SAMPLE_RATE = 8000
BYTES_PER_SAMPLE = 2
CHUNK_BYTES = int(SAMPLE_RATE * (CHUNK_MS / 1000) * BYTES_PER_SAMPLE)


async def receive_loop(ws, received_audio: bytearray, sample_rate_holder: list):
    async for message in ws:
        if isinstance(message, bytes):
            logger.warning(f"Trame binaire inattendue reçue ({len(message)} octets), ignorée.")
            continue
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            logger.warning(f"Message non-JSON reçu, ignoré : {message!r}")
            continue

        if payload.get("type") == "streamAudio":
            data = payload["data"]
            sample_rate_holder[0] = data.get("sampleRate", SAMPLE_RATE)
            audio_bytes = base64.b64decode(data["audioData"])
            received_audio.extend(audio_bytes)
            logger.info(f"Audio reçu : +{len(audio_bytes)} octets (total {len(received_audio)})")
        else:
            logger.info(f"Message reçu (ignoré) : {payload}")


async def send_wav(ws, input_path: str):
    with wave.open(input_path, "rb") as wf:
        assert wf.getframerate() == SAMPLE_RATE, f"Le WAV d'entrée doit être à {SAMPLE_RATE} Hz"
        assert wf.getnchannels() == 1, "Le WAV d'entrée doit être mono"
        pcm = wf.readframes(wf.getnframes())

    logger.info(f"Envoi de {len(pcm)} octets d'audio appelant, par paquets de {CHUNK_BYTES} octets...")
    for i in range(0, len(pcm), CHUNK_BYTES):
        chunk = pcm[i : i + CHUNK_BYTES]
        await ws.send(chunk)
        await asyncio.sleep(CHUNK_MS / 1000)
    logger.info("Envoi terminé.")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--input", required=True, help="WAV appelant, 8kHz mono PCM16")
    parser.add_argument("--output", required=True, help="WAV de sortie (accueil + réponse)")
    parser.add_argument("--greeting-wait-secs", type=float, default=8.0)
    parser.add_argument("--response-wait-secs", type=float, default=15.0)
    args = parser.parse_args()

    received_audio = bytearray()
    sample_rate_holder = [SAMPLE_RATE]

    uri = f"ws://{args.host}:{args.port}"
    logger.info(f"Connexion à {uri} ...")
    async with websockets.connect(uri) as ws:
        recv_task = asyncio.create_task(receive_loop(ws, received_audio, sample_rate_holder))

        logger.info(f"Attente de {args.greeting_wait_secs}s pour l'accueil de l'agent...")
        await asyncio.sleep(args.greeting_wait_secs)

        await send_wav(ws, args.input)

        logger.info(f"Attente de {args.response_wait_secs}s pour la réponse de l'agent...")
        await asyncio.sleep(args.response_wait_secs)

        recv_task.cancel()

    if not received_audio:
        logger.error("Aucun audio reçu de l'agent — voir les logs du service voice-agent.")
        return

    with wave.open(args.output, "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(sample_rate_holder[0])
        out.writeframes(bytes(received_audio))

    logger.info(f"Conversation sauvegardée dans {args.output} ({len(received_audio)} octets audio).")


if __name__ == "__main__":
    asyncio.run(main())
