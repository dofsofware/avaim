-- Appelé depuis le dialplan (public/twilio_inbound.xml pour les vrais appels Twilio,
-- default/microsip_test.xml pour les tests locaux via softphone).
--
-- Rôle : répondre, démarrer le streaming audio bidirectionnel vers Pipecat via
-- mod_audio_stream, puis garder le canal ouvert jusqu'au raccroché tout en jouant l'audio
-- de réponse (TTS) que Pipecat renvoie.
--
-- BUG RÉEL trouvé au premier appel de test réel (via MicroSIP dans cette session) :
-- mod_audio_stream ne joue PAS automatiquement l'audio reçu de Pipecat dans l'appel. Il écrit
-- bien le fichier décodé sur disque (confirmé dans les logs FreeSWITCH : des fichiers
-- /tmp/<uuid>_N.tmp.r8 sont créés), puis déclenche un évènement FreeSWITCH personnalisé
-- ("mod_audio_stream::play", avec le chemin du fichier dans le corps JSON de l'évènement) —
-- mais rien n'écoutait cet évènement, donc le fichier n'était jamais réellement joué dans
-- l'appel (silence total côté appelant, confirmé). Corrigé ci-dessous : ce script s'abonne
-- lui-même à cet évènement et joue le fichier reçu avec session:streamFile().
--
-- PIPECAT_WS_URL est substitué au démarrage du conteneur par entrypoint.sh
-- (voir freeswitch/entrypoint.sh) à partir de la variable d'environnement du même nom,
-- ex: ws://voice-agent:8765

session:answer()
session:setVariable("hangup_after_bridge", "false")

local uuid = session:get_uuid()
local ws_url = "__PIPECAT_WS_URL__"

local api = freeswitch.API()
local cmd = string.format("%s start %s mono 8k", uuid, ws_url)
local result = api:executeString("uuid_audio_stream " .. cmd)
freeswitch.consoleLog("INFO", "[stream_to_pipecat] uuid_audio_stream start => " .. tostring(result) .. "\n")

-- S'abonne à l'évènement personnalisé que mod_audio_stream déclenche pour chaque réponse audio
-- reçue du serveur websocket (voir mod_audio_stream.c:responseHandler — SWITCH_EVENT_CUSTOM,
-- sous-classe "mod_audio_stream::play", chemin du fichier dans le corps JSON de l'évènement).
local play_consumer = freeswitch.EventConsumer("CUSTOM", "mod_audio_stream::play")

session:setHangupHook("on_hangup")
while session:ready() do
    local event = play_consumer:pop(0, 100)
    if event then
        local event_uuid = event:getHeader("Unique-ID")
        if event_uuid == uuid then
            local body = event:getBody()
            local file = body and body:match('"file"%s*:%s*"([^"]+)"')
            if file then
                freeswitch.consoleLog("INFO", "[stream_to_pipecat] lecture audio reçu : " .. file .. "\n")
                session:streamFile(file)
            else
                freeswitch.consoleLog("WARNING", "[stream_to_pipecat] évènement play sans champ 'file' : " .. tostring(body) .. "\n")
            end
        end
    end
end

function on_hangup()
    local stop_result = api:executeString("uuid_audio_stream " .. uuid .. " stop")
    freeswitch.consoleLog("INFO", "[stream_to_pipecat] uuid_audio_stream stop => " .. tostring(stop_result) .. "\n")
end
