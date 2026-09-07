"""Point d'entrée du service Pipecat du POC.

Assemble : Transport websocket (côté FreeSWITCH) -> Whisper (STT, local) -> LLM (BYOK, clé
récupérée depuis Vault, cf. §13.2/§14 du cahier des charges) -> Piper (TTS, local) -> Transport.

Écrit puis VALIDÉ par introspection contre pipecat-ai==1.8.1 réellement installé (build Docker
+ inspection des signatures dans cette session, voir historique de la conversation).

Provider LLM sélectionnable via LLM_PROVIDER=anthropic|gemini (défaut : gemini, le temps que
le compte Anthropic ait des crédits — voir RUNBOOK.md). C'est un simple aiguillage, pas une
vraie "AI Gateway" (cf. cahier des charges §15) : cette abstraction complète reste à construire
au niveau plateforme, hors périmètre de ce POC à un seul agent.
"""

import asyncio
import audioop
import os

from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import LLMRunFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.processors.audio.vad_processor import VADProcessor
from pipecat.services.anthropic.llm import AnthropicLLMService
from pipecat.services.google.gemini_live.stt import GeminiSTTService
from pipecat.services.google.llm import GoogleLLMService
from pipecat.services.google.tts import GeminiTTSService
from pipecat.services.piper.tts import PiperTTSService, PiperTTSSettings
from pipecat.services.whisper.stt import WhisperSTTService
from pipecat.transcriptions.language import Language
from pipecat.transports.websocket.server import (
    SingleClientWebsocketServerParams,
    SingleClientWebsocketServerTransport,
)

from prompt import SYSTEM_PROMPT
from transports.freeswitch_audio_stream import SAMPLE_RATE, FreeswitchAudioStreamSerializer
from vault_client import fetch_llm_api_key

WS_HOST = os.environ.get("PIPECAT_WS_HOST", "0.0.0.0")
WS_PORT = int(os.environ.get("PIPECAT_WS_PORT", "8765"))
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "gemini")
# STT_PROVIDER=gemini|whisper. Le cahier des charges (§ STT/TTS Gateways) impose un STT
# interchangeable ; ce POC en implémente deux. "whisper" reste utile hors ligne, mais sur ce
# matériel (i7-8665U, pas de GPU) il plafonne : le modèle "small" confond "vos horaires
# d'ouverture" avec "vos oreilles de travail", et "medium", qui transcrit juste, coûte ~14 s par
# tour de parole — Whisper traitant toujours des fenêtres de 30 s, ce coût est quasi indépendant
# de la longueur de l'énoncé. Gemini transcrit le même extrait parfaitement en ~1,5 s, avec la
# clé déjà présente dans Vault.
STT_PROVIDER = os.environ.get("STT_PROVIDER", "gemini")
# TTS_PROVIDER=gemini|piper. Piper est préférable en français (local, gratuit, latence minimale)
# mais n'a AUCUNE voix wolof — vérifié sur les 176 voix de son catalogue, dont la seule langue
# africaine est le swahili. C'était le seul maillon réellement bloquant pour le wolof, le STT et
# le LLM le gérant déjà. "gemini" est donc le défaut tant que le POC doit démontrer le
# multilingue ; repasser à "piper" rend le service insensible aux quotas, au prix du wolof.
TTS_PROVIDER = os.environ.get("TTS_PROVIDER", "gemini")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")
# flash-lite plutôt que flash : mesuré à 0,83 s contre 2,32 s pour une réponse courte, ce qui
# compte directement dans la latence perçue au téléphone. Le quota gratuit est par modèle ET par
# jour (20 requêtes pour gemini-2.5-flash, épuisées par les tests de cette session) — changer de
# modèle repart donc sur un quota neuf, mais ce n'est pas une solution durable : prévoir la
# facturation Google ou un crédit Anthropic avant toute démonstration.
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
PIPER_VOICE = os.environ.get("PIPER_VOICE", "fr_FR-siwis-medium")
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "small")
# Débit imposé par Whisper, indépendant de celui du pipeline (8 kHz, cf. SAMPLE_RATE).
WHISPER_SAMPLE_RATE = 16000


