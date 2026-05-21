from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .client import KommoClient

DEFAULT_WON_STATUS_IDS = {142}
DEFAULT_LOST_STATUS_IDS = {143}


def _to_dt(value: Optional[int]) -> Optional[datetime]:
    if not value:
        return None
    return datetime.fromtimestamp(int(value), tz=timezone.utc)


def _bucket_key(dt: datetime, interval: str) -> str:
    if interval == "week":
        start = dt - timedelta(days=dt.weekday())
        return start.strftime("%Y-%m-%d")
    return dt.strftime("%Y-%m-%d")


def _daterange_keys(days: int, interval: str) -> List[str]:
    now = datetime.now(tz=timezone.utc)
    start = now - timedelta(days=days - 1)
    current = start.replace(hour=0, minute=0, second=0, microsecond=0)
    keys = []
    if interval == "week":
        current = current - timedelta(days=current.weekday())
        while current <= now:
            keys.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=7)
    else:
        while current <= now:
            keys.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)
    return keys


def _sum_price(leads: Iterable[Dict[str, Any]]) -> int:
    return int(sum((lead.get("price") or 0) for lead in leads))


def _avg(values: Iterable[float]) -> float:
    values = list(values)
    return round(sum(values) / len(values), 2) if values else 0.0


def _tags(lead: Dict[str, Any]) -> List[str]:
    return [tag.get("name", "").strip().lower() for tag in lead.get("_embedded", {}).get("tags", []) if tag.get("name")]


def _custom_field_value(lead: Dict[str, Any], field_name: str) -> Optional[str]:
    for field in lead.get("custom_fields_values") or []:
        if field.get("field_name") == field_name and field.get("values"):
            return field["values"][0].get("value")
    return None


def _build_pipeline_maps(pipelines: List[Dict[str, Any]]) -> Tuple[Dict[int, str], Dict[int, Dict[str, Any]]]:
    pipeline_names: Dict[int, str] = {}
    statuses: Dict[int, Dict[str, Any]] = {}
    for pipeline in pipelines:
        pipeline_id = pipeline.get("id")
        pipeline_names[pipeline_id] = pipeline.get("name", f"Pipeline {pipeline_id}")
        for status in pipeline.get("_embedded", {}).get("statuses", []):
            statuses[status["id"]] = {
                "status_name": status.get("name", f"Etapa {status.get('id')}") ,
                "pipeline_id": pipeline_id,
                "pipeline_name": pipeline.get("name", f"Pipeline {pipeline_id}"),
                "type": status.get("type"),
            }
    return pipeline_names, statuses


def _owner_name(users_by_id: Dict[int, str], owner_id: Optional[int]) -> str:
    if owner_id is None:
        return "Sem responsável"
    return users_by_id.get(owner_id, f"Usuário {owner_id}")


