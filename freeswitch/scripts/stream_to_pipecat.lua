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

-- Doit être défini AVANT setHangupHook : `function on_hangup()` n'affecte la variable globale
-- qu'au moment où cette instruction s'exécute. Placée après la boucle (qui ne se termine qu'au
-- raccroché), elle n'était jamais atteinte à temps — FreeSWITCH appelait donc un hook nil.
-- BUG RÉEL trouvé dans cette session : chaque appel se terminait par
-- "[ERR] mod_lua.cpp:103 attempt to call a nil value", et le flux mod_audio_stream n'était
-- jamais arrêté proprement. La trace pointait la ligne où le script attendait au moment du
-- raccroché (session:sleep / session:execute), ce qui a d'abord fait suspecter ces appels à tort.
function on_hangup()
    local stop_result = api:executeString("uuid_audio_stream " .. uuid .. " stop")
    freeswitch.consoleLog("INFO", "[stream_to_pipecat] uuid_audio_stream stop => " .. tostring(stop_result) .. "\n")
end

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
    else
        -- Ce "sleep" n'est PAS une simple attente : switch_ivr_sleep() lit activement les
        -- trames du canal (switch_core_session_read_frame) tant que le média est prêt. Or c'est
        -- précisément cette lecture qui déclenche le "media bug" posé par mod_audio_stream sur
        -- le flux entrant — sans elle, l'audio de l'appelant n'est JAMAIS transmis à Pipecat.
        -- BUG RÉEL trouvé dans cette session : une version précédente de ce script se contentait
        -- d'attendre les évènements ci-dessus, croyant le sleep superflu. La voix de l'appelant
        -- ne remontait alors que pendant que l'agent parlait (streamFile() lit lui aussi des
        -- trames), et pas une seconde de plus — donc aucune réponse n'était jamais transcrite,
        -- et le softphone raccrochait au bout d'une trentaine de secondes faute de RTP.
        session:sleep(100)
    end
end
