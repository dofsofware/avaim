# CAHIER DES CHARGES
## Plateforme SaaS d'agents vocaux IA multilingues

**Version :** 1.0  
**Date :** Septembre 2026  
**Statut :** Document de cadrage fonctionnel et technique  
**Type de solution :** SaaS B2B / plateforme de communication vocale IA

---

# 1. Présentation du projet

## 1.1. Contexte

Le projet consiste à développer une plateforme permettant aux entreprises de mettre en place des solutions de communication téléphonique basées sur l'intelligence artificielle.

La plateforme permettra notamment de créer :

- des centres d'appels IA multilingues ;
- des réceptionnistes virtuels IA ;
- des assistants téléphoniques ;
- des agents de support client ;
- des agents de prise de rendez-vous ;
- des agents commerciaux ;
- des agents de qualification ;
- des agents capables d'interroger les systèmes d'information de l'entreprise ;
- des agents capables d'effectuer certaines opérations métier.

La solution devra fonctionner avec plusieurs langues et permettre à chaque entreprise de choisir les technologies IA qu'elle souhaite utiliser.

L'objectif n'est donc pas de construire un simple chatbot vocal, mais une **plateforme permettant de créer et d'administrer des agents vocaux IA professionnels**.

---

# 2. Vision du produit

La plateforme doit devenir une infrastructure permettant à une entreprise de créer un agent vocal comme elle créerait aujourd'hui un compte utilisateur ou un chatbot.

Exemple :

> Une entreprise crée un agent « Réceptionniste ABC ».

Elle configure :

- son nom ;
- son rôle ;
- ses langues ;
- sa langue par défaut ;
- son comportement ;
- son LLM ;
- sa clé API LLM ;
- son moteur STT ;
- son moteur TTS ;
- sa voix ;
- son numéro de téléphone ;
- ses horaires ;
- ses bases de données ;
- ses outils métier ;
- ses règles de transfert vers les humains.

L'agent devient alors accessible par téléphone.

---

# 3. Objectifs

## 3.1. Objectif principal

Développer une plateforme permettant aux entreprises de déployer rapidement des agents vocaux IA multilingues connectés à leurs systèmes d'information.

## 3.2. Objectifs secondaires

La plateforme devra permettre :

1. de recevoir des appels ;
2. d'effectuer des appels sortants ;
3. de gérer plusieurs langues ;
4. de détecter automatiquement la langue du correspondant ;
5. d'utiliser une langue par défaut lorsque la détection échoue ;
6. de choisir son fournisseur LLM ;
7. d'utiliser sa propre clé API LLM ;
8. de choisir son moteur STT ;
9. de choisir son moteur TTS ;
10. de connecter MySQL et PostgreSQL ;
11. d'exécuter des opérations métier sécurisées ;
12. de transférer un appel vers un opérateur humain ;
13. d'enregistrer et transcrire les conversations ;
14. d'analyser les appels ;
15. de gérer plusieurs entreprises sur une même plateforme ;
16. de garantir l'isolation des données entre clients ;
17. de sécuriser les secrets avec HashiCorp Vault ;
18. de permettre une évolution vers de nouveaux modèles et fournisseurs IA.

---

# 4. Périmètre fonctionnel

Le produit sera organisé autour des modules suivants :

### Module 1 — Gestion des entreprises

Gestion des clients de la plateforme.

### Module 2 — Gestion des utilisateurs et des rôles

Gestion des administrateurs et utilisateurs de chaque entreprise.

### Module 3 — Gestion des agents IA

Création et configuration des agents vocaux.

### Module 4 — Gestion multilingue

Configuration des langues et détection automatique.

### Module 5 — Gestion des LLM

Sélection du fournisseur, du modèle et gestion des clés API.

### Module 6 — Speech-to-Text

Transformation de la voix en texte.

### Module 7 — Text-to-Speech

Transformation du texte en voix.

### Module 8 — Téléphonie

Gestion des appels entrants et sortants.

### Module 9 — Orchestration conversationnelle

Gestion du dialogue en temps réel.

### Module 10 — Connexion aux systèmes d'information

Accès contrôlé aux bases MySQL/PostgreSQL et APIs métier.

### Module 11 — Transfert humain

Passage de l'IA vers un opérateur humain.

### Module 12 — Campagnes d'appels

Gestion des appels sortants et campagnes.

### Module 13 — Historique et enregistrements

Conservation des appels, transcriptions et événements.

### Module 14 — Statistiques et reporting

Analyse de l'activité des agents.

### Module 15 — Facturation et consommation

Suivi de l'utilisation de la plateforme.

### Module 16 — Sécurité et audit

Gestion des secrets, permissions, journaux et traçabilité.

---

# 5. Architecture générale

L'architecture cible sera basée sur des composants spécialisés.

```text
                         ┌──────────────────────┐
                         │      CLIENT WEB      │
                         │ Dashboard / Admin UI │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │     API GATEWAY      │
                         └──────────┬───────────┘
                                    │
              ┌─────────────────────┼──────────────────────┐
              │                     │                      │
              ▼                     ▼                      ▼
       ┌─────────────┐      ┌─────────────┐       ┌─────────────┐
       │ Tenant/User │      │ Agent       │       │ Call        │
       │ Service     │      │ Service     │       │ Service     │
       └─────────────┘      └──────┬──────┘       └──────┬──────┘
                                   │                     │
                                   ▼                     ▼
                            ┌────────────────────────────────┐
                            │       REAL-TIME VOICE          │
                            │            LAYER               │
                            │                                │
                            │ FreeSWITCH + Pipecat           │
                            └───────────────┬────────────────┘
                                            │
                       ┌────────────────────┼────────────────────┐
                       │                    │                    │
                       ▼                    ▼                    ▼
                 ┌───────────┐       ┌────────────┐       ┌───────────┐
                 │    STT    │       │ AI Gateway │       │    TTS    │
                 │           │       │            │       │           │
                 │ Whisper / │       │ Claude /   │       │ XTTS /    │
                 │ autres    │       │ OpenAI /   │       │ autres    │
                 └───────────┘       │ Gemini...  │       └───────────┘
                                     └─────┬──────┘
                                           │
                                           ▼
                                  ┌─────────────────┐
                                  │  TOOL / DATA   │
                                  │    GATEWAY     │
                                  └────────┬────────┘
                                           │
                              ┌────────────┴────────────┐
                              ▼                         ▼
                       ┌────────────┐            ┌────────────┐
                       │ MySQL     │            │ PostgreSQL │
                       │ Client    │            │ Client     │
                       └────────────┘            └────────────┘

                              ┌─────────────────┐
                              │ HashiCorp Vault │
                              │ Secrets         │
                              └─────────────────┘
```

---

# 6. Principes architecturaux

