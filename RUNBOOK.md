# RUNBOOK — Premier appel bout-en-bout

Suivre ces étapes dans l'ordre. Chaque étape a une vérification associée — ne pas passer à
la suivante tant que la vérification ne passe pas. Voir le plan complet et son contexte
dans `C:\Users\Smart Business\.claude\plans\calm-popping-chipmunk.md` et l'architecture
cible dans `CLAUDE.md`.

## État actuel (dernière session de travail)

**🎉 Premier appel vocal IA de bout en bout réussi**, en SIP local via MicroSIP (voir section
3ter) : MicroSIP → FreeSWITCH → Pipecat → Gemini → Piper → audio entendu par l'appelant.
L'utilisateur a réellement entendu l'agent dire "Bonjour, je suis l'agent vocal, comment
puis-je vous aider aujourd'hui ?". C'est la preuve que toute la chaîne mécanique fonctionne ;
il ne reste que la configuration Twilio/Orange pour passer d'un test SIP local à un vrai appel
téléphonique.

**Architecture 100% locale, plus de VPS/WireGuard.** La box de l'utilisateur redirige déjà les
ports **8088** (SIP Twilio), **2025** (RTP) et **5061** (SIP interne, pour MicroSIP/tests) vers
son PC, avec une IP publique stable (`41.82.130.197` au moment de cette session). FreeSWITCH et
le service Pipecat tournent tous les deux sur le même PC, branchés sur le même réseau Docker
(`voice-agent_default`).

**Étape 3 (service Pipecat) validée intégralement en local**, sans téléphonie du tout (voir
section 3bis) : accueil vocal → STT → LLM → TTS → audio de réponse, confirmé par un test de
bout en bout avec un client simulant FreeSWITCH.

**Étape 4 (FreeSWITCH) construite, démarrée et validée par un vrai appel** dans cette session —
voir `freeswitch/README.md` pour le détail. `mod_audio_stream` compilé et chargé, Sofia SIP
actif, extension de test `9999` (contexte `default`) fonctionnelle de bout en bout.
Reste à faire pour un vrai appel Twilio : configurer le profil externe sur le port 8088
(actuellement sur 5080 par défaut), l'ACL Twilio, et le numéro réel dans le dialplan (voir
`freeswitch/README.md`, section "Configuration manuelle restante").

LLM utilisé pour les tests : **Gemini**, pas Anthropic — le compte Anthropic lié à la clé
stockée dans Vault n'a pas de crédit (`Your credit balance is too low`), et est un produit
séparé de l'abonnement Claude Code de l'utilisateur (facturation distincte). Une clé Gemini a
été fournie et stockée dans Vault (`secret/tenants/poc/llm/gemini`). Le service supporte les
deux via `LLM_PROVIDER=anthropic|gemini` (défaut `gemini` actuellement, voir
`voice-agent/.env`). Repasser à `LLM_PROVIDER=anthropic` une fois des crédits ajoutés.

**Bugs réels trouvés et corrigés pendant cette session** (utile de garder en tête pour la
suite — ce sont des incohérences amont réelles, pas des erreurs de configuration locales) :

Côté `voice-agent/main.py` (pipeline Pipecat) :
1. Aucune VAD n'était insérée dans le pipeline → `WhisperSTTService` ne recevait jamais de
   signal de fin de parole et ne transcrivait rien. Corrigé en ajoutant un étage
   `VADProcessor` explicite entre `transport.input()` et `stt` (pipecat-ai 1.8.1 n'attache
   plus la VAD au transport contrairement aux versions plus anciennes).
2. `min_volume=0.6` (défaut pipecat) trop strict pour l'audio réellement mesuré → abaissé à
   `0.1`. À réévaluer avec de l'audio téléphonique réel une fois Twilio branché.
3. `PipelineParams.audio_in_sample_rate` vaut **16000 par défaut**, indépendamment du
   `audio_in_sample_rate=8000` réglé sur le transport — corrigé en l'alignant explicitement.

Côté `freeswitch/Dockerfile` (build FreeSWITCH depuis les sources) :
4. `signalwire/freeswitch:latest` n'existe pas publiquement sur Docker Hub.
5. Le dépôt de paquets `files.freeswitch.org` exige un compte depuis 2022.
6. Le dépôt "Entreprise" `fsa.freeswitch.com` est payant, protégé par SSO — inaccessible avec
   un compte gratuit malgré le préfixe de jeton `PT` qui semblait indiquer le contraire.