def collect_decision_snapshot(
    client: KommoClient,
    days: int = 30,
    max_pages: int = 50,
    include_extended: bool = False,
) -> Dict[str, Any]:
    now_ts = int(datetime.now(tz=timezone.utc).timestamp())
    from_ts = int((datetime.now(tz=timezone.utc) - timedelta(days=days)).timestamp())

    # Primeiro, pegamos os pipelines para descobrir todos os IDs de status Ganhos/Perdidos
    pipelines_data = client.fetch_resource("pipelines", all_pages=True)
    won_ids = {142}
    lost_ids = {143}
    
    for pipe in pipelines_data.get("data", []):
        for status in pipe.get("_embedded", {}).get("statuses", []):
            if status.get("type") == 3: # Ganhos
                won_ids.add(status["id"])
            elif status.get("type") == 2: # Perdidos
                lost_ids.add(status["id"])

    snapshot: Dict[str, Any] = {
        "meta": {
            "days": days,
            "generated_at": datetime.now(tz=timezone.utc).isoformat(),
            "from_ts": from_ts,
            "to_ts": now_ts,
            "won_status_ids": list(won_ids),
            "lost_status_ids": list(lost_ids),
        },
        "account": client.fetch_resource("account"),
        "users": client.fetch_resource("users", all_pages=True, max_pages=max_pages),
        "pipelines": pipelines_data,
        "lead_custom_fields": client.fetch_resource("lead-custom-fields", all_pages=True, max_pages=max_pages),
        "active_leads": client.fetch_resource(
            "leads",
            params={"with": "contacts,companies,tags"},
            all_pages=True,
            max_pages=max_pages,
        ),
        "created_leads": client.fetch_resource(
            "leads",
            params={
                "filter[created_at][from]": from_ts,
                "filter[created_at][to]": now_ts,
                "with": "contacts,companies,tags",
            },
            all_pages=True,
            max_pages=max_pages,
        ),
        "won_leads": client.fetch_resource(
            "leads",
            params={
                "filter[closed_at][from]": from_ts,
                "filter[closed_at][to]": now_ts,
                "filter[statuses][0][status_id]": 142, # Mantemos o padrão para o filtro inicial
                "with": "contacts,companies,tags",
            },
            all_pages=True,
            max_pages=max_pages,
        ),
        "lost_leads": client.fetch_resource(
            "leads",
            params={
                "filter[closed_at][from]": from_ts,
                "filter[closed_at][to]": now_ts,
                "filter[statuses][0][status_id]": 143, # Mantemos o padrão para o filtro inicial
                "with": "loss_reason,tags",
            },
            all_pages=True,
            max_pages=max_pages,
        ),
        "open_tasks": client.fetch_resource(
            "tasks",
            params={"filter[is_completed]": 0},
            all_pages=True,
            max_pages=max_pages,
        ),
        "events": client.fetch_resource(
            "events",
            params={"filter[created_at][from]": from_ts},
            all_pages=True,
            max_pages=max_pages,
        ),
    }

    if include_extended:
        snapshot["contacts"] = client.fetch_resource("contacts", all_pages=True, max_pages=max_pages)
        snapshot["companies"] = client.fetch_resource("companies", all_pages=True, max_pages=max_pages)
        snapshot["events_types"] = client.fetch_resource("events-types")
        snapshot["lead_notes"] = client.fetch_resource("lead-notes", all_pages=True, max_pages=max_pages)

    return snapshot