La plateforme devra respecter les principes suivants :

- architecture modulaire ;
- architecture orientée services ;
- API-first ;
- multi-tenant ;
- sécurité Zero Trust autant que possible ;
- séparation entre téléphonie et logique métier ;
- séparation entre IA et données métier ;
- abstraction des fournisseurs IA ;
- secrets centralisés dans Vault ;
- composants remplaçables ;
- scalabilité horizontale ;
- observabilité native.

---

# 7. Gestion des entreprises

La plateforme doit être multi-tenant.

Chaque entreprise constitue un **tenant indépendant**.

## 7.1. Création d'une entreprise

Un administrateur plateforme pourra créer une entreprise avec :

- nom ;
- identifiant unique ;
- adresse ;
- téléphone ;
- email ;
- pays ;
- devise ;
- fuseau horaire ;
- statut ;
- formule d'abonnement.

## 7.2. Isolation

Les données d'un tenant ne doivent jamais être accessibles à un autre tenant.

Cette isolation devra être appliquée :

- au niveau API ;
- au niveau applicatif ;
- au niveau base de données ;
- au niveau stockage ;
- au niveau des appels ;
- au niveau des agents ;
- au niveau des secrets.

---

# 8. Gestion des utilisateurs

Chaque entreprise pourra gérer ses utilisateurs.

## 8.1. Rôles

Les rôles initiaux proposés :

### Super Administrator

Administrateur global de la plateforme.

### Tenant Administrator

Administrateur d'une entreprise.

### Supervisor

Responsable des agents et des opérations.

### Agent Manager

Gestionnaire des agents IA.

### Call Center Operator

Opérateur humain.

### Analyst

Accès aux statistiques et rapports.

### Viewer

Accès en lecture seule.

---

# 9. Gestion des agents IA

Le cœur de la plateforme sera le module de création d'agents.

## 9.1. Création d'un agent

L'administrateur pourra créer :

- nom de l'agent ;
- description ;
- rôle ;
- personnalité ;
- instructions système ;
- langues ;
- langue par défaut ;
- LLM ;
- STT ;
- TTS ;
- voix ;
- outils disponibles ;
- horaires ;
- règles de transfert ;
- numéro de téléphone.

## 9.2. Exemple

```text
Nom : Réceptionniste ABC
Rôle : Accueil téléphonique
Langues :
    - Français
    - Wolof
    - Anglais
    - Pulaar

Langue par défaut :
    Français

LLM :
    Claude

STT :
    Faster-Whisper

TTS :
    moteur configuré par l'administrateur

Outils :
    - rechercherClient
    - consulterSolde
    - prendreRendezVous
    - créerTicket
    - transfererVersHumain
```

---

# 10. Gestion multilingue

Le multilingue est une fonctionnalité fondamentale du produit et doit être prévu dès la première version.

## 10.1. Langues

Un agent pourra supporter plusieurs langues.

Exemple :

```text
Français
Wolof
Anglais
Arabe
Pulaar
Serer
Espagnol
Portugais
...
```

La liste ne doit pas être codée en dur afin de permettre l'ajout de nouvelles langues.

---

# 11. Détection automatique de la langue

À chaque début de conversation, la plateforme tentera d'identifier la langue du correspondant.

```text
Appel
  ↓
Analyse de la voix
  ↓
Détection langue
  ↓
Score de confiance
  ↓
┌──────────────────────────────┐
│ confiance suffisante ?       │
└──────────────┬───────────────┘
               │
        ┌──────┴───────┐
       OUI             NON
        │                │
        ▼                ▼
Langue détectée     Langue par défaut
```

## 11.1. Langue par défaut

Chaque agent devra obligatoirement posséder une langue par défaut.

**Règle obligatoire :**

> Si la langue du correspondant n'est pas détectée avec un niveau de confiance suffisant, l'agent utilise automatiquement la langue par défaut définie par l'administrateur.

## 11.2. Seuil de confiance

Le système devra pouvoir gérer un seuil de confiance.

Exemple :

```text
Wolof : 94 %
→ langue acceptée

Français : 87 %
→ langue acceptée

Pulaar : 38 %
→ détection insuffisante
→ langue par défaut
```

Le seuil pourra être configurable.

---

# 12. Code-switching

La plateforme devra être capable de gérer les conversations dans lesquelles plusieurs langues sont utilisées.

Exemple :

> « Bonjour, dama bëgg xam sama solde. »

Le système devra éviter de changer de langue à chaque mot et devra identifier la langue dominante de la conversation.

L'architecture devra toutefois permettre au modèle de comprendre des phrases mélangées.

---

# 13. Gestion des LLM

Le produit sera **LLM-agnostique**.

L'entreprise cliente pourra choisir son fournisseur et son modèle.

## 13.1. Fournisseurs

La plateforme devra être conçue pour supporter notamment :

- Claude ;
- OpenAI ;
- Gemini ;
- Mistral ;
- Azure OpenAI ;
- modèles privés/self-hosted ;
- autres fournisseurs compatibles.

Claude pourra être le premier fournisseur implémenté.

## 13.2. BYOK — Bring Your Own Key

Chaque client pourra fournir sa propre clé API.

Exemple :

```text
Provider : Anthropic
Model : modèle choisi
API Key : ****************
```

La clé ne devra jamais être affichée en clair après son enregistrement.

---

# 14. Gestion sécurisée des clés LLM

Les clés API ne doivent jamais être stockées en clair dans :

- MySQL ;
- PostgreSQL ;
- fichiers de configuration ;
- Git ;
- logs ;
- variables exposées au frontend.

Elles devront être stockées dans **HashiCorp Vault**.

Exemple conceptuel :

```text
secret/
   tenants/
      tenant-123/
         llm/
            anthropic/
               api-key
```

L'application récupère temporairement le secret lorsque cela est nécessaire.

---

# 15. AI Gateway

Un composant **AI Gateway** devra être développé afin de découpler la plateforme des fournisseurs LLM.

```text
Agent
  ↓
AI Gateway
  ↓
┌──────────┬──────────┬──────────┐
│ Claude   │ OpenAI   │ Gemini   │
└──────────┴──────────┴──────────┘
```

L'application métier ne devra pas contenir de logique spécifique à Claude.

Cela permettra de remplacer ou ajouter un fournisseur sans modifier toute la plateforme.

---

# 16. Speech-to-Text

Le STT transforme la voix du correspondant en texte.

```text
Voix
 ↓
STT
 ↓
Texte
 ↓
LLM
```

## 16.1. Architecture

Le STT devra également être abstrait.

```text
STT Gateway
   │
   ├── Faster-Whisper
   ├── Provider B
   ├── Provider C
   └── modèle spécialisé
```

Faster-Whisper pourra être utilisé comme première solution self-hosted.