7. La branche `packages` de spandsp clonée par défaut est en version 3.0.0, sous le minimum
   `>= 3.1.1` exigé par FreeSWITCH — corrigé en pointant vers le tag `v3.1.1`.
8. `fsdeb.sh` ne doit être appelé qu'une seule fois (bug de re-téléchargement sinon).
9. `entrypoint.sh` utilisait `-nc` (mode démon) au lieu de `-c` (premier plan) — le conteneur
   s'arrêtait immédiatement après démarrage. Corrigé.
10. Les appels d'un utilisateur enregistré (ex. MicroSIP) sont routés par FreeSWITCH via le
    contexte **`default`**, pas `public` (réservé aux appels entrants non authentifiés comme
    Twilio) — l'extension de test avait été placée au mauvais endroit. Corrigé en la dupliquant
    dans `conf/dialplan/default/microsip_test.xml`.
11. **Le plus important** : `mod_audio_stream` n'a jamais joué automatiquement l'audio reçu de
    Pipecat dans l'appel. Il écrit bien le fichier décodé sur disque puis déclenche un
    évènement FreeSWITCH personnalisé (`mod_audio_stream::play`, chemin du fichier dans le
    corps JSON de l'évènement) — mais rien n'écoutait cet évènement, donc silence total côté
    appelant malgré un pipeline par ailleurs fonctionnel. Corrigé dans
    `scripts/stream_to_pipecat.lua` : le script s'abonne maintenant lui-même à cet évènement
    via `freeswitch.EventConsumer("CUSTOM", "mod_audio_stream::play")` et joue le fichier reçu
    avec `session:streamFile()`.

Côté `voice-agent/transports/freeswitch_audio_stream.py` :
12. Piste explorée puis abandonnée : grouper l'audio TTS en un seul message `streamAudio` par
    réponse (au lieu d'un message par petite trame ~40ms), dans l'idée de contourner un
    supposé manque de mise en file d'attente côté lecture. Diagnostic finalement erroné (le
    vrai problème était le §11 ci-dessus) et l'implémentation reposait sur `TTSStoppedFrame`,
    qui n'atteint jamais le sérialiseur (intercepté plus haut dans le transport pour son
    propre suivi interne) — le buffer ne se vidait donc jamais. Code revenu à l'envoi immédiat
    par trame, qui fonctionne correctement une fois §11 corrigé.

Les modèles Whisper/Piper/Silero sont pré-téléchargés au build Docker de `voice-agent`
(démarrages quasi instantanés). FreeSWITCH est volumineux à builder (~4.9 GB, 45-90 min au
premier build) mais le cache Docker accélère les reconstructions suivantes.

**Limite connue** (pas bloquante pour un premier appel, mais empêche plusieurs appels sans
intervention) : le service `voice-agent` s'arrête après un seul appel — à restructurer avant
un usage au-delà d'un test unique.

**Prochaine étape** : valider que l'agent répond bien à la voix de l'appelant (pas encore
confirmé — seul l'accueil a été entendu jusqu'ici), puis terminer la config FreeSWITCH
(port 8088, ACL), configurer Twilio, puis le renvoi d'appel Orange.

## Écart assumé par rapport au plan initial : TTS

Le plan prévoyait XTTS-v2. En préparant le code, il s'avère que le serveur Coqui XTTS
streaming utilisé par Pipecat n'est plus maintenu depuis février 2024, et que Pipecat a
déprécié son `XTTSService` (retiré en v2.0.0). **Ce POC utilise donc Piper TTS à la place**
(`PiperTTSService`, local, activement maintenu dans pipecat-ai, tourne en process sans
serveur séparé). Le cahier des charges n'imposait pas XTTS-v2 de façon stricte ("pourra être
utilisé... lorsqu'il est adapté") — Piper reste self-hosted et pluggable, conforme à l'esprit
de la section 17. À revisiter si la qualité de voix FR de Piper est jugée insuffisante à
l'usage (options : voix Piper FR différente, ou un autre moteur TTS local).

## 1. Clé API Anthropic (fait — clé Gemini utilisée en attendant des crédits)

1. Créer un compte / se connecter sur https://console.anthropic.com et générer une clé API.
2. Vérifier le moteur de secrets Vault :
   ```bash
   export VAULT_ADDR=http://localhost:8300
   export VAULT_TOKEN=<votre token>
   vault secrets list -detailed
   ```
   `secret/` est de type `kv` version `2` sur cette instance (confirmé).
