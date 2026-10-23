"""Składa prompty testu v2 z szablonów w prompty/warianty.md i materiałów.

Użycie:
  python3 zbuduj_prompty.py <katalog_wyjściowy>
      → prompty bez zależności: A-ctx-T0, A-ctx-T1..T4, A-fresh-T1..T4, A+-T1..T4, B-T0
  python3 zbuduj_prompty.py <katalog_wyjściowy> --b-tydzien N --model plik.json [--historia plik.md ...]
      → prompt B-TN z zapisanym modelem i historią ostrzeżeń z poprzednich tygodni

Historia ostrzeżeń: z każdego podanego pliku (odpowiedzi B z poprzednich tygodni) brane są bloki komunikatów
od linii „Co:” do linii „Propozycja:”. Gdy plik nie zawiera takich bloków, wstawiana jest informacja o braku ostrzeżeń.
"""

import argparse
import json
import re
from pathlib import Path

KATALOG = Path(__file__).resolve().parent.parent
MATERIALY = KATALOG / "materialy"


def szablony() -> list[str]:
    tekst = (KATALOG / "prompty" / "warianty.md").read_text(encoding="utf-8")
    # kolejność bloków w pliku: wspólny opis, A-ctx-T0, A-ctx-TN, A-fresh, A+, B-T0, B-TN
    return re.findall(r"```\n(.*?)```", tekst, re.S)


def materialy(katalog: str) -> str:
    pliki = sorted((MATERIALY / katalog).glob("*.md"))
    return "\n\n".join(f"=== PLIK: {p.name} ===\n{p.read_text(encoding='utf-8')}" for p in pliki)


def wstaw(szablon: str, **wartosci: str) -> str:
    for klucz, wartosc in wartosci.items():
        szablon = szablon.replace("{" + klucz + "}", wartosc)
    return szablon


def historia(pliki: list[Path]) -> str:
    bloki = []
    for plik in pliki:
        tekst = plik.read_text(encoding="utf-8")
        znalezione = re.findall(r"(Co:.*?Propozycja:[^\n]*)", tekst, re.S)
        bloki += [f"[{plik.stem}]\n{b.strip()}" for b in znalezione]
    return "\n\n".join(bloki) if bloki else "(brak wcześniejszych ostrzeżeń)"


def wyciagnij_json(tekst: str) -> str:
    start = tekst.find("{")
    glebokosc = 0
    for i in range(start, len(tekst)):
        if tekst[i] == "{":
            glebokosc += 1
        elif tekst[i] == "}":
            glebokosc -= 1
            if glebokosc == 0:
                fragment = tekst[start : i + 1]
                json.loads(fragment)  # błąd = model nie zwrócił poprawnego JSON
                return fragment
    raise ValueError("Nie znaleziono kompletnego obiektu JSON")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("wyjscie", type=Path)
    parser.add_argument("--b-tydzien", type=int)
    parser.add_argument("--model", type=Path)
    parser.add_argument("--historia", type=Path, nargs="*", default=[])
    args = parser.parse_args()
    args.wyjscie.mkdir(parents=True, exist_ok=True)
    _, a_ctx_t0, a_ctx_tn, a_fresh, a_plus, b_t0, b_tn = szablony()

    if args.b_tydzien:
        model = wyciagnij_json(args.model.read_text(encoding="utf-8"))
        n = str(args.b_tydzien)
        tekst = wstaw(b_tn, N=n, MODEL=model, HISTORIA=historia(args.historia), TYDZIEN=materialy(f"tydzien-{n}"))
        (args.wyjscie / f"B-T{n}.txt").write_text(tekst, encoding="utf-8")
        return

    t0 = materialy("t0")
    (args.wyjscie / "A-ctx-T0.txt").write_text(wstaw(a_ctx_t0, T0=t0), encoding="utf-8")
    (args.wyjscie / "B-T0.txt").write_text(wstaw(b_t0, T0=t0), encoding="utf-8")
    for n in range(1, 5):
        tydzien = materialy(f"tydzien-{n}")
        for nazwa, szablon in (("A-ctx", a_ctx_tn), ("A-fresh", a_fresh), ("A+", a_plus)):
            (args.wyjscie / f"{nazwa}-T{n}.txt").write_text(wstaw(szablon, N=str(n), TYDZIEN=tydzien), encoding="utf-8")


if __name__ == "__main__":
    main()
