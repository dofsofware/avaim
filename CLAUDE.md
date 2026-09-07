# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository status

The full SaaS platform described in the cahier des charges (`Cahier des charges — Plateforme SaaS d'agents vocaux IA multilingues.md`, in French) is not built yet. What exists today is a single narrow POC: prove that dialing a real phone number connects to an AI agent end-to-end, following the target chain (telecom → FreeSWITCH → Pipecat → STT → LLM → TTS → FreeSWITCH → telecom) with Twilio standing in temporarily for the telecom operator. See `RUNBOOK.md` for the step-by-step operational procedure and current status, and the plan at `C:\Users\Smart Business\.claude\plans\calm-popping-chipmunk.md` for the full design rationale.

**🎉 First end-to-end AI voice call succeeded in this session**, over local SIP via MicroSIP (no Twilio/PSTN needed to prove this): MicroSIP → FreeSWITCH → Pipecat → Gemini → Piper → audio actually heard by the caller ("Bonjour, je suis l'agent vocal, comment puis-je vous aider aujourd'hui ?"). The entire mechanical chain is proven; what's left is Twilio/Orange configuration to go from a local SIP test to a real phone call. See `RUNBOOK.md` section 4bis for the reproducible test procedure, and the bug list below — the last and most important one (`mod_audio_stream` never actually playing returned audio into the call) was the final blocker.

**Architecture: 100% local, no VPS.** The user's home router already forwards two public ports (8088 TCP+UDP for SIP, 2025 TCP+UDP for RTP) to their PC with a stable public IP — confirmed reachable from outside after a real network diagnosis (Windows Firewall rules were the missing piece). So FreeSWITCH and the Pipecat service both run on the same PC, no WireGuard tunnel needed.

