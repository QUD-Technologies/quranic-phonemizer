"""The root consumer facade over the native analysis projections."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from threading import RLock

from ..api import Recitation, alphabet, recitation
from ..model.address import (
    KhilafId,
    Option,
    Riwayah,
    Script,
    VariantSelection,
    check_riwayah,
)
from ..model.inscription import StopAdvice
from ..orthography.write import Pen, pen_for
from ..render.alphabet import allowed_extra_phonemes, effective_extra_phonemes
from ..riwayat.khilaf import DYNAMIC_SCOPE_RULES
from ..session import Session, phonemize_request
from .build import build_bundle
from .catalogue import tajweed_rules as _tajweed_rules
from .cells.dtos import CellView
from .cells.view import build_cell_view
from .dtos import AnalysisBundle, RuleDefinition
from .facts import AnalysisFacts, analyse
from .highlight_dtos import HighlightGroup
from .highlights import highlight_groups
from .inscription import InscriptionFacts, inscribe
from .result import AnalysisResult, _result_from_bundle
from .schema import (
    KINDS,
    analysis_document,
    cell_document,
    highlight_document,
    serialize_document,
    source_document,
)
from .schema.serialize import Json
from .source import build_source_view
from .source_dtos import SourceView

_DEFAULT_SCRIPT = {
    Riwayah.HAFS: Script.UTHMANI,
    Riwayah.WARSH: Script.UTHMANI,
}
_SPELLINGS = ("source", "transformed")
_SYNTHETIC_STOP_SIGNS = ("verse",)


class UnknownExtraPhoneme(ValueError):
    """A rendering distinction not optional for the selected riwayah."""


class UnknownStopSign(ValueError):
    """A stop class unavailable in the selected riwayah and script."""


class UnknownRule(ValueError):
    """A rule absent from the selected riwayah's published catalogue."""


def supported_riwayat() -> tuple[str, ...]:
    from ..api import PACKAGES

    return tuple(sorted(riwayah.value for riwayah in PACKAGES))


def _script_for(riwayah: Riwayah, script: str | None) -> Script:
    return Script(script) if script else _DEFAULT_SCRIPT[riwayah]


def available_stop_signs(
    riwayah: str, *, script: str | None = None
) -> tuple[str, ...]:
    name = check_riwayah(riwayah)
    selected = _script_for(name, script)
    inventory = recitation(name).inventory(selected)
    declared = {
        entry.advice for entry in inventory.marks.values()
        if entry.advice is not None
    }
    return _SYNTHETIC_STOP_SIGNS + tuple(
        advice.value for advice in StopAdvice if advice in declared
    )


def available_stop_editions(riwayah: str) -> tuple[str, ...]:
    """Mushaf printings whose waqf marks the riwayah packages, default first.
    Empty when the riwayah packages a single edition."""
    from ..api import PACKAGES

    return PACKAGES[check_riwayah(riwayah)].STOP_EDITIONS


def available_variants(riwayah: str) -> dict[str, dict[str, object]]:
    return recitation(check_riwayah(riwayah)).khilaf.points()


def variant_catalogue(riwayah: str) -> tuple[dict[str, object], ...]:
    return recitation(check_riwayah(riwayah)).khilaf.public_catalogue()


def tajweed_rules(riwayah: str) -> tuple[RuleDefinition, ...]:
    return _tajweed_rules(riwayah)


def _selection(variants: dict | None) -> VariantSelection:
    if not variants:
        return VariantSelection()
    options = []
    for key, value in variants.items():
        if not isinstance(value, str):
            raise TypeError(
                f"{key}: variant choices are scalar strings, got "
                f"{type(value).__name__}"
            )
        options.append(Option(KhilafId(key), value))
    return VariantSelection(tuple(options))


def _resolved_variant(recitation_: Recitation, selection: VariantSelection):
    return {
        point.value: spec.choose(selection)
        for point, spec in recitation_.khilaf.variants.items()
    }


@dataclass(slots=True)
class _ProjectionState:
    session: Session
    facts: AnalysisFacts
    inscription: InscriptionFacts
    bundle: AnalysisBundle
    pen: Pen
    source_view: SourceView | None = None
    highlight_view: tuple[HighlightGroup, ...] | None = None
    cell_views: dict[str, CellView] = field(default_factory=dict)
    lock: RLock = field(default_factory=RLock)

    def source(self) -> SourceView:
        with self.lock:
            if self.source_view is None:
                self.source_view = build_source_view(
                    self.session,
                    bundle=self.bundle,
                    facts=self.facts,
                    insc=self.inscription,
                )
            return self.source_view

    def highlights(self) -> tuple[HighlightGroup, ...]:
        with self.lock:
            if self.highlight_view is None:
                self.highlight_view = highlight_groups(self.source(), self.bundle)
            return self.highlight_view

    def cells(self, spelling: str) -> CellView:
        if spelling not in _SPELLINGS:
            raise ValueError(
                f"spelling must be 'source' or 'transformed', got {spelling!r}"
            )
        with self.lock:
            if spelling not in self.cell_views:
                self.cell_views[spelling] = build_cell_view(
                    self.session,
                    ref=self.bundle.ref,
                    riwayah=self.bundle.riwayah,
                    script=self.bundle.script,
                    variant=self.bundle.variant,
                    extra_phonemes=self.bundle.extra_phonemes,
                    spelling=spelling,
                    pen=self.pen if spelling == "transformed" else None,
                    bundle=self.bundle,
                    source=self.source(),
                    facts=self.facts,
                    insc=self.inscription,
                )
            return self.cell_views[spelling]