## 16.2. Configuration

Chaque agent pourra avoir :

- moteur STT ;
- modèle ;
- langue ;
- paramètres ;
- seuil de confiance ;
- configuration spécifique.

---

# 17. Text-to-Speech

Le TTS transforme la réponse textuelle en voix.

```text
LLM
 ↓
Texte
 ↓
TTS
 ↓
Voix
```

La plateforme devra permettre de choisir :

- moteur ;
- modèle ;
- langue ;
- voix ;
- vitesse ;
- paramètres audio.

XTTS-v2 pourra être utilisé lorsqu'il est adapté à la langue concernée.

**Important :** le support d'une langue devra être validé moteur par moteur. La plateforme ne devra pas considérer automatiquement qu'un moteur TTS supporte toutes les langues.

Pour les langues africaines, notamment le wolof, une stratégie permettant de brancher des modèles ou fournisseurs spécialisés devra être prévue.

---

# 18. Pipeline conversationnel temps réel

Le traitement d'un appel devra fonctionner approximativement ainsi :

```text
Téléphone
   ↓
FreeSWITCH
   ↓
Pipecat
   ↓
STT
   ↓
Texte
   ↓
LLM
   ↓
Tool Calling éventuel
   ↓
Réponse
   ↓
TTS
   ↓
Pipecat
   ↓
FreeSWITCH
   ↓
Téléphone
```

---

# 19. Téléphonie

FreeSWITCH sera utilisé comme infrastructure téléphonique.

Il devra gérer notamment :

- appels entrants ;
- appels sortants ;
- SIP ;
- numéros téléphoniques ;
- routage ;
- IVR ;
- transfert ;
- conférences ;
- files d'attente ;
- enregistrement ;
- gestion des événements téléphoniques.

---

# 20. Numéros téléphoniques

Un tenant pourra associer un ou plusieurs numéros à ses agents.

Exemple :

```text
+221 XX XXX XX XX
        ↓
Agent : Réceptionniste ABC
```

La plateforme devra permettre :

- association numéro → agent ;
- horaires ;
- routage ;
- activation/désactivation ;
- règles de débordement ;
- transfert.

---

# 21. Appels entrants

Lorsqu'un appel arrive :

```text
Appel
 ↓
Identification du numéro
 ↓
Identification du tenant
 ↓
Identification de l'agent
 ↓
Initialisation session
 ↓
Détection langue
 ↓
Conversation IA
```

Le système devra conserver l'ensemble des événements importants de l'appel.

---

# 22. Appels sortants

La plateforme devra également permettre à un agent IA d'effectuer des appels sortants.

Cas d'utilisation :

- rappel client ;
- confirmation de rendez-vous ;
- relance ;
- enquête ;
- notification ;
- prospection ;
- recouvrement ;
- campagne marketing.

---

# 23. Campagnes d'appels

Une campagne pourra contenir :

- nom ;
- description ;
- agent ;
- numéro source ;
- liste de contacts ;
- horaires ;
- nombre maximum d'appels simultanés ;
- nombre de tentatives ;
- délai entre tentatives ;
- scénario ;
- statut.

Statuts :

```text
DRAFT
SCHEDULED
RUNNING
PAUSED
COMPLETED
CANCELLED
```

---

# 24. Gestion des contacts

Un contact pourra contenir :

- nom ;
- prénom ;
- téléphone ;
- email ;
- langue ;
- informations personnalisées ;
- statut ;
- historique des appels.

---

# 25. Transfert vers un humain

L'agent devra pouvoir transférer un appel vers un opérateur humain.

Exemples :

> « Je vais vous mettre en relation avec un conseiller. »

Le transfert pourra être déclenché :

- par le client ;
- par l'IA ;
- par une règle métier ;
- après plusieurs échecs de compréhension ;
- pour une demande sensible ;
- lorsque l'IA ne possède pas les permissions nécessaires.

---

# 26. Résumé avant transfert

Avant le transfert, l'IA devra générer un résumé destiné à l'opérateur.

Exemple :

```text
Client : Mamadou Ndiaye

Motif :
Demande concernant son paiement.

Informations récupérées :
Dernier paiement : 125 000 FCFA
Date : 03/09/2026

Demande :
Le client souhaite connaître le prochain échéancier.

Action :
Transfert vers conseiller.
```

L'opérateur devra recevoir ce résumé sans demander au client de répéter toute son histoire.

---

# 27. Gestion des outils métier

Le LLM ne devra pas avoir accès directement aux bases de données.

Il devra utiliser des **outils contrôlés**.

Exemple :

```text
LLM
 ↓
getCustomer()
 ↓
Tool Gateway
 ↓
Data Service
 ↓
PostgreSQL
```

---

# 28. Tool Calling

Un agent pourra disposer d'une liste d'outils.

Exemples :

```text
getCustomer()
getCustomerBalance()
getPaymentHistory()
createAppointment()
cancelAppointment()
createTicket()
getTicketStatus()
transferToHuman()
sendSMS()
```

Chaque outil devra définir :

- nom ;
- description ;
- paramètres ;
- types ;
- permissions ;
- tenant ;
- règles d'utilisation ;
- niveau de risque.

---

# 29. Accès aux bases MySQL et PostgreSQL

Les entreprises pourront connecter leurs bases :

- MySQL ;
- PostgreSQL.

Les données métier restent dans les systèmes de l'entreprise.

**HashiCorp Vault ne sert pas à stocker les données métier.**

Vault servira à stocker les informations sensibles permettant d'accéder aux systèmes :

- username ;
- password ;
- certificats ;
- clés ;
- tokens ;
- chaînes de connexion sensibles ;
- secrets API.

---

# 30. Architecture Data Gateway

```text
                   LLM
                    │
                    ▼
               Tool Gateway
                    │
                    ▼
               Data Gateway
                    │
           ┌────────┴────────┐
           ▼                 ▼
        MySQL            PostgreSQL
```

Le Data Gateway devra appliquer :

- authentification ;
- autorisation ;
- validation des paramètres ;
- filtrage tenant ;
- requêtes paramétrées ;
- limitation des opérations ;
- journalisation.

---

# 31. Interdiction du SQL libre généré par le LLM

Le LLM ne devra pas pouvoir envoyer directement :

```sql
SELECT * FROM clients;
```

ou pire :

```sql
DROP TABLE clients;
```

Le modèle devra utiliser des outils préalablement déclarés.

Exemple :

```text
getCustomerByPhone(phone)
```

Le backend décide ensuite de la requête SQL à exécuter.

Cela constitue une exigence de sécurité majeure.

---

# 32. Opérations de lecture et d'écriture

Les opérations devront être classées par niveau de risque.

### Lecture

Exemples :

- rechercher un client ;
- consulter un solde ;
- consulter un rendez-vous.

