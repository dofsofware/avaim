# FreeSWITCH — POC 100% local

Ce dossier construit l'image FreeSWITCH + `mod_audio_stream`, qui tourne directement sur le PC
de l'utilisateur (pas de VPS : la box Internet redirige déjà les ports 8088 et 2025 vers ce
PC, avec une IP publique stable — voir `../RUNBOOK.md` pour le diagnostic réseau qui a validé
ça). FreeSWITCH et Pipecat tournent sur la même machine ; plus besoin de tunnel WireGuard.

Voir `../CLAUDE.md` et le cahier des charges pour le contexte complet.

## État : le build fonctionne (validé dans cette session)

`docker build -t poc-freeswitch .` compile FreeSWITCH depuis les sources GitHub (branche
`master`) et compile `mod_audio_stream` par-dessus. Comptez 45-90 minutes au premier build
(dépendances SignalWire personnalisées + FreeSWITCH lui-même) ; les reconstructions suivantes
réutilisent le cache Docker et sont bien plus rapides tant que le Dockerfile ne change pas en
amont des étapes concernées.

**Quatre incohérences amont réelles ont été trouvées et corrigées pendant cette session** (à
garder en tête si un futur `docker build` échoue à nouveau après une mise à jour du dépôt
FreeSWITCH upstream) :
1. `signalwire/freeswitch:latest` n'existe pas publiquement sur Docker Hub.
2. Le dépôt de paquets précompilés `files.freeswitch.org` exige un compte depuis 2022 malgré
   une documentation en ligne parfois obsolète qui prétend le contraire.
3. Le dépôt "Entreprise" `fsa.freeswitch.com` (jetons préfixés `PT`) est un vrai dépôt payant
   protégé par SSO Atlassian Crowd — inaccessible avec un compte gratuit.
4. La branche `packages` de `github.com/freeswitch/spandsp` que le script officiel
   `build-dependencies.sh` clone par défaut est figée à la version 3.0.0, en dessous du minimum
   `>= 3.1.1` exigé par FreeSWITCH — corrigé en repointant vers le tag `v3.1.1` du même dépôt
   (voir le commentaire dans `Dockerfile`).

Par ailleurs, `fsdeb.sh` (script de packaging officiel) ne doit être appelé **qu'une seule
fois** par arbre source : son mécanisme de téléchargement des dépendances embarquées
(`debian/util.sh:getlib`) remplace l'archive téléchargée par un répertoire du même nom en guise
de marqueur, et un second appel échoue en tentant de re-télécharger par-dessus. D'où l'ordre du
`Dockerfile` : générer `debian/control` via `debian/bootstrap.sh` seul, installer les
dépendances via `mk-build-deps -i`, puis un unique appel à `fsdeb.sh`.

Et un bug distinct trouvé au premier `docker run` réel : `entrypoint.sh` utilisait `-nc`
(mode démon, se détache en arrière-plan) au lieu de `-c` (premier plan) — avec `-nc`, le
conteneur s'arrêtait immédiatement après le démarrage puisque le process qui le maintenait en
vie se backgroundait tout seul. Corrigé.

## Build & run en local

```bash
cd freeswitch
docker build -t poc-freeswitch .

docker run -d --name freeswitch \
  -e PIPECAT_WS_URL=ws://<IP_OU_NOM_DOCKER_DU_SERVICE_VOICE_AGENT>:8765 \
  -p 8088:8088/tcp -p 8088:8088/udp \
  -p 2025:2025/udp \
  poc-freeswitch
```

`PIPECAT_WS_URL` doit pointer vers le service `voice-agent` (voir `../voice-agent/`). Si les
deux tournent dans le même réseau Docker Compose, utiliser le nom du service
(`ws://voice-agent:8765`) ; sinon, l'IP locale du PC sur le réseau Docker de FreeSWITCH.

**Vérification immédiate** (le conteneur doit rester "Up", pas "Exited") :
```bash
docker ps --filter name=freeswitch
fs_cli -H 127.0.0.1   # ou : docker exec -it freeswitch fs_cli
# dans fs_cli :
module_exists mod_audio_stream   # doit renvoyer true
sofia status                     # doit montrer le profil "external" RUNNING
```

## Configuration manuelle restante

1. **Profil SIP externe sur le port 8088** : par défaut, le profil `external` écoute sur le
   port 5080 (visible dans `sofia status`). Fusionner `patches/external_profile.snippet` (à
   l'intérieur du conteneur, `docker exec -it freeswitch sh`) pour le faire écouter sur 8088 et
   déclarer l'IP publique de la box. Puis `fs_cli -x "sofia profile external restart"`.
2. **ACL Twilio** : fusionner `patches/acl.conf.xml.snippet` dans
   `/etc/freeswitch/autoload_configs/acl.conf.xml`, avec les vraies plages IP de signalisation
   Twilio (lien dans le commentaire du fichier). Puis `fs_cli -x reloadacl`.
3. **Dialplan** : éditer `/etc/freeswitch/dialplan/public/twilio_inbound.xml` pour remplacer
   `TWILIO_NUMBER_E164` par le numéro Twilio réellement acheté. Recharger avec
   `fs_cli -x reloadxml`.

## Test réel (une fois Twilio configuré, cf. `../RUNBOOK.md`)

Observer `fs_cli` en direct pendant l'appel de test pour voir l'INVITE arriver, l'extension
`twilio_inbound_to_agent` matcher, et les logs
`[stream_to_pipecat] uuid_audio_stream start => ...`.

## Sécurité (à faire dès ce POC, pas seulement en prod)

- Ne jamais laisser le profil `external` ouvert à `0.0.0.0/0` au-delà du strict testing —
  restreindre à l'ACL Twilio dès que le premier appel de test a réussi.
- Envisager `fail2ban` avec le filtre FreeSWITCH standard sur le PC, en plus de l'ACL, tant que
  les ports 8088/2025 restent exposés côté box.
- Ne pas exposer `fs_cli`/ESL (port 8021) publiquement — le laisser sur `127.0.0.1` uniquement
  (déjà le cas par défaut, ne pas le republier via `-p` sur le conteneur).