@dataclass(frozen=True, slots=True)
class Result:
    """One eager analysis with cached, selective native projections."""

    analysis: AnalysisResult
    _state: _ProjectionState
    _rule_catalogue: tuple[RuleDefinition, ...]
    _variant_catalogue: tuple[dict[str, object], ...]
    _dynamic_sites: dict = field(default_factory=dict)

    @property
    def words(self):
        return self.analysis.words

    @property
    def boundaries(self):
        return self.analysis.boundaries

    @property
    def sounds(self):
        return self.analysis.sounds

    @property
    def rule_occurrences(self):
        return self.analysis.rule_occurrences

    @property
    def mergers(self):
        return self.analysis.mergers

    @property
    def rule_catalogue(self) -> tuple[RuleDefinition, ...]:
        return self._rule_catalogue

    def rule_definition(self, rule: str) -> RuleDefinition:
        for definition in self._rule_catalogue:
            if definition.id.value == rule:
                return definition
        raise UnknownRule(
            f"{rule!r} is not published for {self.analysis.riwayah}; "
            f"available rules: {[d.id.value for d in self._rule_catalogue]}"
        )

    def text(self) -> str:
        return self.analysis.text()

    def phonemes(self, by: str | None = None):
        return self.analysis.phonemes(by)

    def source(self) -> SourceView:
        return self._state.source()

    def highlights(self) -> tuple[HighlightGroup, ...]:
        return self._state.highlights()

    def cells(self, *, spelling: str = "source") -> CellView:
        return self._state.cells(spelling)

    def variant_occurrences(self) -> tuple[dict[str, object], ...]:
        words = {word.ref: word for word in self.words}
        boundaries = {boundary.id: boundary for boundary in self.boundaries}
        rows = []
        for entry in self._variant_catalogue:
            if entry["dynamic_scope"]:
                rows.extend(self._dynamic_variant_rows(entry))
                continue
            for occurrence in entry["occurrences"]:
                matched = [words.get(ref) for ref in occurrence["word_refs"]]
                if any(word is None for word in matched):
                    continue
                targets = [
                    words.get(ref) for ref in occurrence["target_word_refs"]
                ]
                if any(word is None for word in targets):
                    continue
                first = matched[0]
                after = boundaries[first.after_boundary_id]
                before = boundaries[first.before_boundary_id]
                requirement = occurrence["requires"]
                active = (
                    requirement == "all"
                    or requirement == "waqf" and after.state.value == "stop"
                    or requirement == "ibtidaa" and before.state.value in {"start", "stop"}
                    or requirement in {"wasl", "joined"}
                    and after.state.value in {"join", "sakt"}
                )
                rows.append({
                    "variant_id": entry["id"],
                    "selected": self.analysis.variant[entry["id"]],
                    "word_ids": [word.id.value for word in matched],
                    "target_word_ids": [word.id.value for word in targets],
                    "anchor": occurrence["anchor"],
                    "anchor_word_id": first.id.value,
                    "anchor_boundary_id": (
                        first.after_boundary_id.value
                        if occurrence["anchor"] == "boundary" else None
                    ),
                    "requires": requirement,
                    "active": active,
                    "masked": not active,
                })
        return tuple(rows)

    def _dynamic_variant_rows(self, entry) -> list[dict[str, object]]:
        """Sites of a dynamic-scope selector, from its realized marker rules
        or the owning package's structural resolver."""
        scope = entry["dynamic_scope"]
        markers = DYNAMIC_SCOPE_RULES.get(scope)
        if markers is not None:
            spans = [
                [word_id.value for word_id in occurrence.word_ids]
                for occurrence in self.analysis.rule_occurrences
                if occurrence.rule_id.value in markers
            ]
        elif scope in self._dynamic_sites:
            session = self._state.session
            spans = [
                [index]
                for selector, index in self._dynamic_sites[scope](
                    session.score, session.boundaries
                )
                if selector == entry["id"]
            ]
        else:
            raise ValueError(
                f"{entry['id']}: no resolver for dynamic scope {scope!r}"
            )
        rows = []
        for word_ids in spans:
            first = next(
                word for word in self.words
                if word.id.value == word_ids[0]
            )
            anchor = "boundary" if len(word_ids) > 1 else "word"
            rows.append({
                "variant_id": entry["id"],
                "selected": self.analysis.variant[entry["id"]],
                "word_ids": word_ids,
                "target_word_ids": word_ids,
                "anchor": anchor,
                "anchor_word_id": first.id.value,
                "anchor_boundary_id": (
                    first.after_boundary_id.value if anchor == "boundary"
                    else None
                ),
                "requires": "all",
                "active": True,
                "masked": False,
            })
        return rows

    def document(self, kind: str, *, spelling: str = "source") -> Json:
        if kind not in KINDS:
            raise ValueError(f"unknown document kind {kind!r}; expected {sorted(KINDS)}")
        if kind == "analysis_result":
            document = analysis_document(self.analysis)
        elif kind == "source_view":
            document = source_document(self.source())
        elif kind == "highlight_groups":
            document = highlight_document(self.highlights())
        else:
            document = cell_document(self.cells(spelling=spelling))
        return serialize_document(document)