### Écriture

Exemples :

- créer un rendez-vous ;
- créer une réclamation ;
- modifier une information.

### Opération sensible

Exemples :

- annulation ;
- remboursement ;
- suppression ;
- modification financière.

Les opérations sensibles pourront nécessiter :

- confirmation du client ;
- confirmation humaine ;
- double validation ;
- règles métier spécifiques.

---

# 33. Gestion des prompts

Chaque agent pourra avoir :

- system prompt ;
- instructions ;
- règles métier ;
- ton ;
- personnalité ;
- informations générales ;
- règles d'escalade.

Exemple :

```text
Tu es le réceptionniste de l'entreprise ABC.

Tu dois :
- être poli ;
- répondre en français ou wolof ;
- ne jamais inventer une information ;
- utiliser les outils disponibles pour obtenir les données client ;
- transférer vers un humain si tu ne peux pas répondre ;
- ne jamais révéler les informations techniques internes.
```

---

# 34. Sécurité du prompt

La plateforme devra protéger les instructions système contre :

- prompt injection ;
- extraction du prompt ;
- manipulation de l'agent ;
- tentative d'accès aux secrets ;
- contournement des permissions.

Le LLM ne devra jamais recevoir :

- mots de passe Vault ;
- credentials DB inutiles ;
- secrets internes ;
- informations d'autres tenants.

---

# 35. Base de connaissances

Une évolution importante pourra permettre à un agent de consulter une base documentaire.

Sources possibles :

- PDF ;
- FAQ ;
- documents ;
- pages web ;
- procédures ;
- documentation interne.

Architecture possible :

```text
Documents
   ↓
Chunking
   ↓
Embeddings
   ↓
Vector Database
   ↓
RAG
   ↓
LLM
```

Cette fonctionnalité pourra être prévue dès l'architecture mais éventuellement livrée après le MVP.

---

# 36. Historique des conversations

Chaque appel devra produire une session.

Informations :

- tenant ;
- agent ;
- numéro ;
- date ;
- durée ;
- direction ;
- langue ;
- statut ;
- transcription ;
- résumé ;
- outils utilisés ;
- transfert éventuel ;
- coût estimé ;
- erreurs.

---

# 37. Enregistrement audio

La plateforme pourra enregistrer les appels selon la configuration du client et les obligations légales applicables.

L'enregistrement devra être :

- sécurisé ;
- associé à l'appel ;
- accessible selon permissions ;
- soumis à une politique de conservation ;
- supprimable selon les règles définies.

L'utilisateur devra pouvoir être informé lorsque l'enregistrement est activé lorsque cela est requis.

---

# 38. Transcription

Une transcription pourra être générée automatiquement.

Exemple :

```text
[00:00]
Agent : Bonjour, comment puis-je vous aider ?

[00:04]
Client : Bonjour, dama bëgg xam sama solde.

[00:08]
Agent : ...
```

La transcription devra pouvoir être associée à la langue détectée.

---

# 39. Résumé automatique

À la fin d'un appel, le système pourra générer :

- résumé ;
- motif ;
- actions effectuées ;
- résultat ;
- sentiment éventuel ;
- besoin de rappel ;
- transfert éventuel.

---

# 40. Dashboard

Chaque entreprise disposera d'un dashboard.

## Indicateurs principaux

- nombre d'appels ;
- appels entrants ;
- appels sortants ;
- appels réussis ;
- appels abandonnés ;
- durée moyenne ;
- taux de résolution IA ;
- taux de transfert humain ;
- langues utilisées ;
- consommation LLM ;
- consommation STT ;
- consommation TTS ;
- coûts estimés.

---

# 41. Dashboard temps réel

Une vue temps réel pourra afficher :

```text
Appels actifs : 24
Agents actifs : 8
Opérateurs humains : 12

Appels IA : 18
Appels humains : 6

Langues :
FR : 11
Wolof : 8
EN : 3
Pulaar : 2
```

---

# 42. Supervision des appels

Les superviseurs pourront consulter :

- appels actifs ;
- agent utilisé ;
- langue ;
- durée ;
- statut ;
- opérateur ;
- éventuelles erreurs.

Une fonctionnalité de supervision en direct pourra être prévue pour une version ultérieure.

---

# 43. Gestion des opérateurs humains

La plateforme devra permettre de gérer :

- opérateurs ;
- équipes ;
- files d'attente ;
- horaires ;
- compétences ;
- langues maîtrisées.

Exemple :

```text
File : Support Wolof
    ├── Agent 1
    ├── Agent 2
    └── Agent 3
```

---

# 44. Routage intelligent

Lorsqu'un transfert est nécessaire, le système pourra rechercher :

1. un opérateur disponible ;
2. parlant la langue du client ;
3. appartenant à la bonne équipe ;
4. disposant des compétences nécessaires.

---

# 45. Horaires

Chaque agent pourra avoir des horaires.

Exemple :

```text
Lundi       08:00 - 18:00
Mardi       08:00 - 18:00
Mercredi    08:00 - 18:00
Jeudi       08:00 - 18:00
Vendredi    08:00 - 17:00
Samedi      Fermé
Dimanche    Fermé
```

En dehors des horaires :

```text
Appel
 ↓
Agent
 ↓
Hors horaires
 ↓
Message
 ↓
Prise de message / callback / transfert selon configuration
```

---

# 46. Gestion des callbacks

L'agent pourra proposer un rappel.

Informations :

- numéro ;
- date ;
- heure ;
- motif ;
- langue ;
- agent ;
- statut.

---

# 47. Notifications

La plateforme pourra générer des notifications :

- appel manqué ;
- transfert ;
- campagne terminée ;
- erreur ;
- consommation élevée ;
- crédit faible ;
- agent indisponible.

Canaux possibles :

- email ;
- SMS ;
- webhook ;
- notification dashboard.

---

# 48. Webhooks

La plateforme devra exposer des webhooks.

Exemples :

```text
call.started
call.answered
call.ended
call.transferred
call.failed
agent.created
campaign.completed
```

Chaque événement pourra être envoyé au système du client.

---

# 49. API

La plateforme devra être API-first.

Exemples :

```http
POST /api/v1/tenants
GET  /api/v1/tenants/{id}

POST /api/v1/agents
GET  /api/v1/agents
PUT  /api/v1/agents/{id}

POST /api/v1/agents/{id}/languages

POST /api/v1/agents/{id}/calls

GET /api/v1/calls
GET /api/v1/calls/{id}

POST /api/v1/campaigns
POST /api/v1/campaigns/{id}/start

POST /api/v1/tools
POST /api/v1/data-sources

GET /api/v1/analytics
```

---

# 50. Authentification

L'authentification devra être centralisée.

Une solution basée sur **Keycloak** pourra être utilisée.

