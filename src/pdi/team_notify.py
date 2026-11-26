"""DI Team T6 (docs/plan-t6-skroty-slack.md): „Ask team” i dzienny skrót do Slacka przez DI Channels.

Dwie wiadomości do DI Channels, z tym samym podpisem co „czeka na Ciebie” (`X-PDI-Signature`, `PDI_CHANNELS_*`):
- `POST /pdi/asked` (`team.asked`): przy „Ask team” każda zapytana osoba dostaje wiadomość prywatną. pdi wysyła tylko
  `sub` osób z suity; DI Channels sam szuka ich w Slacku przez di-identity, więc e-mail nie przechodzi przez pdi.
  Odpowiedź mówi, kogo nie znaleziono; ta lista zostaje przy konsultacji (`unreachable`).
- `POST /pdi/digest` (`team.digest`): raz dziennie skrót dla zatwierdzającego (co czeka, w kolejności pilności;
  pytania u zespołu; agenda „Discuss”) i dla każdej osoby, na której odpowiedź czeka pytanie. Pusty skrót nie idzie.
  `id` = `digest-<odbiorca>-<dzień>`, więc drugie uruchomienie tego samego dnia DI Channels uzna za powtórkę.

To nie są zdarzenia kontraktu: odbiorcą jest osoba, jak przy `gate.waiting`. Błąd wysyłki nigdy nie cofa pytania.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from pdi import agenda, consult, escalate, waiting
from pdi.notify import LOCAL_HOSTS, TIMEOUT_SECONDS

ASKED_PATH = "/pdi/asked"
ESCALATED_PATH = "/pdi/escalated"
DIGEST_PATH = "/pdi/digest"
MAX_ITEMS = 10

JsonPost = Callable[[str, dict[str, str], bytes], tuple[int, bytes]]

# Od najpilniejszego (OM1 §4–§5): do przeglądu, wstrzymana, po terminie, termin dziś, przypomnienie, nowa.
_URGENCY = ["review", "paused", "overdue", "due_today", "reminder", "new"]


def _post_json(url: str, headers: dict[str, str], body: bytes) -> tuple[int, bytes]:
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")  # noqa: S310 — adres sprawdzony
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:  # noqa: S310
            return int(response.status), response.read(64 * 1024)
    except urllib.error.HTTPError as e:
        return int(e.code), b""


def _send(
    config: waiting.ChannelsConfig, path: str, message: dict[str, Any], post: JsonPost | None, now: int | None
) -> tuple[dict[str, Any], Any]:
    """Podpisany POST do DI Channels: (`{"status": sent | skipped | failed, …}`, odpowiedź JSON albo None)."""
    if not config.url:
        return {"status": "skipped", "error": "Brak PDI_CHANNELS_URL — wiadomość do Slacka nie wysłana."}, None
    url = urllib.parse.urlsplit(config.url)
    if (
        url.username
        or url.password
        or not (url.scheme == "https" or (url.scheme == "http" and url.hostname in LOCAL_HOSTS))
    ):
        return {
            "status": "failed",
            "error": "PDI_CHANNELS_URL musi być adresem https:// (http tylko dla localhost), bez loginu.",
        }, None
    if not config.secret:
        return {"status": "failed", "error": "Brak PDI_CHANNELS_SIGNING_SECRET — wiadomość nie została wysłana."}, None
    body = json.dumps(message, ensure_ascii=False).encode()
    ts = str(now if now is not None else int(time.time()))
    signature = "v1=" + hmac.new(config.secret.encode(), ts.encode() + b"." + body, hashlib.sha256).hexdigest()
    headers = {
        "content-type": "application/json",
        "x-pdi-timestamp": ts,
        "x-pdi-event": str(message["type"]),
        "x-pdi-signature": signature,
    }
    try:
        status, raw = (post or _post_json)(config.url.rstrip("/") + path, headers, body)
    except OSError:
        return {"status": "failed", "error": "Nie udało się nawiązać połączenia: DI Channels."}, None
    if not 200 <= status < 300:
        return {"status": "failed", "error": f"DI Channels odpowiedział {status} na {message['type']}."}, None
    try:
        return {"status": "sent"}, json.loads(raw or b"null")
    except ValueError:
        return {"status": "sent"}, None


def _link(config: waiting.ChannelsConfig, page: str) -> dict[str, str]:
    """Link do strony konsoli, nigdy z tokenem sesji (token nie może trafić do komunikatora)."""
    return {"url": f"{config.console_url.rstrip('/')}/{page}"} if config.console_url else {}


def asked_message(item: dict[str, Any], c: dict[str, Any], config: waiting.ChannelsConfig) -> dict[str, Any]:
    """Treść `team.asked`: kto pyta, o co, jakie opcje, do kiedy; bez odpowiedzi innych i bez treści artefaktów."""
    out: dict[str, Any] = {
        "type": "team.asked",
        "id": f"asked-{item['id']}-{c['asked_at']}"[:128],
        "item": item["id"],
        "summary": str(item.get("summary") or item["id"])[:300],
        "asked_by": c["decider"]["name"][:80],
        "people": [a["sub"] for a in c["asked"]],
        "options": list(c["options"]),
        "closes_at": c["closes_at"],
        **_link(config, "inbox"),
    }
    for key in ("change", "gate"):
        if item.get(key):
            out[key] = item[key]
    return out


def notify_asked(
    config: waiting.ChannelsConfig,
    item: dict[str, Any],
    c: dict[str, Any],
    *,
    at: str,
    post: JsonPost | None = None,
    now: int | None = None,
) -> dict[str, Any]:
    """Wysyła `team.asked`; wynik do zapisu przy konsultacji, z nazwami osób, których DI Channels nie znalazł."""
    sent, answer = _send(config, ASKED_PATH, asked_message(item, c, config), post, now)
    result: dict[str, Any] = {**sent, "at": at}
    if sent["status"] == "sent":
        names = {a["sub"]: a["name"] for a in c["asked"]}
        delivered = answer.get("delivered") if isinstance(answer, dict) else None
        rows = delivered if isinstance(delivered, list) else []
        result["unreachable"] = [
            names[r["person"]]
            for r in rows
            if isinstance(r, dict) and r.get("status") in ("not_in_slack", "failed") and r.get("person") in names
        ]
    return result


def notify_escalated(
    config: waiting.ChannelsConfig,
    item: dict[str, Any],
    e: dict[str, Any],
    *,
    at: str,
    post: JsonPost | None = None,
    now: int | None = None,
) -> dict[str, Any]:
    """Wysyła `team.escalated` (T7): adresat dostaje wiadomość, że decyzja o tej sprawie jest teraz jego."""
    msg: dict[str, Any] = {
        "type": "team.escalated",
        "id": f"escalated-{item['id']}-{e['at']}"[:128],
        "item": item["id"],
        "summary": str(item.get("summary") or item["id"])[:300],
        "by": e["by"]["name"][:80],
        "to": e["to"]["sub"],
        "reason": e["reason"][:1000],
        "due": _due(item, config),
        **_link(config, "inbox"),
    }
    for key in ("change", "gate"):
        if item.get(key):
            msg[key] = item[key]
    sent, answer = _send(config, ESCALATED_PATH, msg, post, now)
    result: dict[str, Any] = {**sent, "at": at}
    if sent["status"] == "sent" and isinstance(answer, dict) and isinstance(answer.get("delivered"), str):
        result["delivered"] = answer["delivered"]
    return result


def _due(item: dict[str, Any], config: waiting.ChannelsConfig) -> str:
    """Termin sprawy z OM1 (dzień); eskalacja go nie zmienia."""
    if item.get("received_at"):
        return str(waiting.message(item, config)["due"])
    return datetime.now(UTC).date().isoformat()


def stage_of(item: dict[str, Any], now: datetime) -> str:
    """Najświeższy etap terminu osiągnięty teraz (OM1 §4–§5); „new”, gdy żaden."""
    if not item.get("received_at"):
        return "new"
    reached = [s for s, when in waiting.stages(item) if when <= now]
    return reached[-1] if reached else "new"


def approver_digest(
    items: list[dict[str, Any]],
    consults: consult.Consultations,
    entries: list[dict[str, Any]],
    *,
    now: datetime,
    config: waiting.ChannelsConfig,
) -> dict[str, Any] | None:
    """Skrót dla zatwierdzającego albo None, gdy nic na nim nie ma."""
    day = now.astimezone(UTC).date().isoformat()
    rows = []
    for it in items:
        if it.get("status") != "open":
            continue
        stage = stage_of(it, now)
        msg = waiting.message(it, config, stage) if it.get("received_at") else None
        row: dict[str, Any] = {
            "item": it["id"],
            "summary": str(it.get("summary") or it["id"])[:300],
            "stage": stage,
            "due": msg["due"] if msg else day,
        }
        for key in ("change", "gate"):
            if it.get(key):
                row[key] = it[key]
        if msg and msg.get("url"):
            row["url"] = msg["url"]
        rows.append((_URGENCY.index(stage), row["due"], it.get("received_at") or "", it["id"], row))
    rows.sort(key=lambda r: r[:4])
    open_ids = {it["id"]: it for it in items if it.get("status") == "open"}
    with_team, unreachable = [], []
    for item_id in consults.open_items():
        open_item = open_ids.get(item_id)
        view = consults.view(item_id, "")
        if open_item is None or view is None:
            continue
        summary = str(open_item.get("summary") or item_id)[:300]
        with_team.append({"item": item_id, "summary": summary, "answered": view["answered"],
                          "asked": view["asked"], "closes_at": view["closes_at"]})  # fmt: skip
        unreachable += [n for n in view["unreachable"] if n not in unreachable]
    digest = {
        "type": "team.digest",
        "id": f"digest-approver-{day}",
        "to": {"approver": True},
        "day": day,
        "waiting": {"total": len(rows), "items": [r[-1] for r in rows[:MAX_ITEMS]]},
        "with_team": with_team[:MAX_ITEMS],
        "asked_of_you": [],
        "to_discuss": {"count": len(entries), **(_link(config, "discuss") if entries else {})},
        "unreachable": unreachable[:20],
    }
    empty = not rows and not with_team and not entries
    return None if empty else digest


def person_digests(
    items: list[dict[str, Any]],
    consults: consult.Consultations,
    people: list[consult.Person],
    *,
    now: datetime,
    config: waiting.ChannelsConfig,
    escalations: escalate.Escalations | None = None,
) -> list[dict[str, Any]]:
    """Skróty osób, na których odpowiedź czeka pytanie zespołu („Asked of you”) albo do których eskalowano sprawę
    („Escalated to you”, T7); inni nie dostają nic."""
    day = now.astimezone(UTC).date().isoformat()
    open_items = {it["id"]: it for it in items if it.get("status") == "open"}
    summaries = {i: str(it.get("summary") or i)[:300] for i, it in open_items.items()}
    out = []
    for person in people:
        escalated = []
        for item_id in escalations.escalated_to(person.sub) if escalations else []:
            e = escalations.view(item_id) if escalations else None
            if item_id not in open_items or e is None:
                continue
            escalated.append({"item": item_id, "summary": summaries[item_id], "by": e["by"]["name"][:80],
                              "due": _due(open_items[item_id], config), **_link(config, "inbox")})  # fmt: skip
        mine = []
        for item_id in consults.asked_of(person.sub):
            view = consults.view(item_id, person.sub)
            if item_id not in summaries or view is None:
                continue
            mine.append({"item": item_id, "summary": summaries[item_id], "asked_by": view["decider"][:80],
                         "closes_at": view["closes_at"], **_link(config, "inbox")})  # fmt: skip
        if not mine and not escalated:
            continue
        out.append({
            "type": "team.digest",
            "id": f"digest-{person.sub}-{day}"[:128],
            "to": {"person": person.sub},
            "day": day,
            "waiting": {"total": 0, "items": []},
            "with_team": [],
            "asked_of_you": mine[:MAX_ITEMS],
            "escalated_to_you": escalated[:MAX_ITEMS],
            "to_discuss": {"count": 0},
            "unreachable": [],
        })  # fmt: skip
    return out


def collect(
    registry: Any, config: waiting.ChannelsConfig, *, now: datetime
) -> tuple[dict[str, Any] | None, list[dict[str, Any]], dict[str, str]]:
    """Skrót zatwierdzającego, skróty osób i nazwy osób po `sub` — z rejestru (skrzynka, konsultacje, agenda)."""
    from pdi.inbox import Inbox  # skrzynka importuje moduły powiadomień

    items = Inbox(registry).items(status="open")
    consults = consult.Consultations(registry.root, now=lambda: now)
    entries = agenda.build(items, consults, order=agenda.Order(registry.root).get(), now=now)
    people = consult.People(registry.root, now=lambda: now).all()
    return (
        approver_digest(items, consults, entries, now=now, config=config),
        person_digests(
            items,
            consults,
            people,
            now=now,
            config=config,
            escalations=escalate.Escalations(registry.root, now=lambda: now),
        ),
        {p.sub: p.name for p in people},
    )


def send_digests(
    registry: Any, config: waiting.ChannelsConfig, *, now: datetime | None = None, post: JsonPost | None = None
) -> list[dict[str, Any]]:
    """Wysyła dzisiejsze skróty; po jednym wyniku na odbiorcę (`to`, `status`, `error`)."""
    moment = (now or datetime.now(UTC)).astimezone(UTC)
    approver, personal, names = collect(registry, config, now=moment)
    out = []
    for d in ([approver] if approver else []) + personal:
        to = "approver" if "approver" in d["to"] else names.get(d["to"]["person"], d["to"]["person"])
        sent, answer = _send(config, DIGEST_PATH, d, post, int(moment.timestamp()))
        row = {"to": to, **sent}
        if sent["status"] == "sent" and isinstance(answer, dict) and answer.get("delivered"):
            row["delivered"] = answer["delivered"]
        out.append(row)
    return out


def main() -> None:
    """`pdi-digest`: dzienne skróty do Slacka (z crona w dni robocze tuż przed 8:00)."""
    import sys

    from pdi.registry import Registry

    json.dump(
        {"digests": send_digests(Registry.from_env(), waiting.ChannelsConfig.from_env())},
        sys.stdout,
        ensure_ascii=False,
    )
    sys.stdout.write("\n")