3. Stocker la clé :
   ```bash
   vault kv put secret/tenants/poc/llm/anthropic api_key=<CLE_ANTHROPIC>
   ```
4. **Vérification** : `vault kv get secret/tenants/poc/llm/anthropic` affiche bien la clé
   stockée, jamais en clair ailleurs (pas dans ce dépôt, pas dans un `.env` committé).

## 2. Réseau (fait — plus de WireGuard nécessaire)

Vérifié dans cette session : la box de l'utilisateur redirige déjà les ports 8088 (TCP+UDP) et
2025 (TCP+UDP) vers l'IP locale du PC (`192.168.1.10`), et cette redirection est bien
joignable depuis l'extérieur (testé avec un listener TCP temporaire + `canyouseeme.org`).
L'IP publique de la box (`41.82.130.197`) est stable.

FreeSWITCH et `voice-agent` doivent simplement partager un réseau Docker pour communiquer (le
plus simple : les mettre dans le même fichier `docker-compose.yml`, ou connecter le conteneur
FreeSWITCH au réseau `voice-agent_default` existant via `docker network connect`).

**Vérification** : `docker network inspect voice-agent_default` liste bien les deux
conteneurs une fois démarrés.

## 3. Service Pipecat (PC local)

```bash
cd voice-agent
cp .env.example .env
# éditer .env : VAULT_TOKEN=<le même token que ci-dessus>, LLM_PROVIDER=gemini
docker compose up -d --build
```

**Vérification** : `docker logs voice-agent` montre qu'il écoute sur `0.0.0.0:8765`.

### 3bis. Test synthétique en local (sans FreeSWITCH ni téléphone)

Pour valider tout le pipeline (Whisper → LLM → Piper) sans FreeSWITCH/Twilio, un client de
test (`voice-agent/test_client.py`) simule ce que `mod_audio_stream` enverrait :

```bash
# 1) Générer une phrase de test "appelant" au format téléphonie (8kHz mono PCM16), une fois :
#    (voir historique de session pour la commande piper+ffmpeg utilisée : synthèse d'une
#    phrase française via le CLI `piper` déjà présent dans l'image, puis resample à 8kHz
#    avec ffmpeg — refaire au besoin, fichier non committé dans le dépôt)

# 2) Démarrer le service (voir section 3 ci-dessus), puis dans un autre terminal :
docker run --rm --network voice-agent_default -v <dossier_local>:/data voice-agent-voice-agent \
  python test_client.py --host voice-agent --port 8765 \
  --input /data/caller_8k.wav --output /data/conversation_out.wav --response-wait-secs 40
```

Sous Git Bash/MSYS, préfixer avec `MSYS_NO_PATHCONV=1` pour éviter que les chemins `/data/...`
soient réécrits en chemins Windows. Le service `voice-agent` s'arrête après cet appel (limite
connue ci-dessus) — le redémarrer (`docker compose up -d`) avant un nouveau test.

**Vérification** : `docker logs voice-agent` montre `New client connection`, l'accueil, la
transcription Whisper, puis une réponse LLM cohérente synthétisée en audio.

## 4. FreeSWITCH (PC local)

Voir `freeswitch/README.md` pour le détail complet (build — déjà validé dans cette session —,
configuration du port 8088, ACL Twilio, dialplan).

```bash
cd freeswitch
docker build -t poc-freeswitch .   # déjà fait, cache Docker réutilisé si rien n'a changé
docker run -d --name freeswitch \
  -e PIPECAT_WS_URL=ws://voice-agent:8765 \
  --network voice-agent_default \
  -p 8088:8088/tcp -p 8088:8088/udp \
  -p 2025:2025/udp \
  -p 5061:5060/udp -p 5061:5060/tcp \
  -p 16384-16394:16384-16394/udp \
  poc-freeswitch
```

`5061` (→ 5060 interne) et `16384-16394` servent au test SIP local via MicroSIP (section 4bis) —
`5060` est évité côté hôte car occupé par MicroSIP lui-même sur le PC de l'utilisateur.

**Vérification** : `docker ps` montre le conteneur "Up" (pas "Exited" — vérifier ce point en
particulier, un bug de ce type a déjà été rencontré et corrigé). Puis :
```bash
docker exec freeswitch fs_cli -x "module_exists mod_audio_stream"   # doit renvoyer true
docker exec freeswitch fs_cli -x "sofia status"                     # profil "external" RUNNING
```

