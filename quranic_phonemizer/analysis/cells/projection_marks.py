"""Written-mark composition and reading-specific cell glyph changes."""

from __future__ import annotations

from dataclasses import replace

from ...model.address import Junction
from ...model.canon import CanonLetter, VowelForm
from ...model.performance import Aspect, Consonant
from ...orthography.write import Pen
from ..facts import AnalysisFacts
from ..ids import CellColumnId, OccurrenceId
from ..source_dtos import SourceView
from .dtos import CellColumn, CellRole, CellStatus, CellTier, CellWord

DAGGER_ALIF = "ٰ"
MADD_SIGN = "ٓ"
MAQSURA = "ى"
TATWEEL = "ـ"
ISHMAM_MARK = "۫"
VOWEL_ISHMAM_MARK = "۬"


def _merged_carrier(base: CellColumn, mark: CellColumn) -> CellColumn:
    owned = tuple(dict.fromkeys((*base.owned_sound_ids, *mark.owned_sound_ids)))
    presented = tuple(
        dict.fromkeys((*base.presented_sound_ids, *mark.presented_sound_ids))
    )
    active = bool(owned or presented)
    return replace(
        base,
        role=CellRole.MADD if CellRole.MADD in {base.role, mark.role} else base.role,
        text=base.text + mark.text,
        source_character_ids=(*base.source_character_ids, *mark.source_character_ids),
        source_unit_ids=(*base.source_unit_ids, *mark.source_unit_ids),
        status=CellStatus.PRESENT if active else base.status,
        rule_occurrence_ids=tuple(
            dict.fromkeys((*base.rule_occurrence_ids, *mark.rule_occurrence_ids))
        ),
        silence=None if active else base.silence,
        owned_sound_ids=owned,
        presented_sound_ids=presented,
    )


def _remap_column(
    word: CellWord, removed: CellColumnId, kept: CellColumnId
) -> CellWord:
    columns = tuple(
        replace(
            col,
            attached_to_column_id=(
                kept
                if col.attached_to_column_id == removed
                else col.attached_to_column_id
            ),
        )
        for col in word.columns
        if col.id != removed
    )
    sounds = tuple(
        replace(
            sound,
            column_ids=tuple(
                dict.fromkeys(
                    kept if col == removed else col for col in sound.column_ids
                )
            ),
        )
        for sound in word.sounds
    )
    return replace(word, columns=columns, sounds=sounds)


def fold_maqsura_daggers(word: CellWord) -> CellWord:
    """Compose a maqsura and its riding dagger/maddah as one carrier."""
    index = 0
    while index + 1 < len(word.columns):
        base, mark = word.columns[index : index + 2]
        if (
            base.tier is CellTier.MAIN
            and mark.tier is CellTier.MAIN
            and base.text.endswith(MAQSURA)
            and mark.text.startswith(DAGGER_ALIF)
        ):
            folded = _merged_carrier(base, mark)
            columns = tuple(
                folded if col.id == base.id else col for col in word.columns
            )
            word = _remap_column(replace(word, columns=columns), mark.id, base.id)
            continue
        index += 1
    return word


def clean_structural_marks(word: CellWord) -> CellWord:
    """Remove source positioning and evidence marks from rendered cell ink."""
    return replace(
        word,
        columns=tuple(
            replace(
                col,
                text=(
                    col.text.replace(TATWEEL, "")
                    if col.role in {CellRole.HARAKA, CellRole.TANWEEN}
                    else col.text
                ).replace(ISHMAM_MARK, ""),
            )
            if TATWEEL in col.text or ISHMAM_MARK in col.text
            else col
            for col in word.columns
        ),
    )


def fold_vowel_ishmam_presenter(word: CellWord) -> CellWord:
    """Remove the `س۬يء` quality witness as an independent cell.

    Its vowel is owned by the following yaa carrier.  Once carrier projection
    has attached this soundless presenter to that madd column, retain the
    source ids on the carrier and remap the sound to the carrier alone.  The
    source mark remains available in the inscription/source views; transformed
    cells expose only semantic sound or orthography.
    """
    rider = next(
        (
            column
            for column in word.columns
            if column.text == VOWEL_ISHMAM_MARK
            and column.role is CellRole.HARAKA
            and not column.owned_sound_ids
            and column.attached_to_column_id is not None
        ),
        None,
    )
    if rider is None:
        return word
    host = next(
        (
            column for column in word.columns
            if column.id == rider.attached_to_column_id
            and column.role is CellRole.MADD
        ),
        None,
    )
    if host is None:
        return word
    merged = replace(
        host,
        source_character_ids=tuple(dict.fromkeys(
            (*rider.source_character_ids, *host.source_character_ids)
        )),
        source_unit_ids=tuple(dict.fromkeys(
            (*rider.source_unit_ids, *host.source_unit_ids)
        )),
        rule_occurrence_ids=tuple(dict.fromkeys(
            (*rider.rule_occurrence_ids, *host.rule_occurrence_ids)
        )),
        presented_sound_ids=tuple(dict.fromkeys(
            (*rider.presented_sound_ids, *host.presented_sound_ids)
        )),
    )
    columns = tuple(
        merged if column.id == host.id else column for column in word.columns
    )
    return _remap_column(replace(word, columns=columns), rider.id, host.id)


def _shared_silence_host(rider, by_id, facts):
    if (
        rider.tier is CellTier.MAIN
        or rider.status is not CellStatus.DROPPED
        or rider.attached_to_column_id is None
        or rider.owned_sound_ids
        or rider.presented_sound_ids
    ):
        return None
    host = by_id.get(rider.attached_to_column_id)
    cause = (
        facts.occurrences[rider.silence.value].rule.value
        if isinstance(rider.silence, OccurrenceId)
        else None
    )
    if (
        host is None
        or host.status is not CellStatus.DROPPED
        or host.silence != rider.silence
        or cause != "naql"
        or host.variant_id != rider.variant_id
        or host.variant_choice != rider.variant_choice
    ):
        return None
    return host