Fonctionnalités :

- OAuth2/OIDC ;
- JWT ;
- RBAC ;
- MFA ;
- gestion des sessions ;
- gestion des utilisateurs ;
- fédération d'identité éventuellement.

---

# 51. Autorisation

Chaque requête devra vérifier :

```text
Utilisateur
   ↓
Tenant
   ↓
Rôle
   ↓
Permission
   ↓
Ressource
```

Exemple :

Un utilisateur du tenant A ne doit jamais pouvoir récupérer :

```http
GET /api/v1/tenants/B/calls
```

---

# 52. Permissions

Les permissions pourront être fines.

Exemple :

```text
AGENT_READ
AGENT_CREATE
AGENT_UPDATE
AGENT_DELETE

CALL_READ
CALL_RECORDING_READ
CALL_TRANSCRIPT_READ

DATABASE_READ
DATABASE_WRITE

CAMPAIGN_CREATE
CAMPAIGN_START

USER_CREATE
USER_UPDATE
```

---

# 53. HashiCorp Vault

Vault constituera le coffre-fort des secrets.

Secrets potentiels :

```text
LLM API keys
STT API keys
TTS API keys
SIP credentials
Database credentials
Webhook secrets
OAuth secrets
Encryption keys
```

---

# 54. Gestion des secrets

Règles obligatoires :

- aucun secret dans Git ;
- aucun secret dans les logs ;
- aucun secret dans le frontend ;
- aucun secret en clair en base ;
- accès minimal nécessaire ;
- rotation possible ;
- audit des accès ;
- séparation des secrets par tenant.

---

# 55. Architecture backend

Une architecture Java/Spring Boot est recommandée pour les services métier.

Services possibles :

```text
api-gateway
identity-service
tenant-service
user-service
agent-service
call-service
campaign-service
telephony-service
ai-gateway
stt-service
tts-service
tool-service
data-service
connector-service
notification-service
analytics-service
billing-service
audit-service
```

Tous ces services ne sont pas obligatoires dans le MVP.

---

# 56. Pipecat

Pipecat sera utilisé pour la gestion du pipeline conversationnel temps réel.

Il aura notamment pour responsabilité de coordonner :

```text
Audio entrant
      ↓
STT
      ↓
LLM
      ↓
Tools
      ↓
LLM
      ↓
TTS
      ↓
Audio sortant
```

Le composant Pipecat pourra être développé comme un service Python spécialisé.

---

# 57. Répartition technologique

### Java / Spring Boot

Pour :

- logique métier ;
- API ;
- gestion des tenants ;
- utilisateurs ;
- agents ;
- campagnes ;
- sécurité ;
- données ;
- outils ;
- administration.

### Python / Pipecat

Pour :

- conversation temps réel ;
- orchestration audio ;
- streaming ;
- STT ;
- LLM ;
- TTS.

### FreeSWITCH

Pour :

- téléphonie ;
- SIP ;
- appels ;
- transfert ;
- audio.

---

# 58. Communication interservices

Selon les besoins :

### Synchrone

REST / HTTP ou gRPC pour les opérations nécessitant une réponse immédiate.

### Asynchrone

Un broker pourra être utilisé pour :

- événements d'appels ;
- analytics ;
- notifications ;
- facturation ;
- traitement des transcriptions ;
- traitement des résumés.

Kafka pourra être introduit lorsque le volume le justifiera.

---

# 59. Base de données plateforme

La plateforme devra disposer de sa propre base de données.

PostgreSQL est recommandé pour les données applicatives.

Elle contiendra notamment :

```text
tenant
user
role
permission
agent
agent_language
agent_tool
llm_configuration
stt_configuration
tts_configuration
phone_number
call
call_transcript
call_recording
campaign
contact
operator
queue
audit
usage
billing
```

Les bases clients restent séparées.

---

# 60. Modèle Agent

Exemple conceptuel :

```text
Agent
-----
id
tenantId
name
description
systemPrompt
defaultLanguage
status
llmConfigId
sttConfigId
ttsConfigId
createdAt
updatedAt
```

---

# 61. Modèle Language

```text
Language
--------
id
code
name
enabled
```

Exemples :

```text
fr-FR
en-US
wo-SN
ff-SN
sr-SN
ar
```

Les codes exacts devront être normalisés dans le référentiel linguistique de la plateforme.

---

# 62. Matrice de capacités linguistiques

Chaque langue devra être associée aux capacités réellement disponibles.

Exemple :

| Langue | Détection | STT | LLM | TTS |
|---|---|---|---|---|
| Français | Oui | Oui | Oui | Oui |
| Anglais | Oui | Oui | Oui | Oui |
| Wolof | Oui* | Oui* | Oui* | Oui* |
| Pulaar | Oui* | Oui* | Oui* | Oui* |

`*` signifie que la qualité et la disponibilité devront être validées par des tests.

La plateforme ne devra jamais annoncer une langue comme « supportée » simplement parce qu'un modèle prétend la gérer. Un benchmark réel devra être réalisé.

---

# 63. Latence

La conversation devra être aussi naturelle que possible.

Les principaux indicateurs seront :

- temps de détection de parole ;
- latence STT ;
- latence LLM ;
- latence TTS ;
- temps total de réponse ;
- interruptions ;
- qualité du streaming.

L'architecture devra favoriser le **streaming temps réel** plutôt que d'attendre la fin complète de chaque traitement.

---

# 64. Gestion des interruptions

L'utilisateur doit pouvoir interrompre l'IA.

Exemple :

```text
IA : Bonjour, je vais vous expliquer...
Client : Attendez !
IA : Oui, je vous écoute.
```

Cette fonctionnalité est essentielle pour avoir une conversation naturelle.

---

# 65. Gestion des erreurs

Si un composant tombe en panne :

```text
STT indisponible
      ↓
Fallback STT
      ↓
si indisponible
      ↓
Message utilisateur / transfert humain
```

Même logique pour :

- LLM ;
- TTS ;
- base de données ;
- outil métier.

---

# 66. Fallback LLM

La plateforme pourra permettre plusieurs modèles de secours.

Exemple :

```text
LLM principal
    ↓
Claude
    ↓
erreur
    ↓
LLM fallback
    ↓
Provider secondaire
```

Cette fonctionnalité pourra être activée selon la formule du client.

---

# 67. Fallback linguistique

Si une langue n'est pas correctement supportée :

```text
Langue demandée
      ↓
Moteur compatible ?
   │          │
  Oui        Non
   │          │
   ▼          ▼
Continuer   langue de secours
```

La langue de secours pourra être définie par l'administrateur.

---

# 68. Journalisation

Tous les événements importants devront être journalisés.

Exemples :