### 4bis. Test réel via MicroSIP (validé dans cette session — recommandé avant Twilio)

Avant de configurer Twilio, valider toute la chaîne avec un softphone gratuit, gratuitement et
sans toucher à la box :

1. Installer MicroSIP (https://www.microsip.org/downloads).
2. Créer un compte : **Serveur SIP** `127.0.0.1:5061`, **Proxy SIP** `127.0.0.1:5061` (les
   deux champs, pas seulement le premier — sinon les appels sortants partent vers le port SIP
   par défaut 5060, qui est celui de MicroSIP lui-même, causant un bouclage sur soi-même),
   **Nom d'utilisateur/Login** `1000`, **Domaine** `192.168.1.10` (IP locale du PC),
   **Mot de passe** `1234` (compte de test par défaut de FreeSWITCH).
3. Une fois enregistré (icône verte), composer **`9999`** — déclenche
   `conf/dialplan/default/microsip_test.xml`, qui lance le même script Lua qu'un appel Twilio
   réel.

**Vérification** : l'agent doit être **entendu** en train de se présenter, et répondre à ce que
vous dites ensuite. Si l'appel affiche "Temporarily Unavailable" ou se comporte comme un appel
entrant inattendu, revoir la config Proxy SIP (point 2).

## 5. Twilio Elastic SIP Trunk

1. Créer un compte Twilio (l'essai gratuit suffit pour ce POC).
2. Console Twilio → **Elastic SIP Trunking** → créer un trunk.
3. Dans **Origination**, ajouter une Origination URI : `sip:41.82.130.197:8088` (adapter si
   l'IP publique de la box a changé — vérifier dans l'interface de la box).
4. Acheter un numéro Twilio (Voice-capable) et l'associer à ce trunk.
5. Noter le numéro Twilio au format E.164 — il sert à la fois pour `TWILIO_NUMBER_E164`
   dans `freeswitch/conf/dialplan/public/twilio_inbound.xml` et pour le renvoi Orange.
6. Récupérer les plages IP de signalisation Twilio (https://www.twilio.com/docs/sip-trunking/ip-addresses)
   et les mettre dans `freeswitch/patches/acl.conf.xml.snippet` avant de l'appliquer.

**Vérification** : dans la console Twilio, le trunk affiche un statut actif ; un appel de
test Twilio ("Test Credentials" / appel manuel vers le numéro Twilio depuis un téléphone
normal, sans passer par Orange) doit faire sonner/répondre FreeSWITCH — valider ce chemin
AVANT de toucher au renvoi d'appel Orange, pour isoler les problèmes.

## 6. Renvoi d'appel Orange Sénégal

Depuis le combiné du `+221 77 729 59 14` :

```
*#21#                          → vérifier l'état actuel du renvoi (doit être inactif au départ)
**21*<numero_twilio_E164>#     → activer le renvoi total vers le numéro Twilio
```

Après chaque session de test :
```
##002#                         → désactiver tous les renvois, revenir à la normale
```

**Vérification** : composer `*#21#` doit maintenant confirmer le renvoi actif vers le numéro
Twilio.

## 7. Test de bout en bout

1. Vérifier que Pipecat (`docker compose ps`), FreeSWITCH (`docker ps`) et le trunk Twilio
   sont tous actifs.
2. Depuis un **autre téléphone**, appeler `+221 77 729 59 14`.
3. Observer en parallèle :
   - `docker exec freeswitch fs_cli` : l'appel arrive, matche l'extension, lance le script Lua.
   - `docker logs -f voice-agent` : connexion du client websocket, transcriptions STT,
     réponses LLM, synthèse TTS.
4. Attendu : décroché automatique, l'agent se présente en français, comprend une question
   simple, répond vocalement.
5. Raccrocher, puis désactiver le renvoi Orange (`##002#`), et redémarrer `voice-agent`
   (`docker compose up -d`) avant le prochain test.

## En cas d'échec

Revenir à l'étape précédente qui a une vérification propre et repartir de là — ne pas
essayer de déboguer plusieurs couches à la fois (SIP, réseau Docker, pipeline Pipecat) en même
temps. Partager les logs exacts (FreeSWITCH `fs_cli`, `docker logs voice-agent`) pour qu'on
identifie la couche fautive.
