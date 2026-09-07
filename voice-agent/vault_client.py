"""Récupération des clés API LLM depuis HashiCorp Vault au démarrage.

Conforme à la règle non négociable du cahier des charges (§14, §53, §98) : la clé LLM
n'est jamais codée en dur ni lue depuis une variable d'environnement en clair dans le
docker-compose — uniquement récupérée dynamiquement depuis Vault au démarrage du process.

Chemins des secrets : secret/tenants/poc/llm/<provider>, clé "api_key" (voir RUNBOOK.md
racine pour les commandes `vault kv put` exactes déjà exécutées pour anthropic et gemini).

Essaie d'abord le format KV v2 (mount "secret/" avec kv-v2, confirmé sur cette instance
Vault via /v1/sys/mounts), puis retombe sur KV v1 par prudence si jamais l'instance change.
"""

import os

import aiohttp
from loguru import logger

VAULT_ADDR = os.environ.get("VAULT_ADDR", "http://localhost:8300")
VAULT_TOKEN = os.environ.get("VAULT_TOKEN")
SECRET_KEY = "api_key"


async def fetch_llm_api_key(provider: str) -> str:
    if not VAULT_TOKEN:
        raise RuntimeError(
            "VAULT_TOKEN n'est pas défini. Ce service ne doit jamais utiliser le token root "
            "en dehors de ce POC local — voir RUNBOOK.md pour créer une policy dédiée avant "
            "toute mise en environnement partagé."
        )

    secret_path = f"tenants/poc/llm/{provider}"
    headers = {"X-Vault-Token": VAULT_TOKEN}

    async with aiohttp.ClientSession(headers=headers) as session:
        # Tentative KV v2 : GET /v1/secret/data/<path>, secret dans json["data"]["data"]
        v2_url = f"{VAULT_ADDR}/v1/secret/data/{secret_path}"
        async with session.get(v2_url) as resp:
            if resp.status == 200:
                body = await resp.json()
                api_key = body["data"]["data"].get(SECRET_KEY)
                if api_key:
                    logger.info(f"Clé {provider} récupérée depuis Vault (KV v2).")
                    return api_key

        # Repli KV v1 : GET /v1/secret/<path>, secret dans json["data"]
        v1_url = f"{VAULT_ADDR}/v1/secret/{secret_path}"
        async with session.get(v1_url) as resp:
            if resp.status == 200:
                body = await resp.json()
                api_key = body["data"].get(SECRET_KEY)
                if api_key:
                    logger.info(f"Clé {provider} récupérée depuis Vault (KV v1).")
                    return api_key

    raise RuntimeError(
        f"Impossible de récupérer le secret '{provider}' depuis Vault (chemin '{secret_path}', "
        f"clé '{SECRET_KEY}'). Vérifier que le secret a bien été écrit et que le token a accès."
    )
