from pdi.form import FIELDS, form_page, parse_form, thanks_page

EVIL = "<script>alert(1)</script>"


def body(**values: str) -> bytes:
    from urllib.parse import urlencode

    base = {
        "t": "tok",
        "kind": "problem",
        "title": "Brak operacji masowych",
        "who": "operator Control Tower",
        "cannot": "zmienić konfiguracji wielu ładowarek naraz",
        "impact": "zmiana taryfy zajmuje dzień",
        "reporter": "operator-1",
    }
    base.update(values)
    return urlencode(base).encode()


def test_form_page_has_every_field_hidden_token_and_no_script() -> None:
    page = form_page("tok-1")

    for name in FIELDS:
        assert f'name="{name}"' in page
    assert '<input type="hidden" name="t" value="tok-1">' in page
    assert "<script" not in page
    assert 'action="/problems"' in page and 'method="post"' in page


def test_form_page_after_errors_keeps_values_escaped_and_names_the_field() -> None:
    page = form_page("tok", values={"title": EVIL}, errors={"who": "Podaj, kto ma problem."})

    assert EVIL not in page
    assert "&lt;script&gt;" in page
    assert "Podaj, kto ma problem." in page


def test_parse_form_gives_a_form_channel_draft() -> None:
    draft, errors, token = parse_form(body(workaround="po kolei", frequency=""))

    assert errors == {}
    assert token == "tok"  # noqa: S105 — token testowy
    assert draft == {
        "kind": "problem",
        "title": "Brak operacji masowych",
        "who": "operator Control Tower",
        "cannot": "zmienić konfiguracji wielu ładowarek naraz",
        "impact": "zmiana taryfy zajmuje dzień",
        "reporter": "operator-1",
        "workaround": "po kolei",
        "channel": "form",
    }


def test_parse_form_reports_missing_and_too_long_fields_and_bad_kind() -> None:
    _, errors, _ = parse_form(body(who="", title="x" * 201, kind="rozkaz"))

    assert set(errors) == {"who", "title", "kind"}


def test_parse_form_ignores_unknown_fields_and_bad_encoding() -> None:
    draft, errors, _ = parse_form(body(channel="slack", id="PRB-9"))
    assert errors == {} and draft["channel"] == "form" and "id" not in draft

    _, errors, token = parse_form(b"\xff\xfe")
    assert errors and token == ""


def test_thanks_page_names_the_problem_and_similar_ones_escaped() -> None:
    page = thanks_page({"id": "PRB-4", "title": EVIL}, [{"id": "PRB-1", "title": "Podobne", "score": 0.5}])

    assert "PRB-4" in page and "PRB-1" in page and "Podobne" in page
    assert EVIL not in page