def _merge_shared_silence(columns, source, host, rider):
    character_ids = tuple(sorted(
        {*host.source_character_ids, *rider.source_character_ids},
        key=lambda item: item.value,
    ))
    unit_ids = tuple(sorted(
        {*host.source_unit_ids, *rider.source_unit_ids},
        key=lambda item: item.value,
    ))
    merged = replace(
        host,
        text="".join(source.characters[item.value].text for item in character_ids),
        source_character_ids=character_ids,
        source_unit_ids=unit_ids,
        rule_occurrence_ids=tuple(dict.fromkeys(
            (*host.rule_occurrence_ids, *rider.rule_occurrence_ids)
        )),
    )
    return [
        replace(column, attached_to_column_id=host.id)
        if column.attached_to_column_id == rider.id
        else merged if column.id == host.id else column
        for column in columns if column.id != rider.id
    ]


def fold_shared_silence_riders(
    word: CellWord, source: SourceView, facts: AnalysisFacts
) -> CellWord:
    """Fold a silenced Naql haraka into its silenced qata host."""
    columns = list(word.columns)
    while True:
        by_id = {column.id: column for column in columns}
        pair = next(
            ((host, rider) for rider in columns
             if (host := _shared_silence_host(rider, by_id, facts)) is not None),
            None,
        )
        if pair is None:
            return replace(word, columns=tuple(columns))
        columns = _merge_shared_silence(columns, source, *pair)


def _owns_consonant(col: CellColumn, facts: AnalysisFacts) -> bool:
    return col.tier is CellTier.MAIN and any(
        isinstance(facts.sounds[sound.value].value, Consonant)
        for sound in col.owned_sound_ids
    )


def _needs_pausal_sukun(col, facts, slot_of_unit, pausal) -> bool:
    slots = [
        slot_of_unit[unit.value]
        for unit in col.source_unit_ids
        if unit.value in slot_of_unit
    ]
    return any(
        slot in pausal
        or facts.slots[facts.slot_index[slot]].nucleus.stopped.form is VowelForm.ABSENT
        for slot in slots
    )


def _pausal_consonant_text(word, col, facts, slot_of_unit, pen) -> str:
    indices = [
        facts.slot_index[slot_of_unit[unit.value]]
        for unit in col.source_unit_ids
        if unit.value in slot_of_unit
    ]
    hamza = next(
        (index for index in indices if facts.slots[index].letter is CanonLetter.HAMZA),
        None,
    )
    if hamza is None:
        return col.text
    previous = hamza - 1
    quality = None
    if previous >= 0 and facts.word_of_slot[previous] == word.word_id.value:
        state = facts.slots[previous].nucleus.stopped
        if state.form is VowelForm.SHORT:
            quality = state.quality
    return pen.pausal_hamza(quality)


def pausal_slots(facts: AnalysisFacts) -> frozenset:
    """Slots whose vowel a boundary occurrence silenced."""
    return frozenset(
        slot
        for edge in facts.silences
        if edge.aspect is Aspect.VOWEL
        and edge.by is not None
        and facts.occurrences[edge.by].boundary is not None
        for slot in edge.slots
    )


def fold_pausal_sukun(
    word: CellWord, facts: AnalysisFacts, slot_of_unit, pen: Pen, pausal
) -> CellWord:
    """Put a stopped consonant's recovered sukun in its native letter cell."""
    stopped = facts.junctions[word.word_id.value] in {Junction.STOP, Junction.EDGE}
    consonants = [col for col in word.columns if _owns_consonant(col, facts)]
    final = consonants[-1] if stopped and consonants else None
    if final is not None and not _needs_pausal_sukun(
        final, facts, slot_of_unit, pausal
    ):
        final = None
    return replace(
        word,
        columns=tuple(
            replace(
                col,
                text=(
                    _pausal_consonant_text(word, col, facts, slot_of_unit, pen)
                    + pen.role("sukun")
                ),
                status=(
                    CellStatus.REPLACED
                    if col.status is CellStatus.PRESENT
                    else col.status
                ),
            )
            if final is not None
            and col.id == final.id
            and not col.text.endswith(pen.role("sukun"))
            else col
            for col in word.columns
        ),
    )


def _rule_names(col: CellColumn, facts: AnalysisFacts) -> set[str]:
    return {
        facts.occurrences[occurrence.value].rule.value
        for occurrence in col.rule_occurrence_ids
    }


def transform_plain_madd(words, facts: AnalysisFacts):
    """A munfasil shortened to tabii at waqf no longer displays a maddah."""
    return tuple(
        replace(
            word,
            columns=tuple(
                replace(
                    col,
                    text=col.text.replace(MADD_SIGN, ""),
                    status=(
                        CellStatus.REPLACED
                        if col.status is CellStatus.PRESENT
                        else col.status
                    ),
                )
                if (
                    col.role is CellRole.MADD
                    and MADD_SIGN in col.text
                    and "madd_tabii" in _rule_names(col, facts)
                    and not any(
                        name != "madd_tabii" and name.startswith("madd_")
                        for name in _rule_names(col, facts)
                    )
                )
                else col
                for col in word.columns
            ),
        )
        for word in words
    )


__all__ = [
    "DAGGER_ALIF",
    "MAQSURA",
    "clean_structural_marks",
    "fold_shared_silence_riders",
    "fold_maqsura_daggers",
    "fold_pausal_sukun",
    "pausal_slots",
    "transform_plain_madd",
]