class TelephonyWhisperSTTService(WhisperSTTService):
    """WhisperSTTService corrigé pour de l'audio téléphonique 8 kHz.

    BUG RÉEL trouvé dans cette session, et de loin le plus coûteux : faster-whisper attend
    TOUJOURS du 16 kHz, mais pipecat-ai 1.8.1 ne rééchantillonne nulle part. `SegmentedSTTService`
    transmet son tampon brut au débit du pipeline (`stt_service.py:890`) et `WhisperSTTService`
    le convertit simplement en float32 avant de le passer au modèle (`whisper/stt.py:413-419`).
    Sur une chaîne téléphonique à 8 kHz, Whisper entendait donc la voix deux fois trop lente et
    une octave trop bas. Mesuré sur un vrai enregistrement d'appel, à modèle identique :
        sans rééchantillonnage : "Bon, je vous traite à la tête pour vous" — 30,3 s
        avec rééchantillonnage  : "Bonjour, je voudrais savoir..."        —  5,5 s
    Soit la précision ET la vitesse (5,5x) d'un seul coup. La lenteur avait d'abord été imputée
    à tort à la taille du modèle, alors que Whisper traitait chaque énoncé comme s'il durait le
    double.

    beam_size=1 : pipecat n'expose aucune option de décodage — il appelle
    `model.transcribe(audio, language=...)` sans transmettre le champ `Settings.extra` pourtant
    déclaré. On les lie donc au modèle lui-même. La recherche gloutonne s'est révélée plus rapide
    que le beam_size=5 par défaut, à qualité équivalente sur nos enregistrements.

    Une amorce (`initial_prompt`) a été essayée puis ÉCARTÉE : elle ne corrigeait la transcription
    que lorsqu'elle contenait déjà les mots attendus. Avec une amorce neutre, le résultat était
    identique à l'absence d'amorce — le gain apparent venait de la fuite de la réponse dans le
    test, pas d'un vrai conditionnement.
    """

    def _load(self):
        super()._load()
        transcribe = self._model.transcribe
        self._model.transcribe = lambda audio, **kw: transcribe(
            audio, beam_size=1, condition_on_previous_text=False, **kw
        )

    async def run_stt(self, audio: bytes):
        if self.sample_rate != WHISPER_SAMPLE_RATE:
            audio, _ = audioop.ratecv(audio, 2, 1, self.sample_rate, WHISPER_SAMPLE_RATE, None)
        async for frame in super().run_stt(audio):
            yield frame


async def build_tts():
    if TTS_PROVIDER == "gemini":
        # sample_rate=24000 est OBLIGATOIRE : l'API Gemini renvoie toujours du 24 kHz, mais le
        # service étiquette ses trames avec son propre `sample_rate`, lequel vaut sinon celui du
        # pipeline (8 kHz). BUG RÉEL constaté à l'oral dans cette session — de l'audio 24 kHz
        # annoncé comme du 8 kHz est rejoué trois fois trop lentement, d'où une voix « robotique
        # et ralentie ». Le service émet bien un avertissement au démarrage ("Google TTS requires
        # 24000Hz sample rate") mais ne corrige rien. Une fois le débit réel annoncé, c'est le
        # transport de sortie qui rééchantillonne vers les 8 kHz de FreeSWITCH
        # (base_output.py:604).
        return GeminiTTSService(
            api_key=await fetch_llm_api_key("gemini"),
            sample_rate=GeminiTTSService.GOOGLE_SAMPLE_RATE,
            params=GeminiTTSService.InputParams(language=Language.FR),
        )
    if TTS_PROVIDER == "piper":
        return PiperTTSService(settings=PiperTTSSettings(voice=PIPER_VOICE, language="fr"))
    raise ValueError(f"TTS_PROVIDER inconnu : {TTS_PROVIDER!r} (attendu: gemini, piper)")


async def build_stt():
    if STT_PROVIDER == "gemini":
        # Le débit du pipeline (8 kHz) est transmis tel quel dans le mime-type de chaque bloc
        # audio ; vérifié qu'un extrait d'appel réel en 8 kHz est transcrit aussi bien qu'une
        # version rééchantillonnée à 16 kHz, donc rien à convertir ici.
        return GeminiSTTService(
            api_key=await fetch_llm_api_key("gemini"),
            # `languages` sert d'indice (pas de contrainte) sur les langues attendues — cf. §11
            # du cahier des charges. Le service refuse de combiner ces indices avec
            # `language_auto` ("mutually exclusive", les indices l'emportent) : on s'en tient
            # donc aux indices, qui conviennent mieux à un agent dont les langues sont déclarées.
            # Validé sur un vrai appel : Gemini a transcrit "Ninga def? Man dégguma wolof tubab
            # dé. Est-ce que meun nga ma comprendre ?" en identifiant le wolof, y compris
            # l'alternance codique wolof/français au sein d'une même phrase (§12). Épinglé sur
            # `language=Language.FR` seul, il forçait au contraire le wolof dans le moule
            # français — constaté à l'usage, "élections Sénégal" pour une phrase en wolof.
            settings=GeminiSTTService.Settings(languages=[Language.FR, Language.WO]),
        )
    if STT_PROVIDER == "whisper":
        return TelephonyWhisperSTTService(
            device="cpu",
            compute_type="int8",
            settings=WhisperSTTService.Settings(model=WHISPER_MODEL, language=Language.FR),
        )
    raise ValueError(f"STT_PROVIDER inconnu : {STT_PROVIDER!r} (attendu: gemini, whisper)")


def build_llm(api_key: str):
    if LLM_PROVIDER == "anthropic":
        return AnthropicLLMService(
            api_key=api_key,
            settings=AnthropicLLMService.Settings(
                model=ANTHROPIC_MODEL,
                max_tokens=1024,
                system_instruction=SYSTEM_PROMPT,
            ),
        )
    if LLM_PROVIDER == "gemini":
        return GoogleLLMService(
            api_key=api_key,
            settings=GoogleLLMService.Settings(
                model=GEMINI_MODEL,
                max_tokens=1024,
                system_instruction=SYSTEM_PROMPT,
            ),
        )
    raise ValueError(f"LLM_PROVIDER inconnu : {LLM_PROVIDER!r} (attendu: anthropic, gemini)")