def build_decision_report(
    snapshot: Dict[str, Any],
    interval: str = "day",
    stale_days: int = 7,
    top_n: int = 10,
    won_status_ids: Optional[set[int]] = None,
    lost_status_ids: Optional[set[int]] = None,
) -> Dict[str, Any]:
    # Prioriza IDs dinâmicos vindos do snapshot se não forem passados explicitamente
    meta_won = snapshot.get("meta", {}).get("won_status_ids")
    meta_lost = snapshot.get("meta", {}).get("lost_status_ids")
    
    won_status_ids = won_status_ids or (set(meta_won) if meta_won else DEFAULT_WON_STATUS_IDS)
    lost_status_ids = lost_status_ids or (set(meta_lost) if meta_lost else DEFAULT_LOST_STATUS_IDS)

    account = snapshot.get("account", {})
    users = snapshot.get("users", {}).get("data", [])
    pipelines = snapshot.get("pipelines", {}).get("data", [])
    lead_custom_fields = snapshot.get("lead_custom_fields", {}).get("data", [])
    all_leads = snapshot.get("active_leads", {}).get("data", [])
    created_leads = snapshot.get("created_leads", {}).get("data", [])
    won_leads = snapshot.get("won_leads", {}).get("data", [])
    lost_leads = snapshot.get("lost_leads", {}).get("data", [])
    open_tasks = snapshot.get("open_tasks", {}).get("data", [])
    events = snapshot.get("events", {}).get("data", [])

    # Importante: Como a API pode falhar no filtro de status_id, fazemos uma segunda camada de filtragem manual
    # Baseado nos IDs que descobrimos dinamicamente
    all_closed_leads = created_leads + won_leads + lost_leads
    
    # Dedup por ID para evitar contagem dupla
    unique_leads = {l["id"]: l for l in all_closed_leads}.values()
    
    real_won = [l for l in unique_leads if l.get("status_id") in won_status_ids]
    real_lost = [l for l in unique_leads if l.get("status_id") in lost_status_ids]
    
    won_leads = real_won if real_won else won_leads
    lost_leads = real_lost if real_lost else lost_leads

    users_by_id = {user["id"]: user.get("name", f"Usuário {user['id']}") for user in users}
    pipeline_names, statuses = _build_pipeline_maps(pipelines)

    active_leads = [lead for lead in all_leads if lead.get("status_id") not in won_status_ids | lost_status_ids]
    now_ts = snapshot.get("meta", {}).get("to_ts") or int(datetime.now(tz=timezone.utc).timestamp())
    stale_limit = now_ts - stale_days * 86400

    created_ids = {lead.get("id") for lead in created_leads}
    won_same_window = [lead for lead in won_leads if lead.get("id") in created_ids]

    overview = {
        "leads_created": len(created_leads),
        "active_leads": len(active_leads),
        "won_leads": len(won_leads),
        "lost_leads": len(lost_leads),
        "revenue_won": _sum_price(won_leads),
        "active_pipeline_value": _sum_price(active_leads),
        "win_rate_over_decisions": round((len(won_leads) / max(1, len(won_leads) + len(lost_leads))) * 100, 2),
        "same_window_created_to_won_rate": round((len(won_same_window) / max(1, len(created_leads))) * 100, 2),
        "avg_ticket_won": round(_sum_price(won_leads) / max(1, len(won_leads)), 2),
        "avg_cycle_days_won": _avg(
            (lead["closed_at"] - lead["created_at"]) / 86400
            for lead in won_leads
            if lead.get("closed_at") and lead.get("created_at")
        ),
    }

    keys = _daterange_keys(snapshot.get("meta", {}).get("days", 30), interval)
    series_map = {
        key: {"bucket": key, "created": 0, "won": 0, "lost": 0, "revenue_won": 0}
        for key in keys
    }
    for lead in created_leads:
        dt = _to_dt(lead.get("created_at"))
        if dt:
            series_map.setdefault(_bucket_key(dt, interval), {"bucket": _bucket_key(dt, interval), "created": 0, "won": 0, "lost": 0, "revenue_won": 0})["created"] += 1
    for lead in won_leads:
        dt = _to_dt(lead.get("closed_at"))
        if dt:
            bucket = _bucket_key(dt, interval)
            series_map.setdefault(bucket, {"bucket": bucket, "created": 0, "won": 0, "lost": 0, "revenue_won": 0})
            series_map[bucket]["won"] += 1
            series_map[bucket]["revenue_won"] += int(lead.get("price") or 0)
    for lead in lost_leads:
        dt = _to_dt(lead.get("closed_at"))
        if dt:
            bucket = _bucket_key(dt, interval)
            series_map.setdefault(bucket, {"bucket": bucket, "created": 0, "won": 0, "lost": 0, "revenue_won": 0})
            series_map[bucket]["lost"] += 1
    series = [series_map[key] for key in sorted(series_map.keys())]

    pipeline_summary = []
    by_pipeline_active = defaultdict(list)
    by_pipeline_won = defaultdict(list)
    by_pipeline_lost = defaultdict(list)
    for lead in active_leads:
        by_pipeline_active[lead.get("pipeline_id")].append(lead)
    for lead in won_leads:
        by_pipeline_won[lead.get("pipeline_id")].append(lead)
    for lead in lost_leads:
        by_pipeline_lost[lead.get("pipeline_id")].append(lead)
    for pipeline in pipelines:
        pipeline_id = pipeline["id"]
        active = by_pipeline_active.get(pipeline_id, [])
        won = by_pipeline_won.get(pipeline_id, [])
        lost = by_pipeline_lost.get(pipeline_id, [])
        pipeline_summary.append({
            "pipeline_id": pipeline_id,
            "pipeline_name": pipeline.get("name"),
            "active_count": len(active),
            "active_value": _sum_price(active),
            "won_count": len(won),
            "won_value": _sum_price(won),
            "lost_count": len(lost),
            "decision_win_rate": round((len(won) / max(1, len(won) + len(lost))) * 100, 2),
        })
    pipeline_summary.sort(key=lambda item: (-item["won_value"], -item["active_value"], item["pipeline_name"] or ""))

    stage_summary = []
    by_stage = defaultdict(list)
    for lead in active_leads:
        by_stage[lead.get("status_id")].append(lead)
    for status_id, leads in by_stage.items():
        info = statuses.get(status_id, {})
        stage_summary.append({
            "status_id": status_id,
            "stage_name": info.get("status_name", f"Etapa {status_id}"),
            "pipeline_name": info.get("pipeline_name", pipeline_names.get(leads[0].get("pipeline_id"), "Sem pipeline")),
            "active_count": len(leads),
            "active_value": _sum_price(leads),
            "stale_count": sum(1 for lead in leads if (lead.get("updated_at") or 0) < stale_limit),
        })
    stage_summary.sort(key=lambda item: (-item["active_value"], -item["active_count"], item["stage_name"]))

    owner_map: Dict[int | None, Dict[str, Any]] = defaultdict(lambda: {
        "owner_id": None,
        "owner_name": "",
        "active_count": 0,
        "active_value": 0,
        "won_count": 0,
        "won_value": 0,
        "lost_count": 0,
        "stale_active_count": 0,
        "open_tasks": 0,
        "overdue_tasks": 0,
    })
    for lead in active_leads:
        owner_id = lead.get("responsible_user_id")
        entry = owner_map[owner_id]
        entry["owner_id"] = owner_id
        entry["owner_name"] = _owner_name(users_by_id, owner_id)
        entry["active_count"] += 1
        entry["active_value"] += int(lead.get("price") or 0)
        if (lead.get("updated_at") or 0) < stale_limit:
            entry["stale_active_count"] += 1
    for lead in won_leads:
        owner_id = lead.get("responsible_user_id")
        entry = owner_map[owner_id]
        entry["owner_id"] = owner_id
        entry["owner_name"] = _owner_name(users_by_id, owner_id)
        entry["won_count"] += 1
        entry["won_value"] += int(lead.get("price") or 0)
    for lead in lost_leads:
        owner_id = lead.get("responsible_user_id")
        entry = owner_map[owner_id]
        entry["owner_id"] = owner_id
        entry["owner_name"] = _owner_name(users_by_id, owner_id)
        entry["lost_count"] += 1
    for task in open_tasks:
        owner_id = task.get("responsible_user_id")
        entry = owner_map[owner_id]
        entry["owner_id"] = owner_id
        entry["owner_name"] = _owner_name(users_by_id, owner_id)
        entry["open_tasks"] += 1
        if (task.get("complete_till") or 0) < now_ts:
            entry["overdue_tasks"] += 1
    owner_summary = []
    for entry in owner_map.values():
        decisions = entry["won_count"] + entry["lost_count"]
        entry["win_rate"] = round((entry["won_count"] / max(1, decisions)) * 100, 2)
        entry["avg_ticket_won"] = round(entry["won_value"] / max(1, entry["won_count"]), 2)
        owner_summary.append(entry)
    owner_summary.sort(key=lambda item: (-item["won_value"], -item["active_value"], item["owner_name"]))

    loss_reasons = Counter()
    for lead in lost_leads:
        reasons = lead.get("_embedded", {}).get("loss_reason", [])
        if not reasons:
            loss_reasons["Sem motivo registrado"] += 1
        for reason in reasons:
            loss_reasons[reason.get("name", "Sem motivo registrado")] += 1

    stale_leads = []
    for lead in active_leads:
        updated_at = lead.get("updated_at") or 0
        if updated_at >= stale_limit:
            continue
        status_info = statuses.get(lead.get("status_id"), {})
        stale_leads.append({
            "lead_id": lead.get("id"),
            "lead_name": lead.get("name"),
            "pipeline_name": status_info.get("pipeline_name", pipeline_names.get(lead.get("pipeline_id"), "Sem pipeline")),
            "stage_name": status_info.get("status_name", f"Etapa {lead.get('status_id')}"),
            "owner_name": _owner_name(users_by_id, lead.get("responsible_user_id")),
            "price": int(lead.get("price") or 0),
            "updated_at": updated_at,
            "days_without_update": round((now_ts - updated_at) / 86400, 1),
            "tags": _tags(lead),
        })
    stale_leads.sort(key=lambda item: (-item["price"], -item["days_without_update"]))

    open_task_summary = {
        "open_tasks": len(open_tasks),
        "overdue_tasks": sum(1 for task in open_tasks if (task.get("complete_till") or 0) < now_ts),
        "tasks_due_today": sum(1 for task in open_tasks if datetime.fromtimestamp(task.get("complete_till") or 0, tz=timezone.utc).date() == datetime.now(tz=timezone.utc).date()),
        "by_type": Counter(str(task.get("task_type_id", "unknown")) for task in open_tasks).most_common(top_n),
    }

    event_type_counts = Counter(event.get("type", "unknown") for event in events)
    stage_change_events = []
    for event in events:
        if event.get("type") != "lead_status_changed":
            continue
        before = (event.get("value_before") or [{}])[0].get("lead_status", {})
        after = (event.get("value_after") or [{}])[0].get("lead_status", {})
        before_status = statuses.get(before.get("id"), {})
        after_status = statuses.get(after.get("id"), {})
        stage_change_events.append({
            "created_at": event.get("created_at"),
            "entity_id": event.get("entity_id"),
            "from_stage": before_status.get("status_name", before.get("id")),
            "to_stage": after_status.get("status_name", after.get("id")),
            "pipeline_name": after_status.get("pipeline_name") or before_status.get("pipeline_name"),
            "to_won": after.get("id") in won_status_ids,
            "to_lost": after.get("id") in lost_status_ids,
        })
    stage_transition_counts = Counter(
        f"{item['pipeline_name'] or 'Sem pipeline'} | {item['from_stage']} -> {item['to_stage']}"
        for item in stage_change_events
    )

    tag_counts = Counter()
    for lead in created_leads + won_leads + lost_leads:
        tag_counts.update(_tags(lead))

    dentista_summary = Counter()
    for lead in won_leads:
        dentista_summary[_custom_field_value(lead, "Dentista") or "Não informado"] += int(lead.get("price") or 0)

    custom_field_catalog = [
        {
            "field_id": field.get("id"),
            "field_name": field.get("name"),
            "field_type": field.get("type"),
            "is_required": field.get("is_required"),
        }
        for field in lead_custom_fields[:200]
    ]

    return {
        "meta": snapshot.get("meta", {}),
        "account": {
            "id": account.get("id"),
            "name": account.get("name"),
            "subdomain": account.get("subdomain"),
            "users_count": len(users),
            "pipelines_count": len(pipelines),
        },
        "overview": overview,
        "series": series,
        "pipeline_summary": pipeline_summary,
        "stage_summary": stage_summary[: max(top_n, 20)],
        "owner_summary": owner_summary[: max(top_n, 20)],
        "loss_reasons": [{"reason": reason, "count": count} for reason, count in loss_reasons.most_common(top_n)],
        "stale_leads": stale_leads[:top_n],
        "task_summary": open_task_summary,
        "events_summary": {
            "top_event_types": [{"type": event_type, "count": count} for event_type, count in event_type_counts.most_common(top_n)],
            "top_stage_transitions": [{"transition": name, "count": count} for name, count in stage_transition_counts.most_common(top_n)],
            "won_stage_changes": sum(1 for item in stage_change_events if item["to_won"]),
            "lost_stage_changes": sum(1 for item in stage_change_events if item["to_lost"]),
        },
        "tag_summary": [{"tag": tag, "count": count} for tag, count in tag_counts.most_common(top_n)],
        "dentista_revenue": [{"dentista": name, "revenue": value} for name, value in dentista_summary.most_common(top_n)],
        "custom_field_catalog": custom_field_catalog,
    }
