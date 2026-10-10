"""Compose transformed columns into the renderer-ready cell projection."""

from __future__ import annotations

from dataclasses import replace

from ...model.canon import Rule
from ...model.performance import Aspect, Vowel
from ...orthography.write import Pen
from ..attributions import (
    Classified,
    Hosted,
    Insertion,
    Merged,
    Relengthened,
    Silenced,
)
from ..facts import AnalysisFacts
from ..ids import OccurrenceId, SoundId
from ..inscription import InscriptionFacts
from ..source_dtos import LiteralSilence, SourceView
from .align import next_column_id
from .dtos import CellRole, CellStatus, CellWord
from .projection_carriers import (
    ensure_carriers,
    ensure_started_qualities,
    slot_of_columns,
)
from .projection_compounds import (
    fold_article_naql_madd,
    project_warsh_compounds,
)
from .projection_groups import group_words
from .projection_marks import (
    clean_structural_marks,
    fold_maqsura_daggers,
    fold_pausal_sukun,
    fold_shared_silence_riders,
    fold_vowel_ishmam_presenter,
    pausal_slots,
    transform_plain_madd,
)
from .projection_naql import split_carried_naql_alif
from .projection_semantics import (
    keep_pausal_alif_on_carriers,
    preserve_semantic_cells,
)
from .projection_sukun import fold_sukun


class _ColumnIndex:
    """Columns in text order, looked up by owned sound, presented sound,
    silence, and source slot."""

    def __init__(self, words: tuple[CellWord, ...], slot_of_unit) -> None:
        self.columns = [c for w in words for c in w.columns]
        self.owners: dict[SoundId, list] = {}
        self.presenters: dict[SoundId, list] = {}
        self.at_slot: dict[object, list[int]] = {}
        self.silenced: dict[object, list] = {}
        for index, col in enumerate(self.columns):
            self.silenced.setdefault(col.silence, []).append(col)
            for sound in dict.fromkeys(col.owned_sound_ids):
                self.owners.setdefault(sound, []).append(col)
            for sound in dict.fromkeys(col.presented_sound_ids):
                self.presenters.setdefault(sound, []).append(col)
            for unit in col.source_unit_ids:
                slot = slot_of_unit.get(unit.value)
                self.at_slot.setdefault(slot, []).append(index)

    def sound(self, sound: int, *, presenters=False) -> list:
        found = (self.presenters if presenters else self.owners).get(SoundId(sound))
        return list(found or ())

    def in_slots(self, slots) -> list:
        found = {index for slot in set(slots) for index in self.at_slot.get(slot, ())}
        return [self.columns[index] for index in sorted(found)]


def _silenced_targets(index: _ColumnIndex, edge):
    roles = (
        {CellRole.HARAKA, CellRole.TANWEEN, CellRole.MADD}
        if edge.aspect is Aspect.VOWEL
        else {CellRole.LETTER}
    )
    return [
        col
        for col in index.in_slots(edge.slots)
        if not isinstance(col.silence, LiteralSilence)
        and (col.role in roles or col.silence == OccurrenceId(edge.by))
    ]


def _modifier_targets(index: _ColumnIndex, facts, modifier):
    occurrence = OccurrenceId(modifier.by)
    carrier_only = (
        isinstance(modifier, Relengthened)
        and facts.occurrences[modifier.by].rule is Rule.ILTIQA_SHORTENING
    )
    if carrier_only:
        return list(index.silenced.get(occurrence, ()))
    targets = index.sound(modifier.sound)
    if isinstance(modifier, Classified) or isinstance(
        facts.sounds[modifier.sound].value, Vowel
    ):
        targets.extend(index.sound(modifier.sound, presenters=True))
    return targets


