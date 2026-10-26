"""Serwer MCP pdi (stdio): zapis i odczyt decyzji z miejsca pracy (Claude Code, Claude Desktop)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Any, Literal, NotRequired

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp_types import ToolAnnotations
from typing_extensions import TypedDict  # pydantic na 3.11 wymaga TypedDict z typing_extensions

from pdi.changes import ChangeNotFound
from pdi.dispatch import DispatchConfig
from pdi.impact import ShipScopeConfig
from pdi.inbox import Inbox, ItemClosed, ItemNotFound
from pdi.notify import NotifyConfig
from pdi.registry import CannotSupersede, Decision, DecisionNotFound, InvalidDecision, Registry
from pdi.trace import trace

INSTRUCTIONS = """\
Rejestr decyzji pdi. Zapisuj decyzję (record_decision) tylko na wyraźną prośbę człowieka i dopiero po tym,
jak zatwierdzi pokazany mu szkic — nie decyduj sam, co jest decyzją. Nie dopisuj uzasadnień ani założeń,
których nie było w rozmowie; czego brakuje, o to zapytaj. Zanim zaproponujesz rozwiązanie w obszarze, który mógł
być już rozstrzygnięty, sprawdź find_decisions; gdy propozycja przeczy wcześniejszej decyzji, powiedz to wprost
i zaproponuj supersede_decision zamiast cichej zmiany kursu. Skrzynka (list_inbox) zbiera bramki i oceny skutku
z tf, ci_for_sdlc i ShipScope; decide_inbox_item zapisuje decyzję jak record_decision — też tylko po zatwierdzeniu
szkicu — i uruchamia następną fazę. Stan przebiegu zmiany: list_changes, get_change."""

Kind = Literal["product", "technical", "process", "triage", "intent", "gate", "other"]
Status = Literal["recorded", "superseded", "reverted"]
InboxStatus = Literal["open", "decided", "superseded", "all"]
ChangeStatus = Literal["open", "rejected", "done", "all"]
GateOutcome = Literal["approved", "changes_requested", "rejected"]
ImpactOutcome = Literal["met", "not_met", "unknown"]
ProblemOutcome = Literal["accepted", "rejected"]


class Source(TypedDict):
    kind: Literal["claude-cli", "claude-ai", "slack", "confluence", "jira", "manual"]
    url: NotRequired[str]
    excerpt: NotRequired[str]


class Option(TypedDict):
    option: str
    chosen: bool
    note: NotRequired[str]


class Evidence(TypedDict):
    text: str
    epistemic_status: Literal["observation", "interpretation", "hypothesis", "ai_inference"]
    source_url: NotRequired[str]


class Assumption(TypedDict):
    statement: str
    load_bearing: bool
    invalidated_if: str


class SuccessMetric(TypedDict):
    metric: str
    target: str
    horizon: NotRequired[str]


class Links(TypedDict, total=False):
    prb: str
    chg: str
    tsk: str
    pr: str
    adr: str


DRAFT_FIELDS = (
    "statement",
    "why",
    "kind",
    "project",
    "source",
    "drafted_by",
    "decided_by",
    "decided_at",
    "options",
    "evidence",
    "assumptions",
    "dependencies",
    "success_metric",
    "review_by",
    "links",
    "tags",
)

_WRITE = ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True)
_READ = ToolAnnotations(read_only_hint=True)


def build_server(
    registry: Callable[[], Registry] = Registry.from_env,
    dispatch: Callable[[], DispatchConfig] = DispatchConfig.from_env,
) -> MCPServer:
    server = MCPServer("pdi", instructions=INSTRUCTIONS)

    def open_registry() -> Registry:
        try:
            return registry()
        except RuntimeError as e:
            raise ToolError(str(e)) from e

    def open_inbox() -> Inbox:
        return Inbox(
            open_registry(),
            dispatch=dispatch(),
            notify=NotifyConfig.from_env(),
            shipscope=ShipScopeConfig.from_env(),
        )

    @server.tool(annotations=_WRITE)
    def record_decision(
        statement: str,
        why: str,
        kind: Kind,
        source: Source,
        drafted_by: Literal["ai", "human"],
        project: str | None = None,
        decided_by: str | None = None,
        decided_at: str | None = None,
        options: list[Option] | None = None,
        evidence: list[Evidence] | None = None,
        assumptions: list[Assumption] | None = None,
        dependencies: list[str] | None = None,
        success_metric: SuccessMetric | None = None,
        review_by: str | None = None,
        links: Links | None = None,
        tags: list[str] | None = None,
    ) -> Decision:
        """Zapisuje zatwierdzoną przez człowieka decyzję w rejestrze pdi i zwraca ją z nadanym ID (DEC-nnnn).

        Wywołuj dopiero po tym, jak człowiek zatwierdził szkic. statement: co zdecydowano, jedno zdanie.
        why: uzasadnienie, 1–5 zdań, tylko z rozmowy. source: skąd decyzja (kind, url wątku/strony, krótki cytat).
        project: projekt, którego dotyczy decyzja — zwykle nazwa bieżącego repo; pomiń dla decyzji ogólnych.
        drafted_by: "ai", gdy szkic przygotował model. decided_at: RRRR-MM-DD (domyślnie dziś); decided_by:
        domyślnie PDI_DECIDED_BY. evidence.epistemic_status odróżnia obserwację od interpretacji, hipotezy
        i wniosku AI. assumptions: założenia; load_bearing=true, gdy ich upadek zmienia decyzję; invalidated_if:
        sygnał, po którym założenie przestaje być prawdziwe. Ponowienie identycznego zapisu zwraca istniejący wpis.
        """
        draft = _draft(locals())
        reg = open_registry()
        try:
            return reg.record(draft)
        except InvalidDecision as e:
            raise ToolError(str(e)) from e

    @server.tool(annotations=_READ)
    def find_decisions(
        query: str = "",
        tags: list[str] | None = None,
        since: str | None = None,
        status: Status | None = None,
        kind: Kind | None = None,
        project: str | None = None,
        limit: int = 10,
    ) -> dict[str, list[Decision]]:
        """Szuka wcześniejszych decyzji: „co już zdecydowaliśmy w tej sprawie i dlaczego?”.

        query: słowa kluczowe (pasują też fragmenty słów, np. „dostaw” znajdzie „dostawy”); puste = najnowsze.
        Filtry: tags (wszystkie muszą pasować), since (RRRR-MM-DD, data decyzji), status, kind, project
        (np. nazwa bieżącego repo; bez filtra — wszystkie projekty); limit wyników.
        Zwraca skróty z założeniami nośnymi; pełny wpis: get_decision.
        """
        return {
            "decisions": open_registry().find(
                query, tags=tags, since=since, status=status, kind=kind, project=project, limit=limit
            )
        }

    @server.tool(annotations=_READ)
    def get_decision(decision_id: str) -> Decision:
        """Zwraca pełny wpis decyzji o ID w formacie DEC-nnnn (opcje, dowody, założenia, źródło, powiązania)."""
        try:
            return open_registry().get(decision_id)
        except DecisionNotFound as e:
            raise ToolError(str(e)) from e

    @server.tool(annotations=_WRITE)
    def supersede_decision(
        old_decision_id: str,
        statement: str,
        why: str,
        kind: Kind,
        source: Source,
        drafted_by: Literal["ai", "human"],
        project: str | None = None,
        decided_by: str | None = None,
        decided_at: str | None = None,
        options: list[Option] | None = None,
        evidence: list[Evidence] | None = None,
        assumptions: list[Assumption] | None = None,
        dependencies: list[str] | None = None,
        success_metric: SuccessMetric | None = None,
        review_by: str | None = None,
        links: Links | None = None,
        tags: list[str] | None = None,
    ) -> Decision:
        """Zapisuje nową decyzję, która zastępuje old_decision_id (zmiana kursu zamiast nadpisania historii).

        Stara decyzja dostaje status superseded i odnośnik do nowej. Wywołuj po zatwierdzeniu szkicu przez
        człowieka; pola jak w record_decision, a why powinno mówić, co się zmieniło od starej decyzji.
        """
        draft = _draft(locals())
        reg = open_registry()
        try:
            return reg.supersede(old_decision_id, draft)
        except (InvalidDecision, DecisionNotFound, CannotSupersede) as e:
            raise ToolError(str(e)) from e

    @server.tool(annotations=_READ)
    def list_inbox(status: InboxStatus = "open") -> dict[str, list[dict[str, Any]]]:
        """Skrzynka pdi: bramki („flaga przeszła na etap 10%, przejść dalej?”), oceny skutku MVP i problemy z pasm
        kontrolnych tf („rollbacki poza 3σ — nowe zgłoszenie?”).

        status: open (domyślnie, czeka na decyzję), decided albo all. Każda pozycja: id, kind (gate /
        impact_review / problem), change (problem może go nie mieć), release, summary, received_at; bramka i problem
        mają event (pełne zdarzenie z kontraktu), problem też metric (odczyt pasma), ocena skutku — intent, metric,
        draft (szkic wniosku) i data (odczyty z ShipScope).
        """
        return {"items": open_inbox().items(status=None if status == "all" else status)}

    @server.tool(annotations=_WRITE)
    def decide_inbox_item(
        item_id: str,
        statement: str,
        why: str,
        source: Source,
        drafted_by: Literal["ai", "human"],
        outcome: GateOutcome | ImpactOutcome | ProblemOutcome | None = None,
        project: str | None = None,
        decided_by: str | None = None,
        decided_at: str | None = None,
        options: list[Option] | None = None,
        evidence: list[Evidence] | None = None,
        assumptions: list[Assumption] | None = None,
        dependencies: list[str] | None = None,
        success_metric: SuccessMetric | None = None,
        review_by: str | None = None,
        links: Links | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Zamyka pozycję skrzynki decyzją w rejestrze; wywołuj po zatwierdzeniu szkicu przez człowieka.

        Bramka (kind gate) wymaga outcome: approved, changes_requested albo rejected; decyzja dostaje kind gate,
        stan zmiany się przesuwa, a następna faza tf (albo poprawki tej samej) zostaje uruchomiona.
        Ocena skutku MVP (kind impact_review) wymaga outcome: met, not_met albo unknown — wynik potwierdzony przez
        człowieka, może różnić się od szkicu pdi (pole draft pozycji); decyzja dostaje kind product, zależność od
        decyzji o intencji i odczyt z ShipScope jako dowód. Problem z pasm kontrolnych tf (kind problem,
        metric.breached) wymaga outcome accepted albo rejected; decyzja dostaje kind triage i odczyt pasma jako dowód
        (links.prb podaj, gdy powstało zgłoszenie).
        links.chg nadaje skrzynka ze zdarzenia. Pozostałe pola jak w record_decision.
        """
        draft = _draft({**locals(), "kind": "other"})
        try:
            return open_inbox().decide(item_id, draft, outcome=outcome)
        except (InvalidDecision, ItemNotFound, ItemClosed) as e:
            raise ToolError(str(e)) from e

    @server.tool(annotations=_WRITE)
    def open_due_impact_reviews(today: str | None = None) -> dict[str, list[dict[str, Any]]]:
        """Otwiera oceny skutku MVP, których termin minął (po feature.released R1 i N dniach z success_metric).

        Dla każdej czyta z ShipScope status zmiany i metryki PROD od wydania i szkicuje wniosek (draft: verdict met /
        not_met / unknown, reason). Zwykle robi to cron (`pdi-impact-review`); today (RRRR-MM-DD) tylko do sprawdzeń.
        """
        try:
            day = date.fromisoformat(today) if today else None
        except ValueError as e:
            raise ToolError("today: data w formacie RRRR-MM-DD.") from e
        return {"opened": open_inbox().open_due_reviews(today=day)}

    @server.tool(annotations=_READ)
    def list_changes(status: ChangeStatus = "open") -> dict[str, list[dict[str, Any]]]:
        """Zmiany (CHG), które zna orkiestrator: zatwierdzone bramki, na co czekają, ostatnie uruchomienie fazy.

        status: open (domyślnie), rejected, done albo all.
        """
        return {"changes": open_inbox().changes.all(status=None if status == "all" else status)}

    @server.tool(annotations=_READ)
    def get_change(change: str) -> dict[str, Any]:
        """Pełny stan przebiegu zmiany (np. CHG-12), z historią zdarzeń i decyzji."""
        try:
            return open_inbox().changes.get(change)
        except ChangeNotFound as e:
            raise ToolError(str(e)) from e

    @server.tool(annotations=_READ)
    def get_trace(change: str, live: bool = True) -> dict[str, Any]:
        """Graf śladu zmiany: PRB → CHG → bramki i decyzje → TSK → PR → wdrożenia → wydania → ocena skutku.

        nodes (id, kind, label, status), edges (from, to, kind), gaps (luki do pokazania człowiekowi, nie do
        naprawiania) i mermaid (flowchart do wklejenia). live=true czyta status wdrożeń z ShipScope
        (PDI_SHIPSCOPE_URL, PDI_SHIPSCOPE_TOKEN); live=false tylko z tego, co pdi ma.
        """
        try:
            return trace(open_registry(), change, shipscope=ShipScopeConfig.from_env(), live=live)
        except ChangeNotFound as e:
            raise ToolError(str(e)) from e

    @server.tool(annotations=_WRITE)
    def retry_dispatch(change: str) -> dict[str, Any]:
        """Ponawia nieudane uruchomienie fazy tf i wysyłkę decyzji do ci_for_sdlc (po poprawce ustawień)."""
        try:
            return open_inbox().retry_dispatch(change)
        except (ChangeNotFound, InvalidDecision) as e:
            raise ToolError(str(e)) from e

    return server


def _draft(args: dict[str, Any]) -> Decision:
    """Szkic decyzji z argumentów narzędzia: tylko pola kontraktu, bez pominiętych (None)."""
    return {k: args[k] for k in DRAFT_FIELDS if args.get(k) is not None}


def main() -> None:
    build_server().run("stdio")


if __name__ == "__main__":
    main()
