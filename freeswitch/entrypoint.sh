#!/bin/sh
# Substitue le placeholder __PIPECAT_WS_URL__ dans le script Lua avec la valeur réelle
# fournie via la variable d'environnement PIPECAT_WS_URL (ex: ws://voice-agent:8765 si les deux
# conteneurs partagent un réseau Docker Compose, sinon l'IP locale du service voice-agent),
# puis démarre FreeSWITCH normalement.
set -e

: "${PIPECAT_WS_URL:?La variable d'environnement PIPECAT_WS_URL doit être définie (ex: ws://voice-agent:8765)}"

sed -i "s#__PIPECAT_WS_URL__#${PIPECAT_WS_URL}#g" /usr/share/freeswitch/scripts/stream_to_pipecat.lua

# -c : reste au premier plan (indispensable en conteneur, sinon le process se détache en
# arrière-plan via -nc et le conteneur s'arrête aussitôt — bug réel trouvé au premier test réel).
exec /usr/bin/freeswitch -c -nonat