```text
CALL_STARTED
LANGUAGE_DETECTED
STT_REQUEST
LLM_REQUEST
TOOL_CALLED
TOOL_FAILED
TTS_REQUEST
CALL_TRANSFERRED
CALL_ENDED
```

Les logs ne devront jamais contenir de secrets.

---

# 69. Audit

Les actions administratives devront être auditées.

Exemple :

```text
Utilisateur : admin@entreprise
Action : modification_agent
Agent : agent-123
Date : 05/09/2026
Ancienne valeur : ...
Nouvelle valeur : ...
IP : ...
```

---

# 70. Monitoring

La plateforme devra disposer d'une solution d'observabilité.

À surveiller :

- CPU ;
- RAM ;
- GPU ;
- nombre d'appels ;
- latence ;
- erreurs ;
- STT ;
- TTS ;
- LLM ;
- FreeSWITCH ;
- Pipecat ;
- bases de données ;
- Vault ;
- Kubernetes.

---

# 71. Tracing distribué

Les requêtes devront pouvoir être suivies :

```text
Call ID
   ↓
FreeSWITCH
   ↓
Pipecat
   ↓
STT
   ↓
AI Gateway
   ↓
Tool Gateway
   ↓
Data Gateway
   ↓
PostgreSQL
```

Un `correlationId` devra permettre de retrouver toute la chaîne.

---

# 72. Déploiement

La plateforme devra être containerisée avec Docker.

L'environnement de production pourra utiliser Kubernetes.

```text
Kubernetes
 ├── API Gateway
 ├── Spring Boot Services
 ├── Pipecat
 ├── FreeSWITCH
 ├── STT
 ├── TTS
 ├── PostgreSQL
 ├── Redis
 ├── Vault
 └── Monitoring
```

---

# 73. GPU

Les modèles STT/TTS self-hosted pourront nécessiter des GPU.

L'architecture devra donc permettre de disposer de nœuds Kubernetes spécialisés GPU.

---

# 74. CI/CD

Pipeline recommandé :

```text
Git
 ↓
Build
 ↓
Tests
 ↓
Security Scan
 ↓
Docker Image
 ↓
Registry
 ↓
Deploy
 ↓
Kubernetes
```

Les environnements devront être séparés :

```text
DEV
TEST
STAGING
PRODUCTION
```

---

# 75. Tests

## Tests unitaires

Tous les services métier critiques devront être testés.

## Tests d'intégration

Tester :

- API ;
- DB ;
- Vault ;
- FreeSWITCH ;
- Pipecat ;
- LLM ;
- STT ;
- TTS.

## Tests end-to-end

Scénario :

```text
Téléphone
 ↓
FreeSWITCH
 ↓
Pipecat
 ↓
STT
 ↓
LLM
 ↓
Tool
 ↓
DB
 ↓
TTS
 ↓
Téléphone
```

---

# 76. Tests linguistiques

Avant de déclarer une langue comme opérationnelle, elle devra faire l'objet d'une campagne de tests.

Pour chaque langue :

- plusieurs locuteurs ;
- hommes/femmes ;
- différents accents ;
- différents niveaux de bruit ;
- téléphone de qualité variable ;
- débit de parole différent ;
- code-switching ;
- vocabulaire métier.

---

# 77. Benchmark Wolof

Le wolof étant une langue stratégique pour le marché sénégalais, un benchmark spécifique devra être réalisé.

Il faudra mesurer :

- taux d'erreur STT ;
- compréhension LLM ;
- qualité TTS ;
- latence ;
- compréhension des accents ;
- qualité avec bruit ;
- code-switching Wolof/Français.

Aucune technologie spécifique ne devra être considérée comme définitivement validée avant ces tests.

---

# 78. Tests de sécurité

Tests obligatoires :

- authentification ;
- autorisation ;
- isolation tenant ;
- injection SQL ;
- prompt injection ;
- accès Vault ;
- fuite de secrets ;
- API abuse ;
- rate limiting ;
- brute force ;
- élévation de privilèges.

---

# 79. Protection contre les abus

La plateforme devra intégrer :

- rate limiting ;
- quotas ;
- limites d'appels ;
- limites de concurrence ;
- protection contre les boucles IA ;
- timeout ;
- limitation des tools ;
- détection d'erreurs répétées.

---

# 80. Protection des données

La plateforme devra intégrer des mécanismes permettant de respecter les réglementations applicables concernant :

- données personnelles ;
- enregistrements téléphoniques ;
- consentement ;
- conservation ;
- suppression ;
- droit d'accès ;
- confidentialité.

Les exigences juridiques précises devront être validées avec un conseil juridique compétent pour les pays ciblés.

---

# 81. Rétention des données

Chaque tenant pourra définir une politique de conservation.

Exemple :

```text
Enregistrements audio : 30 jours
Transcriptions : 90 jours
Logs métier : 180 jours
Audit : 1 an
```

Les valeurs devront être configurables selon les obligations applicables.

---

# 82. Suppression des données

La plateforme devra permettre la suppression :

- d'un appel ;
- d'un enregistrement ;
- d'une transcription ;
- d'un contact ;
- d'un agent ;
- d'un tenant selon les règles applicables.

La suppression devra également prendre en compte les sauvegardes selon la politique définie.

---

# 83. Facturation

Le modèle commercial recommandé est hybride.

## Abonnement

Le client paie pour :

- nombre d'agents ;
- nombre d'utilisateurs ;
- fonctionnalités ;
- numéros ;
- infrastructure.

## Consommation

Facturation selon :

- minutes téléphoniques ;
- STT ;
- TTS ;
- consommation LLM ;
- stockage ;
- appels sortants.

---

# 84. Modèle BYOK

Avec le modèle BYOK :

> Le client fournit sa clé API LLM.

Avantages :

- contrôle du client ;
- facturation directe du LLM ;
- meilleure transparence ;
- pas besoin pour la startup d'avancer les coûts IA.

La plateforme facture alors principalement :

- logiciel ;
- téléphonie ;
- infrastructure ;
- STT/TTS si nécessaire ;
- fonctionnalités premium.

---

# 85. Mode Managed AI

Une seconde possibilité pourra être proposée :

> Le client ne fournit pas de clé et la plateforme gère le fournisseur IA.

Dans ce cas :

```text
Client
 ↓
Plateforme
 ↓
LLM Provider
```

La plateforme facture la consommation.

---

# 86. Gestion de la consommation

Le système devra mesurer :

```text
Tenant
 ↓
Agent
 ↓
Call
 ↓
LLM tokens
STT seconds
TTS seconds
Telephony seconds
Storage
```

Cela permettra de calculer les coûts.

---

# 87. MVP

Le MVP devra rester suffisamment simple pour permettre une première mise sur le marché rapidement.

### MVP — Fonctionnalités essentielles

