# FreeSWITCH + mod_audio_stream, POC 100% local (PC de l'utilisateur, plus de VPS).
#
# Build validé dans cette session (~4.9GB, 45-90 min au premier build). Plusieurs approches ont
# été essayées et ont échoué avant celle-ci — `signalwire/freeswitch:latest` n'existe pas
# publiquement sur Docker Hub, le dépôt "communautaire" files.freeswitch.org exige désormais un
# compte, et le dépôt "Entreprise" fsa.freeswitch.com (que le préfixe "PT" du jeton fourni
# ciblait, selon la logique du script officiel fsget.sh) s'est révélé être un vrai dépôt payant
# protégé par SSO Atlassian Crowd, inaccessible avec un compte gratuit. On compile donc
# FreeSWITCH depuis les sources via le script de build officiel du projet (`fsdeb.sh`), qui ne
# nécessite aucun compte — seulement du temps de compilation.

FROM debian:bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        ca-certificates \
        sudo \
    && rm -rf /var/lib/apt/lists/*

# NOTE build — incohérence amont trouvée et corrigée : la branche "packages" de spandsp que
# build-dependencies.sh clone par défaut est figée à la version 3.0.0 — en dessous du minimum
# 3.1.1 exigé par configure.ac (`spandsp >= 3.1.1`) — et ne produit donc que libspandsp3-dev,
# alors que debian/bootstrap.sh exige libspandsp4-dev. Vérifié empiriquement (via une étape de
# debug supprimée ensuite) que le tag v3.1.1 du même dépôt bascule justement le SONAME à 4,
# fournissant exactement le paquet attendu sans avoir besoin de toucher debian/bootstrap.sh.
#
# Par ailleurs, fsdeb.sh ne doit être appelé qu'UNE SEULE FOIS : son mécanisme de téléchargement
# des dépendances embarquées (debian/util.sh:getlib) supprime l'archive après extraction et la
# remplace par un répertoire du même nom comme marqueur — un second appel tente de re-télécharger
# par-dessus ce répertoire et échoue ("Is a directory"). D'où l'ordre ci-dessous : la résolution
# des dépendances SignalWire doit être faite AVANT le seul et unique appel à fsdeb.sh.
RUN git clone --depth 1 https://github.com/signalwire/freeswitch.git /usr/src/freeswitch

RUN sed -i "s/git clone --branch packages \\(.*\\)\\/spandsp.git/git clone --branch v3.1.1 \\1\\/spandsp.git/" \
        /usr/src/freeswitch/scripts/packaging/build/dependencies/build-dependencies.sh

# debian/bootstrap.sh (lancé depuis debian/, cf. debian/rules) génère debian/control à partir de
# debian/control-modules — sans toucher à debian/util.sh (téléchargement des dépendances
# embarquées, à part, avec le bug de double-exécution). Le lancer nous-même ici, une fois, permet
# d'installer les Build-Depends AVANT le seul et unique appel à fsdeb.sh plus bas — dpkg-checkbuilddeps
# (dans dpkg-buildpackage, appelé par fsdeb.sh) vérifie des paquets *installés*, pas juste
# disponibles dans un dépôt apt, d'où la nécessité d'un vrai `mk-build-deps -i` avant.
RUN apt-get update && apt-get install -y --no-install-recommends devscripts equivs \
    && rm -rf /var/lib/apt/lists/* \
    && cd /usr/src/freeswitch/debian && ./bootstrap.sh -c bookworm

# Plusieurs dépendances de FreeSWITCH (sofia-sip, libks, signalwire-c, spandsp, et quelques
# codecs) n'existent pas dans les dépôts Debian standards — le projet fournit son propre script
# pour les compiler et les exposer via un dépôt APT local (-r), avant de builder FreeSWITCH
# lui-même. On exclut volontairement `libv8-packaging` de la liste par défaut de `-a` (moteur
# JavaScript V8, très long à compiler, non utilisé par ce POC — ce dépôt utilise Lua). Confirmé
# par un échec de build précédent que libv8 n'apparaît pas dans les Build-Depends de FreeSWITCH.
RUN cd /usr/src/freeswitch \
    && bash scripts/packaging/build/dependencies/build-dependencies.sh \
        -s -c -g -r -o /usr/src/localdeps \
        libbroadvoice libilbc libsilk spandsp sofia-sip libks signalwire-c

# Installation effective (pas juste "disponible") des Build-Depends, contre le dépôt local +
# Debian standard.
RUN apt-get update \
    && cd /usr/src/freeswitch \
    && mk-build-deps -i -r -t "apt-get -y --no-install-recommends -o Debug::pkgProblemResolver=yes" debian/control \
    && rm -rf /var/lib/apt/lists/*

# Seul et unique appel à fsdeb.sh : régénère debian/control (idempotent, sans effet de bord),
# télécharge une fois les dépendances embarquées (util.sh:getlib), puis build.
RUN cd /usr/src/freeswitch \
    && bash scripts/packaging/build/fsdeb.sh -b 1 -o /usr/src/fsdebs/ -w /usr/src/freeswitch

# Installation des .deb produits (freeswitch-meta-all équivalent : tous les paquets générés),
# puis résolution des dépendances runtime restantes.
RUN dpkg -i /usr/src/fsdebs/*.deb || true \
    && apt-get update \
    && apt-get install -y -f --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Dépendances de compilation de mod_audio_stream (le paquet freeswitch-dev généré ci-dessus
# fournit déjà les en-têtes FreeSWITCH nécessaires).
RUN apt-get update && apt-get install -y --no-install-recommends \
        cmake \
        build-essential \
        pkg-config \
        libssl-dev \
        zlib1g-dev \
        libevent-dev \
        libspeexdsp-dev \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --recurse-submodules https://github.com/amigniter/mod_audio_stream.git /usr/src/mod_audio_stream \
    && cd /usr/src/mod_audio_stream \
    && mkdir build && cd build \
    && cmake -DCMAKE_BUILD_TYPE=Release .. \
    && make -j"$(nproc)" \
    && make install \
    && rm -rf /usr/src/mod_audio_stream /usr/src/freeswitch /usr/src/fsdebs /usr/src/localdeps \
    && rm -f /etc/apt/sources.list.d/local.list

# Charge le module au démarrage de FreeSWITCH en l'ajoutant à modules.conf.xml existant
# (insertion juste avant la balise fermante </modules>, additif — ne touche pas au reste).
RUN sed -i 's#</modules>#  <load module="mod_audio_stream"/>\n</modules>#' \
    /etc/freeswitch/autoload_configs/modules.conf.xml

# Quatre bugs réels trouvés aux premiers tests avec un vrai softphone (MicroSIP, puis confirmé
# avec Linphone sur iPhone sur un vrai réseau Wi-Fi — donc pas un problème spécifique à un
# client) : la voix de l'appelant n'atteignait jamais FreeSWITCH (même l'extension d'écho
# native 9196, sans aucun de notre code, ne renvoyait rien) ; FreeSWITCH raccrochait tout seul
# après ~30s (media timeout : aucun RTP reçu de l'appelant).
# 1. Le profil "internal" (clients LAN/locaux) annonçait l'IP PUBLIQUE détectée par STUN pour
#    ext-rtp-ip/ext-sip-ip — un appelant sur le même réseau local tente alors d'envoyer son
#    audio vers cette IP publique, qui doit faire un aller-retour par la box (hairpin NAT),
#    souvent non supporté par les box grand public. Simplement retirer ces params est ALLÉ TROP
#    LOIN : FreeSWITCH retombe alors sur l'IP interne du réseau Docker (ex. 172.18.0.2), qui
#    n'est routable ni depuis le PC hôte de façon fiable, ni depuis un autre appareil du LAN
#    (un iPhone en Wi-Fi, par exemple) — encore pire. La bonne valeur pour un profil "internal"
#    utilisé en test local est l'IP LAN réelle de la machine hôte (ex. 192.168.1.10),
#    paramétrable via LAN_IP au cas où elle changerait. Le profil "external", lui, doit garder
#    son IP publique pour Twilio — non concerné par ce patch.
# 2. La plage de ports RTP globale n'était pas fixée (16384-32768 par défaut, en commentaire
#    dans switch.conf.xml) alors que seuls 16384-16394 sont publiés par Docker vers la box —
#    FreeSWITCH pouvait donc choisir un port RTP hors de la plage réellement joignable pour
#    RECEVOIR l'audio de l'appelant (l'envoi, lui, fonctionnait, d'où l'accueil audible mais
#    aucune réponse jamais captée). Plage restreinte pour correspondre exactement au publié.
# Remplacement par numéro de ligne (plus fiable que matcher le motif "$${external_rtp_ip}" au
# milieu d'un empilement d'échappements shell/sed/Docker ARG) — vérifié à ces lignes exactes
# dans cette version de FreeSWITCH ; si un futur rebuild depuis un commit plus récent échoue
# silencieusement ici, revérifier le numéro de ligne réel avec :
# `grep -n 'ext-rtp-ip\|ext-sip-ip' sip_profiles/internal.xml` dans le conteneur.
ARG LAN_IP=192.168.1.10
RUN grep -n 'external_rtp_ip\|external_sip_ip' /etc/freeswitch/sip_profiles/internal.xml \
    && sed -i \
      -e "299s#.*#    <param name=\"ext-rtp-ip\" value=\"${LAN_IP}\"/>#" \
      -e "300s#.*#    <param name=\"ext-sip-ip\" value=\"${LAN_IP}\"/>#" \
      /etc/freeswitch/sip_profiles/internal.xml \
    && sed -i \
      -e 's#<!-- <param name="rtp-start-port" value="16384"/> -->#<param name="rtp-start-port" value="16384"/>#' \
      -e 's#<!-- <param name="rtp-end-port" value="32768"/> -->#<param name="rtp-end-port" value="16394"/>#' \
      /etc/freeswitch/autoload_configs/switch.conf.xml \
    && grep -n 'ext-rtp-ip\|ext-sip-ip' /etc/freeswitch/sip_profiles/internal.xml

# 3. ext-rtp-ip ci-dessus ne suffisait PAS : FreeSWITCH ne l'applique que s'il juge l'appelant
#    "derrière un NAT", et switch_core_media_check_nat() répond non dès que l'IP de l'appelant
#    tombe dans local-network-acl (localnet.auto = les réseaux RFC1918 auxquels la machine est
#    rattachée). Or les appels arrivent ici depuis 172.18.0.1, la passerelle du réseau Docker,
#    qui est justement dans le sous-réseau du conteneur — donc classée "locale", donc pas de NAT,
#    donc SDP annonçant l'IP interne 172.18.0.2. Vérifié dans les logs : la ligne "c=" du SDP
#    restait à 172.18.0.2 malgré ext-rtp-ip correctement chargé (visible dans `sofia status`) et
#    malgré aggressive-nat-detection=true, qui n'agit pas sur ce test-là. Avec "none", aucun
#    appelant n'est considéré local, ext-rtp-ip s'applique, et le SDP annonce l'IP LAN joignable.
#    C'est la correction qui a fait remonter la voix de l'appelant pour la première fois.
RUN grep -q '<param name="local-network-acl" value="localnet.auto"/>' /etc/freeswitch/sip_profiles/internal.xml \
    && sed -i 's#<param name="local-network-acl" value="localnet.auto"/>#<param name="local-network-acl" value="none"/>#' \
      /etc/freeswitch/sip_profiles/internal.xml

# 4. Le port SIP interne doit être IDENTIQUE dans le conteneur et sur l'hôte. FreeSWITCH publie
#    son port d'écoute réel dans l'en-tête Contact du 200 OK, et le softphone y envoie son ACK.
#    Avec une redirection Docker asymétrique (hôte 5061 -> conteneur 5060), le Contact annonçait
#    5060 alors que rien n'écoutait sur ce port côté hôte : l'ACK n'arrivait jamais et FreeSWITCH
#    raccrochait de lui-même au bout de 32 s (timer SIP 64xT1) avec
#    `Reason: SIP;cause=408;text="ACK Timeout"` — l'audio fonctionnait pourtant, le RTP étant
#    déjà négocié, ce qui rendait le symptôme très trompeur. 5060 est déjà occupé sur l'hôte par
#    le softphone lui-même, d'où 5061 des deux côtés. Le paramètre ext-sip-port existe et
#    corrigerait l'annonce, mais il déplace aussi le port d'écoute réel : autant l'aligner ici.
RUN sed -i 's#internal_sip_port=5060#internal_sip_port=5061#' /etc/freeswitch/vars.xml \
    && grep -n 'internal_sip_port' /etc/freeswitch/vars.xml

# On n'écrase PAS les fichiers par défaut de acl.conf.xml / sip_profiles/external.xml :
# leur contenu exact dépend de la version compilée et les deviner ici risquerait de casser des
# réglages par défaut. Le dialplan, en revanche, est une simple extension additive (un fichier
# de plus dans le dossier), donc sans risque de casser l'existant.
COPY conf/dialplan/public/ /etc/freeswitch/dialplan/public/
# "default" : contexte utilisé pour les appels provenant d'utilisateurs enregistrés (ex.
# MicroSIP) — différent de "public" (appels entrants non authentifiés, ex. Twilio). Constaté
# empiriquement lors du premier test réel MicroSIP dans cette session.
COPY conf/dialplan/default/ /etc/freeswitch/dialplan/default/

COPY scripts/stream_to_pipecat.lua /usr/share/freeswitch/scripts/stream_to_pipecat.lua
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Voir freeswitch/README.md pour :
#  - le patch manuel à appliquer à acl.conf.xml (liste twilio-signaling) ;
#  - le patch manuel à appliquer à sip_profiles/external.xml (sip-port=8088, apply-inbound-acl) ;
#  - la commande `fs_cli -x reloadacl` / `fs_cli -x "sofia profile external restart"` après coup.

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# Ports SIP + RTP publiés au run — voir freeswitch/README.md. Configuration locale POC :
#   8088/tcp+udp : signalisation SIP (redirigé par la box vers ce PC)
#   2025/udp     : un seul port RTP fixe, suffisant pour un appel à la fois
#   5061/tcp+udp : signalisation SIP des softphones locaux (profil "internal") — DOIT être
#                  publié à l'identique (5061:5061), cf. le bug "ACK Timeout" ci-dessus
#   16384-16394/udp : plage RTP, publiée à l'identique elle aussi
EXPOSE 8088/tcp 8088/udp 2025/udp 5061/tcp 5061/udp 16384-16394/udp