async def main() -> None:
    llm_api_key = await fetch_llm_api_key(LLM_PROVIDER)

    transport = SingleClientWebsocketServerTransport(
        host=WS_HOST,
        port=WS_PORT,
        params=SingleClientWebsocketServerParams(
            serializer=FreeswitchAudioStreamSerializer(),
            audio_in_enabled=True,
            audio_out_enabled=True,
            audio_in_sample_rate=SAMPLE_RATE,
            audio_out_sample_rate=SAMPLE_RATE,
        ),
    )

    # pipecat-ai 1.8.1 : la VAD n'est plus un paramètre du transport (constaté par
    # introspection — TransportParams n'a plus de champ vad_analyzer). Il faut l'insérer
    # explicitement comme étage du pipeline, AVANT le STT, sinon WhisperSTTService ne reçoit
    # jamais de VADUserStartedSpeakingFrame/VADUserStoppedSpeakingFrame et ne transcrit rien
    # (bug réel trouvé et corrigé pendant cette session : l'audio arrivait bien jusqu'au STT,
    # mais restait bufferisé indéfiniment faute de signal de fin de tour).
    #
    # min_volume=0.6 (défaut pipecat) s'est révélé trop strict : mesuré empiriquement sur notre
    # audio de test (confiance Silero jusqu'à 0.99, mais volume lissé plafonnant à ~0.19), donc
    # abaissé à 0.1 — la confiance reste le signal principal. À réévaluer avec de l'audio
    # téléphonique réel une fois FreeSWITCH branché (peut nécessiter un ajustement différent).
    vad_params = VADParams(min_volume=0.1)
    vad = VADProcessor(vad_analyzer=SileroVADAnalyzer(params=vad_params))

    # device/compute_type sont des paramètres directs du constructeur, pas des champs de
    # Settings (vérifié par introspection sur pipecat-ai 1.8.1). Sans compute_type explicite,
    # ctranslate2 convertit les poids float16 du modèle en float32 sur CPU — deux fois plus
    # lent que int8 pour une transcription identique sur notre phrase de test.
    stt = await build_stt()

    llm = build_llm(llm_api_key)

    tts = await build_tts()

    context = LLMContext()
    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(vad_analyzer=SileroVADAnalyzer(params=vad_params)),
    )

    pipeline = Pipeline(
        [
            transport.input(),
            vad,
            stt,
            user_aggregator,
            llm,
            tts,
            transport.output(),
            assistant_aggregator,
        ]
    )

    # PipelineParams.audio_in_sample_rate vaut 16000 par défaut, indépendamment de
    # audio_in_sample_rate=8000 réglé sur le transport — bug réel trouvé pendant cette
    # session : la VAD utilisait silencieusement 16000 Hz sur de l'audio réellement à 8000 Hz
    # (aucune erreur, 16000 étant un taux supporté par Silero, juste un mauvais découpage des
    # échantillons), ce qui empêchait toute détection de parole. Doit rester aligné sur
    # SAMPLE_RATE partout dans ce fichier.
    # idle_timeout_secs=None : `PipelineTask` (alias de `pipecat.pipeline.worker.PipelineWorker`)
    # annule tout le pipeline après 5 minutes d'inactivité par défaut (IDLE_TIMEOUT_SECS=300) —
    # bug réel trouvé pendant cette session : le conteneur s'arrêtait tout seul en attendant un
    # appel, avant même qu'un client ne se connecte. Notre service DOIT pouvoir attendre
    # indéfiniment entre deux appels, donc ce minuteur est désactivé.
    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            allow_interruptions=True,
            audio_in_sample_rate=SAMPLE_RATE,
            audio_out_sample_rate=SAMPLE_RATE,
        ),
        idle_timeout_secs=None,
    )

    @transport.event_handler("on_client_connected")
    async def on_client_connected(_transport, _client):
        # Le message d'accueil est déclenché ici, mais son contenu vient du system_instruction
        # (voir prompt.py) : Claude se présente de lui-même dès ce premier LLMRunFrame, sans
        # message utilisateur préalable.
        logger.info("FreeSWITCH connecté — appel en cours, déclenchement du message d'accueil.")
        await task.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(_transport, _client):
        # Bug réel trouvé pendant cette session : appeler task.cancel() ici annule tout le
        # pipeline, ce qui termine runner.run(task) et donc le process — le conteneur
        # s'arrêtait après CHAQUE appel. Or SingleClientWebsocketServerTransport est conçu pour
        # accepter des appels successifs (confirmé en lisant _client_handler du transport
        # installé : il boucle indéfiniment, acceptant un nouveau client après chaque
        # déconnexion). Il suffit donc de réinitialiser la conversation pour le prochain appel,
        # sans toucher au pipeline lui-même.
        logger.info("FreeSWITCH déconnecté — fin d'appel, réinitialisation pour le prochain.")
        context.set_messages([])

    runner = PipelineRunner()
    await runner.run(task)


if __name__ == "__main__":
    asyncio.run(main())
