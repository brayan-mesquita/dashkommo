#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from kommo_analytics.client import KommoClient
from kommo_analytics.reporting import build_decision_report, collect_decision_snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera snapshot e relatório analítico genérico do Kommo")
    sub = parser.add_subparsers(dest="command", required=True)

    snapshot_cmd = sub.add_parser("snapshot", help="coletar snapshot bruto para análise")
    snapshot_cmd.add_argument("--env-file", help="arquivo com KOMMO_SUBDOMAIN e KOMMO_ACCESS_TOKEN")
    snapshot_cmd.add_argument("--days", type=int, default=30, help="janela em dias")
    snapshot_cmd.add_argument("--max-pages", type=int, default=50, help="máximo de páginas por recurso")
    snapshot_cmd.add_argument("--include-extended", action="store_true", help="incluir contatos, empresas, notes e event types")
    snapshot_cmd.add_argument("--output", help="arquivo para salvar o snapshot JSON")

    report_cmd = sub.add_parser("report", help="gerar relatório analítico a partir do Kommo")
    report_cmd.add_argument("--env-file", help="arquivo com KOMMO_SUBDOMAIN e KOMMO_ACCESS_TOKEN")
    report_cmd.add_argument("--days", type=int, default=30, help="janela em dias")
    report_cmd.add_argument("--interval", choices=["day", "week"], default="day", help="granularidade da série")
    report_cmd.add_argument("--stale-days", type=int, default=7, help="dias para considerar lead parado")
    report_cmd.add_argument("--top", type=int, default=10, help="quantidade de itens nas listas principais")
    report_cmd.add_argument("--max-pages", type=int, default=50, help="máximo de páginas por recurso")
    report_cmd.add_argument("--include-extended", action="store_true", help="incluir contatos, empresas, notes e event types")
    report_cmd.add_argument("--snapshot-output", help="salvar também o snapshot bruto")
    report_cmd.add_argument("--output", help="arquivo para salvar o relatório JSON")

    args = parser.parse_args()
    client = KommoClient.from_env(env_file=getattr(args, "env_file", None), search_from=str(CURRENT_DIR))

    snapshot = collect_decision_snapshot(
        client=client,
        days=args.days,
        max_pages=args.max_pages,
        include_extended=getattr(args, "include_extended", False),
    )

    if args.command == "snapshot":
        rendered = json.dumps(snapshot, ensure_ascii=False, indent=2)
        if args.output:
            out = Path(args.output).expanduser()
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(rendered + "\n", encoding="utf-8")
        print(rendered)
        return 0

    if args.snapshot_output:
        out = Path(args.snapshot_output).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = build_decision_report(
        snapshot=snapshot,
        interval=args.interval,
        stale_days=args.stale_days,
        top_n=args.top,
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        out = Path(args.output).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