def _place_rules(
    words: tuple[CellWord, ...], facts: AnalysisFacts, slot_of_unit
) -> tuple[CellWord, ...]:
    placed: dict[int, list[OccurrenceId]] = {
        c.id.value: [] for w in words for c in w.columns
    }
    index = _ColumnIndex(words, slot_of_unit)
    merged = {
        (edge.by, edge.sound) for edge in facts.attributions if isinstance(edge, Merged)
    }
    for edge in facts.attributions:
        if edge.by is None:
            continue
        rule = facts.occurrences[edge.by].rule.value
        if isinstance(edge, Merged) and rule.startswith("madd_"):
            continue
        if (
            isinstance(edge, Hosted)
            and (edge.by, edge.sound) in merged
            and rule != "ibdal_hamza"
            and not rule.startswith(("idgham_", "madd_"))
        ):
            continue
        occurrence = OccurrenceId(edge.by)
        if isinstance(edge, Merged):
            targets = index.sound(edge.sound, presenters=True)
        elif isinstance(edge, Silenced):
            targets = _silenced_targets(index, edge)
        elif isinstance(edge, (Hosted, Insertion)):
            targets = index.sound(edge.sound)
        else:
            targets = []
        for col in targets:
            if occurrence not in placed[col.id.value]:
                placed[col.id.value].append(occurrence)
    for modifier in facts.modifiers:
        occurrence = OccurrenceId(modifier.by)
        for col in _modifier_targets(index, facts, modifier):
            if occurrence not in placed[col.id.value]:
                placed[col.id.value].append(occurrence)
    return tuple(
        replace(
            w,
            columns=tuple(
                replace(c, rule_occurrence_ids=tuple(placed[c.id.value]))
                for c in w.columns
            ),
        )
        for w in words
    )


def _visual_statuses(words, facts):
    silenced = {
        edge.by
        for edge in facts.attributions
        if isinstance(edge, Silenced) and edge.by is not None
    }
    merged = {
        edge.sound: edge.by
        for edge in facts.attributions
        if isinstance(edge, Merged)
        and edge.by is not None
        and facts.occurrences[edge.by].rule.value.startswith("idgham_")
    }
    out = []
    for word in words:
        columns = []
        for col in word.columns:
            merger_source = any(s.value in merged for s in col.presented_sound_ids)
            if merger_source:
                columns.append(replace(col, status=CellStatus.PRESENT, silence=None))
                continue
            cause = next(
                (o for o in col.rule_occurrence_ids if o.value in silenced), None
            )
            empty = not col.owned_sound_ids and not col.presented_sound_ids
            if cause is not None and empty:
                col = replace(col, status=CellStatus.DROPPED, silence=cause)
            columns.append(col)
        out.append(replace(word, columns=tuple(columns)))
    return tuple(out)


def project_words(
    words: tuple[CellWord, ...],
    facts: AnalysisFacts,
    source: SourceView,
    insc: InscriptionFacts,
    pen: Pen,
    *,
    riwayah: str,
) -> tuple[CellWord, ...]:
    """Fold marks, supply carriers, place rules, and state every visual group."""
    out = tuple(clean_structural_marks(word) for word in words)
    out = tuple(fold_maqsura_daggers(word) for word in out)
    out = tuple(fold_sukun(word) for word in out)
    slot_of_unit = slot_of_columns(source, insc)
    pausal = pausal_slots(facts)
    out = tuple(
        fold_pausal_sukun(word, facts, slot_of_unit, pen, pausal) for word in out
    )
    next_id = next_column_id(out)
    carried = []
    for word in out:
        projected, next_id = ensure_carriers(
            word, facts, insc, slot_of_unit, pen, next_id
        )
        carried.append(projected)
    out = _place_rules(tuple(carried), facts, slot_of_unit)
    out = tuple(fold_vowel_ishmam_presenter(word) for word in out)
    out = transform_plain_madd(out, facts)
    out = _visual_statuses(out, facts)
    out = preserve_semantic_cells(out, facts)
    out = split_carried_naql_alif(out, facts, source)
    out = fold_article_naql_madd(out, facts)
    if riwayah == "warsh":
        out = project_warsh_compounds(out, facts, insc, pen)
    out = keep_pausal_alif_on_carriers(out, facts, slot_of_unit)
    out = tuple(fold_shared_silence_riders(word, source, facts) for word in out)
    next_id = next_column_id(out)
    started = []
    for word in out:
        projected, next_id = ensure_started_qualities(
            word, facts, insc, pen, next_id
        )
        started.append(projected)
    out = tuple(started)
    return group_words(out, facts)


__all__ = ["project_words"]
