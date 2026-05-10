#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from kommo_analytics.client import KommoClient


def parse_params(items: List[str]) -> Dict[str, str]:
    params: Dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise SystemExit(f"Parâmetro inválido: {item}. Use chave=valor")
        key, value = item.split("=", 1)
        params[key] = value
    return params


def main() -> int:
    parser = argparse.ArgumentParser(description="Busca dados da API do Kommo por alias ou path bruto")
    parser.add_argument("resource_or_path", nargs="?", help="alias conhecido (ex: leads) ou path /api/v4/...")
    parser.add_argument("--list-resources", action="store_true", help="listar aliases suportados")
    parser.add_argument("--env-file", help="arquivo com KOMMO_SUBDOMAIN e KOMMO_ACCESS_TOKEN")
    parser.add_argument("--param", action="append", default=[], help="parâmetro extra no formato chave=valor")
    parser.add_argument("--limit", type=int, default=250, help="limite por página")
    parser.add_argument("--page", type=int, default=1, help="página inicial")
    parser.add_argument("--all-pages", action="store_true", help="buscar todas as páginas até acabar")
    parser.add_argument("--max-pages", type=int, default=50, help="máximo de páginas quando usar --all-pages")
    parser.add_argument("--output", help="arquivo para salvar o JSON")
    args = parser.parse_args()

    if args.list_resources:
        for resource in KommoClient.available_resources():
            print(resource)
        return 0
    if not args.resource_or_path:
        parser.error("informe um alias ou path bruto /api/v4/...")

    client = KommoClient.from_env(env_file=args.env_file, search_from=str(CURRENT_DIR))
    params = parse_params(args.param)
    result = client.fetch_resource(
        args.resource_or_path,
        params=params,
        all_pages=args.all_pages,
        start_page=args.page,
        max_pages=args.max_pages,
        limit=args.limit,
    )
    rendered = client.dump_json(result, output=args.output)
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