- multi-tenant ;
- utilisateurs ;
- rôles ;
- création d'agents ;
- multilingue ;
- langue par défaut ;
- détection automatique ;
- Claude via AI Gateway ;
- BYOK ;
- Vault ;
- FreeSWITCH ;
- Pipecat ;
- STT ;
- TTS ;
- appels entrants ;
- appels sortants simples ;
- outils métier ;
- MySQL ;
- PostgreSQL ;
- transfert humain ;
- transcription ;
- résumé ;
- historique ;
- dashboard de base ;
- logs ;
- audit ;
- Docker ;
- Kubernetes.

---

# 88. V2

La V2 pourra ajouter :

- campagnes avancées ;
- files d'attente ;
- routage intelligent ;
- base de connaissances ;
- RAG ;
- plusieurs fournisseurs LLM ;
- plusieurs fournisseurs STT/TTS ;
- fallback automatique ;
- analytics avancés ;
- billing complet ;
- webhooks ;
- notifications ;
- supervision temps réel.

---

# 89. V3

La V3 pourra ajouter :

- marketplace d'agents ;
- marketplace de voix ;
- modèles spécialisés africains ;
- entraînement/fine-tuning ;
- agents autonomes avancés ;
- intégrations CRM ;
- Salesforce ;
- HubSpot ;
- WhatsApp ;
- SMS ;
- WebRTC ;
- omnicanal ;
- IA de qualité des appels ;
- scoring automatique des opérateurs.

---

# 90. Cas d'utilisation — Réceptionniste IA

```text
Client appelle
      ↓
Agent répond
      ↓
Détection langue
      ↓
Conversation
      ↓
Identification du besoin
      ↓
Consultation DB/API
      ↓
Réponse
      ↓
Fin de conversation
```

---

# 91. Cas d'utilisation — Consultation client

Client :

> « Bonjour, je voudrais connaître mon solde. »

Agent :

```text
STT
 ↓
LLM
 ↓
getCustomerByPhone()
 ↓
getCustomerBalance()
 ↓
LLM
 ↓
TTS
```

Réponse :

> « Votre solde actuel est de ... »

---

# 92. Cas d'utilisation — Prise de rendez-vous

```text
Client
 ↓
« Je voudrais un rendez-vous demain »
 ↓
LLM
 ↓
getAvailableSlots()
 ↓
LLM
 ↓
Client choisit
 ↓
createAppointment()
 ↓
Confirmation vocale
```

---

# 93. Cas d'utilisation — Transfert humain

```text
Client
 ↓
Question complexe
 ↓
IA ne peut pas répondre
 ↓
Résumé
 ↓
Recherche opérateur
 ↓
Transfert
 ↓
Opérateur reçoit résumé
```

---

# 94. Cas d'utilisation — Appel sortant

```text
Campagne
 ↓
Contact
 ↓
FreeSWITCH
 ↓
Agent IA
 ↓
Conversation
 ↓
Résultat
 ↓
Mise à jour CRM/DB
```

---

# 95. Exigences non fonctionnelles

## Performance

La plateforme devra supporter un nombre croissant d'appels simultanés sans modification majeure de l'architecture.

## Disponibilité

Les composants critiques devront être déployables en haute disponibilité.

## Scalabilité

Les services devront pouvoir être répliqués horizontalement.

## Sécurité

Les secrets et données sensibles devront être protégés à tous les niveaux.

## Maintenabilité

Les composants devront être indépendants et documentés.

## Extensibilité

L'ajout d'un nouveau :

- LLM ;
- STT ;
- TTS ;
- langage ;
- fournisseur téléphonique ;

ne devra pas nécessiter une réécriture globale de la plateforme.

---

# 96. Principe d'extensibilité

Le système devra privilégier les interfaces.

Exemple :

```text
LLMProvider
    ├── ClaudeProvider
    ├── OpenAIProvider
    ├── GeminiProvider
    └── CustomProvider
```

Même principe :

```text
STTProvider
TTSProvider
TelephonyProvider
DatabaseConnector
```

---

# 97. Architecture logique finale

```text
                    ┌───────────────────────┐
                    │       FRONTEND        │
                    │ Dashboard / Admin     │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │      API GATEWAY       │
                    └───────────┬───────────┘
                                │
        ┌───────────────────────┼────────────────────────┐
        │                       │                        │
        ▼                       ▼                        ▼
   Tenant/User             Agent Service            Call Service
        │                       │                        │
        └───────────────────────┼────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   VOICE ORCHESTRATOR  │
                    │       Pipecat         │
                    └───────────┬───────────┘
                                │
             ┌──────────────────┼───────────────────┐
             │                  │                   │
             ▼                  ▼                   ▼
        ┌─────────┐       ┌────────────┐       ┌─────────┐
        │   STT   │       │ AI Gateway │       │   TTS   │
        └─────────┘       └─────┬──────┘       └─────────┘
                                │
              ┌─────────────────┼──────────────────┐
              │                 │                  │
              ▼                 ▼                  ▼
           Claude             OpenAI            Gemini
                               
                                │
                                ▼
                         ┌──────────────┐
                         │ Tool Gateway │
                         └──────┬───────┘
                                │
                         ┌──────▼───────┐
                         │ Data Gateway │
                         └──────┬───────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
                  MySQL                 PostgreSQL

                         ┌───────────────┐
                         │ HashiCorp     │
                         │ Vault         │
                         └───────────────┘

                         ┌───────────────┐
                         │ FreeSWITCH    │
                         │ SIP/Telephony │
                         └───────────────┘
```

---

# 98. Principes de sécurité fondamentaux

Les règles suivantes sont considérées comme non négociables :

### Règle 1

Le LLM ne possède jamais directement les credentials de la base.

### Règle 2

Le LLM ne peut appeler que les outils autorisés.

### Règle 3

Les credentials sont stockés dans Vault.

### Règle 4

Un tenant ne peut accéder aux données d'un autre tenant.

### Règle 5

Toutes les actions sensibles sont auditées.

### Règle 6

Les secrets ne sont jamais écrits dans les logs.

### Règle 7

Les opérations destructives doivent être fortement contrôlées.

### Règle 8

Une IA ne doit jamais inventer une information métier lorsqu'elle peut utiliser une source fiable.

---

# 99. Critères d'acceptation du MVP

Le MVP sera considéré comme fonctionnel lorsqu'un administrateur pourra :

