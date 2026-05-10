from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import requests


@dataclass(frozen=True)
class KommoResourceConfig:
    path: str
    embedded_key: Optional[str] = None
    paginated: bool = True


KOMMO_RESOURCE_MAP: Dict[str, KommoResourceConfig] = {
    "account": KommoResourceConfig("/api/v4/account", paginated=False),
    "users": KommoResourceConfig("/api/v4/users", embedded_key="users"),
    "pipelines": KommoResourceConfig("/api/v4/leads/pipelines", embedded_key="pipelines"),
    "leads": KommoResourceConfig("/api/v4/leads", embedded_key="leads"),
    "contacts": KommoResourceConfig("/api/v4/contacts", embedded_key="contacts"),
    "companies": KommoResourceConfig("/api/v4/companies", embedded_key="companies"),
    "tasks": KommoResourceConfig("/api/v4/tasks", embedded_key="tasks"),
    "events": KommoResourceConfig("/api/v4/events", embedded_key="events"),
    "events-types": KommoResourceConfig("/api/v4/events/types", paginated=False),
    "lead-notes": KommoResourceConfig("/api/v4/leads/notes", embedded_key="notes"),
    "contact-notes": KommoResourceConfig("/api/v4/contacts/notes", embedded_key="notes"),
    "company-notes": KommoResourceConfig("/api/v4/companies/notes", embedded_key="notes"),
    "lead-custom-fields": KommoResourceConfig("/api/v4/leads/custom_fields", embedded_key="custom_fields"),
    "contact-custom-fields": KommoResourceConfig("/api/v4/contacts/custom_fields", embedded_key="custom_fields"),
    "company-custom-fields": KommoResourceConfig("/api/v4/companies/custom_fields", embedded_key="custom_fields"),
    "catalogs": KommoResourceConfig("/api/v4/catalogs", embedded_key="catalogs"),
}


def _load_env_line(raw: str) -> Optional[tuple[str, str]]:
    line = raw.strip()
    if not line or line.startswith("#") or "=" not in line:
        return None
    key, value = line.split("=", 1)
    return key.strip(), value.strip().strip('"').strip("'")


class KommoClient:
    def __init__(self, subdomain: str, access_token: str, timeout: int = 60):
        self.subdomain = subdomain.strip()
        self.access_token = access_token.strip()
        self.timeout = timeout
        if not self.subdomain or not self.access_token:
            raise ValueError("KOMMO_SUBDOMAIN e KOMMO_ACCESS_TOKEN são obrigatórios")
        self.base_url = f"https://{self.subdomain}.kommo.com"

    @classmethod
    def from_env(cls, env_file: Optional[str] = None, search_from: Optional[str] = None) -> "KommoClient":
        cls.load_env(env_file=env_file, search_from=search_from)
        subdomain = os.getenv("KOMMO_SUBDOMAIN")
        token = os.getenv("KOMMO_ACCESS_TOKEN")
        if not subdomain or not token:
            missing = [
                key
                for key in ("KOMMO_SUBDOMAIN", "KOMMO_ACCESS_TOKEN")
                if not os.getenv(key)
            ]
            raise SystemExit("Credenciais ausentes. Defina: " + ", ".join(missing))
        return cls(subdomain=subdomain, access_token=token)

    @staticmethod
    def load_env(env_file: Optional[str] = None, search_from: Optional[str] = None) -> None:
        candidates = []
        if env_file:
            candidates.append(Path(env_file).expanduser())
        if search_from:
            origin = Path(search_from).resolve()
            for candidate in [
                origin / ".env.kommo",
                origin.parent / ".env.kommo",
                origin.parent.parent / ".env.kommo",
                origin.parent.parent.parent / ".env.kommo",
            ]:
                candidates.append(candidate)
        for candidate in candidates:
            if candidate.exists():
                for line in candidate.read_text(encoding="utf-8").splitlines():
                    parsed = _load_env_line(line)
                    if parsed:
                        os.environ.setdefault(parsed[0], parsed[1])

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "openclaw-kommo-analytics/1.0",
        }

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as exc:
            body = exc.response.text if exc.response is not None else ""
            raise SystemExit(f"Erro HTTP ao consultar {url}: {body}") from exc
        except ValueError as exc:
            raise SystemExit(f"Resposta não-JSON ao consultar {url}: {exc}") from exc
        except requests.RequestException as exc:
            raise SystemExit(f"Erro de conexão ao consultar {url}: {exc}") from exc

    def get_paginated(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        embedded_key: Optional[str] = None,
        all_pages: bool = False,
        start_page: int = 1,
        max_pages: int = 50,
        limit: int = 250,
    ) -> Dict[str, Any]:
        query = dict(params or {})
        query.setdefault("limit", limit)
        page = start_page
        pages_fetched = 0
        collected = []
        last_payload: Optional[Dict[str, Any]] = None

        while True:
            page_query = dict(query)
            page_query["page"] = page
            payload = self.get(path, params=page_query)
            last_payload = payload
            current_embedded_key = embedded_key or self._guess_embedded_key(payload)
            items = payload.get("_embedded", {}).get(current_embedded_key or "", [])
            collected.extend(items)
            pages_fetched += 1

            if not all_pages:
                break
            if not items or len(items) < int(page_query["limit"]):
                break
            if pages_fetched >= max_pages:
                break
            page += 1

        return {
            "path": path,
            "embedded_key": embedded_key or self._guess_embedded_key(last_payload or {}),
            "pages_fetched": pages_fetched,
            "records": len(collected),
            "data": collected,
            "last_page": last_payload,
        }

    def fetch_resource(
        self,
        resource_or_path: str,
        params: Optional[Dict[str, Any]] = None,
        all_pages: bool = False,
        start_page: int = 1,
        max_pages: int = 50,
        limit: int = 250,
    ) -> Dict[str, Any]:
        config = KOMMO_RESOURCE_MAP.get(resource_or_path)
        if config:
            if config.paginated:
                return self.get_paginated(
                    config.path,
                    params=params,
                    embedded_key=config.embedded_key,
                    all_pages=all_pages,
                    start_page=start_page,
                    max_pages=max_pages,
                    limit=limit,
                )
            return self.get(config.path, params=params)

        if resource_or_path.startswith("/api/"):
            if all_pages:
                return self.get_paginated(
                    resource_or_path,
                    params=params,
                    embedded_key=None,
                    all_pages=True,
                    start_page=start_page,
                    max_pages=max_pages,
                    limit=limit,
                )
            return self.get(resource_or_path, params=params)

        raise SystemExit(
            f"Recurso desconhecido: {resource_or_path}. Use um alias conhecido ou um path bruto /api/v4/..."
        )

    @staticmethod
    def _guess_embedded_key(payload: Dict[str, Any]) -> Optional[str]:
        embedded = payload.get("_embedded") or {}
        keys = list(embedded.keys())
        return keys[0] if keys else None

    @staticmethod
    def dump_json(data: Any, output: Optional[str] = None) -> str:
        rendered = json.dumps(data, ensure_ascii=False, indent=2)
        if output:
            out = Path(output).expanduser()
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(rendered + "\n", encoding="utf-8")
        return rendered

    @staticmethod
    def available_resources() -> Iterable[str]:
        return sorted(KOMMO_RESOURCE_MAP.keys())