@dataclass(frozen=True)
class Phonemizer:
    riwayah: str = "hafs"
    script: str | None = None
    variants: dict | None = None
    extra_phonemes: tuple[str, ...] = ()
    #: The mushaf printing whose waqf marks are read, from
    #: `available_stop_editions`. None is the riwayah's default.
    stop_edition: str | None = None

    def __post_init__(self) -> None:
        name = check_riwayah(self.riwayah)
        requested = frozenset(self.extra_phonemes)
        allowed = allowed_extra_phonemes(name)
        unknown = requested - allowed
        if unknown:
            raise UnknownExtraPhoneme(
                f"{sorted(unknown)} is not optional for {name.value}; "
                f"choose from {sorted(allowed)}"
            )
        loaded = recitation(name, self.stop_edition)
        script = _script_for(name, self.script)
        selection = _selection(self.variants)
        loaded.khilaf.validate(selection)
        object.__setattr__(self, "_name", name)
        object.__setattr__(self, "_recitation", loaded)
        object.__setattr__(self, "_script", script)
        object.__setattr__(self, "_selection", selection)
        object.__setattr__(self, "_extra", requested)
        object.__setattr__(
            self, "_render_extra", effective_extra_phonemes(name, requested)
        )
        object.__setattr__(self, "_alphabet", alphabet())
        object.__setattr__(self, "_pen", pen_for(loaded.inventory(script)))

    @property
    def available_stop_signs(self) -> tuple[str, ...]:
        return available_stop_signs(self.riwayah, script=self._script.value)

    @property
    def available_variants(self) -> dict[str, dict[str, object]]:
        return available_variants(self.riwayah)

    @property
    def variant_catalogue(self) -> tuple[dict[str, object], ...]:
        return variant_catalogue(self.riwayah)

    @property
    def tajweed_rules(self) -> tuple[RuleDefinition, ...]:
        return tajweed_rules(self.riwayah)

    def _validate_stops(self, stop_signs: Sequence[str]) -> None:
        available = self.available_stop_signs
        unknown = sorted(set(stop_signs) - set(available))
        if unknown:
            raise UnknownStopSign(
                f"{unknown} is not available for "
                f"{self._name.value}/{self._script.value}; "
                f"available stop signs: {list(available)}"
            )

    def analyse(
        self,
        ref: str,
        *,
        stop_signs: Sequence[str] = (),
        stop_refs: Sequence[str] = (),
    ) -> Result:
        self._validate_stops(stop_signs)
        session = phonemize_request(
            self._recitation,
            ref,
            script=self._script,
            stop_signs=stop_signs,
            stop_refs=stop_refs,
            selection=self._selection,
        )
        facts = analyse(
            session,
            self._alphabet,
            extra_phonemes=self._render_extra,
            quality_fallbacks=self._recitation.quality_fallbacks,
        )
        inscription = inscribe(session)
        variant = _resolved_variant(self._recitation, self._selection)
        bundle = build_bundle(
            session,
            ref=ref,
            riwayah=self._name.value,
            script=self._script.value,
            variant=variant,
            extra_phonemes=self._extra,
            facts=facts,
            insc=inscription,
        )
        state = _ProjectionState(
            session=session,
            facts=facts,
            inscription=inscription,
            bundle=bundle,
            pen=self._pen,
        )
        return Result(
            _result_from_bundle(bundle),
            state,
            self.tajweed_rules,
            self.variant_catalogue,
            self._recitation.khilaf.dynamic_sites,
        )


__all__ = [
    "Phonemizer",
    "Result",
    "UnknownExtraPhoneme",
    "UnknownRule",
    "UnknownStopSign",
    "available_stop_signs",
    "available_variants",
    "variant_catalogue",
    "supported_riwayat",
    "tajweed_rules",
]