1. créer une entreprise ;
2. créer un utilisateur ;
3. créer un agent ;
4. choisir plusieurs langues ;
5. définir une langue par défaut ;
6. configurer la détection automatique ;
7. choisir un LLM ;
8. fournir une clé API ;
9. stocker cette clé dans Vault ;
10. configurer STT ;
11. configurer TTS ;
12. associer un numéro ;
13. recevoir un appel ;
14. détecter la langue ;
15. dialoguer avec l'appelant ;
16. interroger une base MySQL ;
17. interroger une base PostgreSQL ;
18. exécuter un outil métier ;
19. répondre vocalement ;
20. transférer vers un humain ;
21. enregistrer/transcrire l'appel selon configuration ;
22. consulter l'historique ;
23. consulter les statistiques ;
24. consulter les logs/audits.

---

# 100. Critère fondamental de réussite

Le produit ne devra pas être évalué uniquement sur sa capacité à « faire parler une IA ».

Le véritable critère de réussite sera :

> **Un utilisateur appelle un numéro de téléphone, parle naturellement dans sa langue, l'agent comprend sa demande, consulte les informations nécessaires dans le système de l'entreprise, exécute l'action autorisée et répond naturellement dans la bonne langue, avec la possibilité de transférer vers un humain lorsque cela est nécessaire.**

---

# 101. Roadmap technique recommandée

## Phase 1 — Foundation

- architecture projet ;
- Git ;
- CI/CD ;
- Docker ;
- Kubernetes ;
- PostgreSQL ;
- Keycloak ;
- Vault ;
- API Gateway ;
- tenant management.

## Phase 2 — Agent Platform

- agent management ;
- langues ;
- prompts ;
- configuration LLM ;
- BYOK ;
- AI Gateway.

## Phase 3 — Voice

- FreeSWITCH ;
- SIP ;
- Pipecat ;
- STT ;
- TTS ;
- streaming audio.

## Phase 4 — Business Tools

- Tool Gateway ;
- Data Gateway ;
- MySQL ;
- PostgreSQL ;
- outils métier.

## Phase 5 — Call Center

- opérateurs ;
- transfert ;
- files ;
- historique ;
- campagnes.

## Phase 6 — Analytics

- dashboard ;
- métriques ;
- coûts ;
- consommation ;
- qualité.

## Phase 7 — Industrialisation

- HA ;
- scaling ;
- GPU ;
- observabilité ;
- sécurité avancée ;
- billing.

---

# 102. Stack technique cible

### Backend

- Java
- Spring Boot
- Spring Security
- PostgreSQL

### Authentication

- Keycloak
- OAuth2 / OpenID Connect
- JWT

### Telephony

- FreeSWITCH
- SIP

### Voice AI

- Pipecat
- Faster-Whisper ou autre STT compatible
- XTTS-v2 ou autre TTS compatible
- fournisseurs externes selon les langues

### LLM

- Claude en premier fournisseur
- architecture multi-provider
- BYOK

### Secrets

- HashiCorp Vault

### Infrastructure

- Docker
- Kubernetes
- éventuellement GPU nodes

### Observabilité

- logs centralisés
- métriques
- traces distribuées
- alerting

---

# 103. Positionnement final du produit

Le produit ne doit pas être présenté uniquement comme :

> « un centre d'appels IA ».

Le positionnement recommandé est :

> **Une plateforme permettant aux entreprises de créer et déployer des agents vocaux IA multilingues capables de dialoguer avec leurs clients et d'interagir avec leurs systèmes d'information.**

Le centre d'appels et le réceptionniste IA deviennent alors deux applications principales de la plateforme.

---

# 104. Résumé exécutif

La solution sera une plateforme SaaS B2B multi-tenant permettant à chaque entreprise de créer ses propres agents vocaux IA.

Chaque agent pourra :

- parler plusieurs langues ;
- détecter automatiquement la langue du client ;
- utiliser une langue par défaut lorsque la détection échoue ;
- utiliser différents LLM ;
- fonctionner avec une clé API fournie par le client ;
- utiliser différents moteurs STT ;
- utiliser différents moteurs TTS ;
- recevoir et effectuer des appels ;
- consulter les données de l'entreprise ;
- utiliser MySQL ou PostgreSQL ;
- accéder aux credentials via HashiCorp Vault ;
- exécuter des outils métier contrôlés ;
- transférer vers un humain ;
- enregistrer et transcrire les conversations ;
- générer des résumés ;
- produire des statistiques.

L'architecture sera conçue dès le départ pour être **multilingue, multi-tenant, multi-LLM, multi-STT, multi-TTS et extensible**.

La séparation stricte entre **téléphonie, IA, logique métier, données et secrets** constituera l'un des principes fondamentaux de l'architecture.

---

# 105. Décisions de conception validées

Les décisions suivantes sont considérées comme acquises pour la conception initiale :

| Sujet | Décision |
|---|---|
| Produit | Plateforme d'agents vocaux IA |
| Marché | B2B / SaaS |
| Multilingue | Oui dès le lancement |
| Détection langue | Automatique |
| Échec détection | Langue par défaut de l'administrateur |
| LLM | Choisi par le client |
| API Key LLM | Fournie par le client (BYOK) |
| LLM initial | Claude |
| Architecture LLM | Multi-provider |
| STT | Pluggable, Faster-Whisper possible |
| TTS | Pluggable, XTTS-v2 possible |
| Téléphonie | FreeSWITCH / SIP |
| Orchestration | Pipecat |
| Bases clientes | MySQL / PostgreSQL |
| Secrets | HashiCorp Vault |
| Accès DB | Tool/Data Gateway |
| SQL libre par LLM | Interdit |
| Multi-tenant | Oui dès le départ |
| Transfert humain | Oui |
| Appels entrants | Oui |
| Appels sortants | Oui |
| Campagnes | Oui, progressivement |
| Dashboard | Oui |
| Audit | Oui |
| Docker | Oui |
| Kubernetes | Oui |
| Architecture | Microservices/modulaire |
| Scalabilité | Horizontale |
| Langues africaines | Supportées lorsque STT/TTS validés |

---

# 106. Conclusion

Le projet doit être conçu comme une **infrastructure technologique de Voice AI**, capable d'évoluer bien au-delà d'un simple réceptionniste téléphonique.

L'architecture devra notamment permettre de remplacer indépendamment :

```text
            ┌──────────────┐
            │     LLM      │
            └──────────────┘
                   ↕
            ┌──────────────┐
            │     STT      │
            └──────────────┘
                   ↕
            ┌──────────────┐
            │     TTS      │
            └──────────────┘
                   ↕
            ┌──────────────┐
            │  TELEPHONY   │
            └──────────────┘
```

sans remettre en cause le reste de la plateforme.

Cette approche permettra de commencer avec **Claude + Faster-Whisper + un moteur TTS adapté + FreeSWITCH + Pipecat**, tout en conservant la possibilité d'intégrer ultérieurement d'autres fournisseurs et modèles.

Le produit pourra ainsi évoluer progressivement d'un **réceptionniste IA** vers une véritable **plateforme de centres de contacts intelligents multilingues**.