POC layout:
- `freeswitch/` — Dockerfile + config for FreeSWITCH, built from source (compiles `mod_audio_stream` to bridge call audio to a websocket). **Builds, runs, and has carried a real two-way voice call** (validated in this session: ~4.9GB image, 45-90min first build). See `RUNBOOK.md`/`freeswitch/README.md` for the real upstream inconsistencies found and fixed while getting this to build and actually work (no public Docker image, two different gated package repos, a spandsp version mismatch between FreeSWITCH and its own dependency-build script, a double-invocation bug in the official `fsdeb.sh` packaging script, a container-exits-immediately bug from using `-nc` instead of `-c`, registered-user calls routing through dialplan context `default` not `public`, and — the big one — `mod_audio_stream` writing returned audio to disk and firing a `mod_audio_stream::play` custom event that nothing consumed, so it was never actually played into the call; fixed by having `scripts/stream_to_pipecat.lua` subscribe to that event itself). Remaining manual config for a real phone call: external SIP profile port (8088), Twilio ACL, dialplan number — see `freeswitch/README.md`.
- `voice-agent/` — Python/Pipecat service that runs locally in Docker: custom FreeSWITCH websocket transport/serializer (`transports/freeswitch_audio_stream.py`, the one piece of code with no off-the-shelf equivalent), Whisper STT, LLM (Anthropic or Gemini, selected via `LLM_PROVIDER` env var, key fetched from Vault, never hardcoded), Piper TTS. **Validated end-to-end**, both synthetically (`voice-agent/test_client.py` simulating FreeSWITCH's audio stream) and over a real SIP call — see `RUNBOOK.md` for the real bugs found/fixed (missing VAD pipeline stage, VAD volume threshold, pipeline-wide sample rate defaulting to 16000 instead of the actual 8000; a later attempt to batch TTS audio into one message per response, keyed off `TTSStoppedFrame`, was reverted — that frame never reaches the serializer, it's intercepted upstream by the transport's own bot-speaking bookkeeping).

**Known deviation from the cahier des charges' illustrative choice**: the spec mentions XTTS-v2 as a candidate TTS engine, but Pipecat's `XTTSService` is deprecated (the Coqui XTTS streaming server it depends on has been unmaintained since Feb 2024). The POC uses **Piper TTS** instead — still local/self-hosted/pluggable, just actively maintained. Revisit if voice quality proves insufficient.

**Anthropic vs Gemini**: a Claude Code/claude.ai subscription does NOT include API credits for console.anthropic.com — they're separate products with separate billing even under the same account. The Anthropic key stored in Vault currently has no credit, so testing uses Gemini (`LLM_PROVIDER=gemini`, key also in Vault at `secret/tenants/poc/llm/gemini`) until that's resolved. Switch back via the env var once Anthropic has credit — no code changes needed either way.

Both `freeswitch/` and `voice-agent/` have now been built, run, and debugged for real in this environment — treat both as working (not just first drafts), with the specific remaining manual-config steps noted above and in `RUNBOOK.md`.

Once code exists beyond this POC, keep this file updated with real build/lint/test commands. Until then, treat the cahier des charges as the source of truth for architecture/naming decisions beyond what's already built.

## What the project is

A B2B SaaS platform that lets companies create and administer multilingual AI voice agents (call centers, virtual receptionists, appointment booking, support, sales qualification, etc.) reachable by phone. It is explicitly **not** a single voice chatbot — it's infrastructure for creating many configurable agents, each tenant choosing its own LLM/STT/TTS providers and supplying its own API keys (BYOK).

## Non-negotiable architectural rules (§98 of the spec)

These constraints override convenience when implementing any feature:

1. The LLM never holds direct database credentials.
2. The LLM may only call pre-declared, explicitly authorized tools — never free-form SQL (no `SELECT *`, no `DROP TABLE`, nothing generated ad hoc). The LLM calls a named tool like `getCustomerByPhone(phone)`; the backend decides the actual query.
3. Credentials/secrets live in HashiCorp Vault — never in Postgres/MySQL, config files, Git, logs, or anything exposed to the frontend.
4. Tenant isolation is absolute: at API, application, database, storage, call, agent, and secrets levels. A user from tenant A must never reach tenant B's data.
5. All sensitive/administrative actions are audited.
6. Secrets are never written to logs.
7. Destructive/sensitive operations (cancellation, refund, deletion, financial changes) require strong controls (confirmation, double validation).
8. The AI must never fabricate business information when a reliable source (tool/DB) is available.

## Target architecture (from the spec)

Layered, replaceable-component design — no layer should leak provider-specific logic into another:

```
Client Web (Dashboard/Admin) → API Gateway → {Tenant/User, Agent, Call} Services
                                                        ↓
                                        Real-time Voice Layer (FreeSWITCH + Pipecat)
                                                        ↓
                                   STT ←→ AI Gateway ←→ TTS
                                              ↓
                                        Tool Gateway → Data Gateway → MySQL / PostgreSQL (tenant systems)
                                                        (secrets fetched from HashiCorp Vault)
```

Key abstraction boundaries to preserve:
- **AI Gateway**: decouples business logic from any specific LLM provider (Claude first, then OpenAI/Gemini/Mistral/Azure OpenAI/self-hosted). No Claude-specific code should live outside this gateway.
- **STT/TTS Gateways**: same pluggable-provider principle (`STTProvider`, `TTSProvider` interfaces). Faster-Whisper is the first self-hosted STT; XTTS-v2 the candidate first TTS. Language support must be validated per-engine, per-language — never assume a provider supports a language just because it claims to (this matters especially for Wolof and other West African languages, called out repeatedly in the spec as needing real benchmarking, §62/§76/§77).
- **Tool Gateway → Data Gateway**: the only path from LLM tool-calls to MySQL/PostgreSQL. Data Gateway enforces authN/authZ, parameter validation, tenant filtering, parameterized queries, and logging. The LLM never touches SQL directly.
- **Vault**: stores only credentials/keys/certificates needed to reach tenant systems (LLM API keys, DB creds, SIP creds, webhook secrets) — never business data itself, structured per-tenant (e.g. `secret/tenants/{tenantId}/llm/anthropic/api-key`).

## Technology split (as decided in the spec, §55-57, §102)

- **Java / Spring Boot** — business logic, REST API, tenant/user/agent/campaign management, security, data access, tool declarations, admin. Services envisioned: `api-gateway`, `identity-service`, `tenant-service`, `user-service`, `agent-service`, `call-service`, `campaign-service`, `telephony-service`, `ai-gateway`, `stt-service`, `tts-service`, `tool-service`, `data-service`, `connector-service`, `notification-service`, `analytics-service`, `billing-service`, `audit-service`. Not all are required for MVP.
- **Python / Pipecat** — real-time conversational pipeline: audio in → STT → LLM → tool calls → LLM → TTS → audio out. Streaming-first, must support user-interrupt (barge-in).
- **FreeSWITCH** — telephony/SIP layer: inbound/outbound calls, routing, IVR, transfer, conferences, queues, recording.
- **PostgreSQL** — platform's own database (tenant, user, role, permission, agent, agent_language, agent_tool, llm_configuration, stt_configuration, tts_configuration, phone_number, call, call_transcript, call_recording, campaign, contact, operator, queue, audit, usage, billing). Tenant business data stays in the tenant's own MySQL/PostgreSQL — never copied into the platform DB.
- **Keycloak** — centralized auth (OAuth2/OIDC, JWT, RBAC, MFA).
- **HashiCorp Vault** — secrets only.
- Sync inter-service calls: REST/gRPC. Async: message broker (Kafka once volume justifies it) for call events, analytics, notifications, billing, transcript/summary processing.

## Multilingual behavior (core to the product, not an add-on)

- Every agent has a mandatory **default language**; language list is data-driven, never hardcoded.
- Language auto-detection runs per call with a **configurable confidence threshold** — below threshold, fall back to the agent's default language (§11).
- Code-switching (e.g. French/Wolof mixed) must be handled without flipping languages every word — identify the dominant language of the conversation while still letting the model parse mixed sentences (§12).
- A capability matrix tracks, per language, whether detection/STT/LLM/TTS are actually validated — a language is never declared "supported" just because a vendor claims it; it needs an actual benchmark (§62). Wolof has a dedicated benchmark requirement (§77) given its strategic importance for the Senegalese market.
- If a language isn't supported by an engine, fall back to an admin-defined fallback language (§67), not a hard failure.

## MVP scope (§87)

When starting implementation, the MVP boundary is: multi-tenant + users/roles + agent creation + multilingual with default language + auto-detection + Claude via AI Gateway + BYOK + Vault + FreeSWITCH + Pipecat + STT/TTS + inbound calls + simple outbound calls + business tools + MySQL/PostgreSQL connectors + human transfer + transcription + summary + history + basic dashboard + logs + audit + Docker + Kubernetes. Everything else (advanced campaigns, intelligent routing, RAG/knowledge base, multi-provider fallback, full billing, webhooks, real-time supervision) is explicitly deferred to V2/V3 (§88-89) — don't over-build these prematurely.
