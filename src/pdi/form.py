"""Formularz zgłoszeń (F3): strony HTML bez skryptów i parsowanie wysłanego formularza — czyste, bez plików.

`pdi-receiver` podaje stronę na `GET /problems/new?t=<PDI_FORM_TOKEN>` i przyjmuje `POST /problems`; zapis robi
`pdi.problems.ProblemStore.record`. Zgłoszenie opisuje problem: kto nie może czego i z jakim skutkiem; pomysł na
rozwiązanie ma osobne pole. Wszystko, co wraca na stronę, jest escapowane. Plan: docs/plan-f3-pdi.md.
"""

from __future__ import annotations

from html import escape
from typing import Any
from urllib.parse import parse_qs

# Pole → (etykieta, podpowiedź, wymagane, najwyżej znaków, wiele wierszy)
FIELDS: dict[str, tuple[str, str, bool, int, bool]] = {
    "title": ("Krótki tytuł", "np. Brak operacji na wielu ładowarkach naraz", True, 200, False),
    "who": ("Kto ma problem?", "rola albo zespół, np. operator Control Tower", True, 300, False),
    "cannot": ("Czego nie może zrobić?", "czynność, nie rozwiązanie", True, 2000, True),
    "impact": ("Jaki to ma skutek?", "czas, pieniądze, błędy, klienci", True, 2000, True),
    "workaround": ("Jak radzi sobie dziś?", "", False, 2000, True),
    "frequency": ("Jak często to się zdarza?", "np. kilka razy w miesiącu", False, 300, False),
    "proposed_solution": ("Masz pomysł na rozwiązanie?", "zapiszemy go osobno od problemu", False, 2000, True),
    "reporter": ("Kto zgłasza?", "login, e-mail albo zespół — na ten adres przyjdą powiadomienia", True, 200, False),
}
KINDS = {"problem": "problem w tym, co działa", "idea": "pomysł na coś nowego"}

_STYLE = (
    "body{font:16px/1.5 system-ui,sans-serif;max-width:640px;margin:32px auto;padding:0 16px;color:#15171a;"
    "background:#f5f6f8}label{display:block;font-weight:600;margin-top:16px}small{color:#5c6168;font-weight:400}"
    "input,textarea{width:100%;box-sizing:border-box;font:inherit;padding:8px;margin-top:4px;border:1px solid #bbb;"
    "border-radius:6px}textarea{min-height:5em}.err{color:#c21e1e;font-weight:400}button{margin-top:24px;"
    "font:inherit;padding:10px 18px;border-radius:6px;border:0;background:#6e5bd6;color:#fff}"
    "@media(prefers-color-scheme:dark){body{background:#0b0c0e;color:#eceef1}input,textarea{background:#121417;"
    "color:#eceef1;border-color:#444}small{color:#9aa0a6}}"
)


def form_page(token: str, *, values: dict[str, str] | None = None, errors: dict[str, str] | None = None) -> str:
    """Strona formularza; po błędach z wpisanymi wartościami i komunikatem przy polu."""
    values = values or {}
    errors = errors or {}
    rows = []
    kind = values.get("kind", "problem")
    options = "".join(
        f'<label><input type="radio" name="kind" value="{k}"{" checked" if k == kind else ""}> {escape(text)}</label>'
        for k, text in KINDS.items()
    )
    rows.append(f"<fieldset><legend>Co zgłaszasz?</legend>{options}{_error(errors, 'kind')}</fieldset>")
    for name, (label, hint, required, limit, multiline) in FIELDS.items():
        value = escape(values.get(name, ""))
        need = " required" if required else ""
        field = (
            f'<textarea name="{name}" maxlength="{limit}"{need}>{value}</textarea>'
            if multiline
            else f'<input name="{name}" value="{value}" maxlength="{limit}"{need}>'
        )
        small = f" <small>{escape(hint)}</small>" if hint else ""
        rows.append(f"<label>{escape(label)}{small}{_error(errors, name)}{field}</label>")
    body = (
        "<h1>Zgłoś problem</h1><p>Opisz, kto i czego nie może zrobić. Odpowiemy powiadomieniem po triażu.</p>"
        f'<form action="/problems" method="post"><input type="hidden" name="t" value="{escape(token)}">'
        f'{"".join(rows)}<button type="submit">Wyślij zgłoszenie</button></form>'
    )
    return _page("Zgłoś problem", body)


def thanks_page(problem: dict[str, Any], similar: list[dict[str, Any]]) -> str:
    """Strona po zapisie: numer zgłoszenia i podobne zgłoszenia (może to już znamy)."""
    items = "".join(f"<li>{escape(s['id'])}: {escape(s['title'])}</li>" for s in similar)
    known = f"<p>Podobne zgłoszenia, które już mamy:</p><ul>{items}</ul>" if similar else ""
    body = (
        f"<h1>Dziękujemy — {escape(problem['id'])}</h1>"
        f"<p>Zapisaliśmy zgłoszenie „{escape(problem['title'])}”. Dostaniesz powiadomienie, gdy zapadnie decyzja.</p>"
        f"{known}"
    )
    return _page("Zgłoszenie zapisane", body)


def parse_form(body: bytes) -> tuple[dict[str, Any], dict[str, str], str]:
    """`(szkic zgłoszenia, błędy pól, token)` z treści `application/x-www-form-urlencoded`; nieznane pola pomija."""
    try:
        raw = parse_qs(body.decode("utf-8"), keep_blank_values=True, max_num_fields=50)
    except (UnicodeDecodeError, ValueError):
        return {}, {"form": "Nieczytelny formularz."}, ""
    values = {k: v[0].strip() for k, v in raw.items() if v}
    errors: dict[str, str] = {}
    kind = values.get("kind", "problem")
    if kind not in KINDS:
        errors["kind"] = "Wybierz problem albo pomysł."
    draft: dict[str, Any] = {"kind": kind}
    for name, (_label, _, required, limit, _) in FIELDS.items():
        value = values.get(name, "")
        if required and not value:
            errors[name] = "To pole jest wymagane."
        elif len(value) > limit:
            errors[name] = f"Najwyżej {limit} znaków."
        elif value:
            draft[name] = value
    draft["channel"] = "form"
    return draft, errors, values.get("t", "")


def values_of(body: bytes) -> dict[str, str]:
    """Wpisane wartości (do ponownego pokazania formularza po błędzie)."""
    try:
        raw = parse_qs(body.decode("utf-8"), keep_blank_values=True, max_num_fields=50)
    except (UnicodeDecodeError, ValueError):
        return {}
    return {k: v[0] for k, v in raw.items() if v and (k in FIELDS or k == "kind")}


def _error(errors: dict[str, str], name: str) -> str:
    return f' <span class="err">{escape(errors[name])}</span>' if name in errors else ""


def _page(title: str, body: str) -> str:
    return (
        f'<!doctype html><html lang="pl"><head><meta charset="utf-8"><meta name="viewport" '
        f'content="width=device-width,initial-scale=1"><title>{escape(title)}</title><style>{_STYLE}</style>'
        f"</head><body>{body}</body></html>"
    )
