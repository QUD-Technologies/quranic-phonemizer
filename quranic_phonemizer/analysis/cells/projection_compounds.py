"""Fold source spellings that represent one renderer cell."""

from __future__ import annotations

from dataclasses import replace

from ...model.canon import CanonLetter, Quality
from ...model.inscription import GlyphKind
from ...model.performance import Consonant, Vowel
from ...orthography.write import Pen
from ..ids import CellColumnId
from ..inscription import InscriptionFacts
from .align import next_column_id
from .dtos import CellRole, CellStatus, CellTier, CellWord

_HAMZA_MARKS = frozenset({"ٔ", "ٕ"})
_HAMZA_GLYPHS = frozenset("ءأإؤئٕٔ")
_SEATS = frozenset({"ا", "و", "ي", "ى", "ے"})


def _unique(items):
    return tuple(dict.fromkeys(items))


def _replace_sound_columns(word, removed, kept):
    return tuple(
        replace(
            sound,
            column_ids=_unique(
                kept if column in removed else column for column in sound.column_ids
            ),
        )
        for sound in word.sounds
    )


def _reattach(columns, removed, kept):
    """Point marks that sat on a folded-away column at the column it joined."""
    for index, column in enumerate(columns):
        if column.attached_to_column_id in removed:
            columns[index] = replace(column, attached_to_column_id=kept)


def _rules_for(word, sounds):
    wanted = set(sounds)
    return _unique(
        occurrence
        for cell in word.sounds
        if cell.sound_id in wanted
        for occurrence in cell.rule_occurrence_ids
    )


def _retarget_sounds(word, old, new, sounds):
    moved = set(sounds)
    return tuple(
        replace(
            cell,
            column_ids=_unique(
                new if column == old and cell.sound_id in moved else column
                for column in cell.column_ids
            ),
        )
        for cell in word.sounds
    )


def _split_shared_length_tashil(
    column, word, facts, pen, new_id, madd_chars, consonants, long_vowels,
):
    cells = {cell.sound_id: cell for cell in word.sounds}
    external = tuple(
        sound for sound in long_vowels
        if column.id not in cells[sound].column_ids
    )
    short = tuple(
        sound for sound in column.owned_sound_ids
        if isinstance((value := facts.sounds[sound.value].value), Vowel)
        and not value.long
    )
    bases = tuple(
        char for char in column.source_character_ids if char not in madd_chars
    )
    if not (
        len(external) == len(consonants) == len(short) == 1
        and len(madd_chars) == len(bases) == 1
    ):
        return None
    quality = facts.sounds[short[0].value].value.quality
    hamza = replace(
        column, text=pen.seated_hamza(quality), source_character_ids=bases,
        status=CellStatus.REPLACED, rule_occurrence_ids=_rules_for(word, consonants),
        owned_sound_ids=consonants, presented_sound_ids=(),
    )
    mark = replace(
        column, id=CellColumnId(new_id), role=CellRole.HARAKA,
        text=pen.short_vowel(quality), source_character_ids=madd_chars,
        tier=CellTier.BELOW if quality is Quality.I else CellTier.ABOVE,
        attached_to_column_id=hamza.id, status=CellStatus.REPLACED, silence=None,
        rule_occurrence_ids=_rules_for(word, short), owned_sound_ids=short,
        presented_sound_ids=(),
    )
    return hamza, mark, short, external


def _split_hamza_madd_column(column, word, facts, insc, pen, new_id):
    madd_chars = tuple(
        char
        for char in column.source_character_ids
        if insc.glyphs[char.value].kind is GlyphKind.MADD_SIGN
    )
    consonants = tuple(
        sound
        for sound in column.owned_sound_ids
        if isinstance(facts.sounds[sound.value].value, Consonant)
    )
    vowels = tuple(
        sound
        for sound in column.owned_sound_ids
        if isinstance((value := facts.sounds[sound.value].value), Vowel)
        and value.long
        and value.quality is Quality.A
    )
    if not madd_chars or not consonants or not vowels:
        return None
    shared = _split_shared_length_tashil(
        column, word, facts, pen, new_id,
        madd_chars, consonants, vowels,
    )
    if shared is not None:
        return shared
    hamza_text = "".join(
        insc.glyphs[char.value].char
        for char in column.source_character_ids
        if char not in madd_chars
    )
    if not any(glyph in hamza_text for glyph in _HAMZA_GLYPHS) and any(
        glyph in column.text for glyph in _HAMZA_GLYPHS
    ):
        retained_marks = "".join(
            insc.glyphs[char.value].char
            for char in column.source_character_ids
            if char not in madd_chars
            and insc.glyphs[char.value].kind is not GlyphKind.BASE
        )
        hamza_text = column.text + retained_marks
    hamza = replace(
        column,
        text=hamza_text,
        source_character_ids=tuple(
            char for char in column.source_character_ids if char not in madd_chars
        ),
        rule_occurrence_ids=_rules_for(word, consonants),
        owned_sound_ids=consonants,
    )
    carrier = replace(
        column,
        id=CellColumnId(new_id),
        role=CellRole.MADD,
        text=pen.short_vowel(Quality.A) + pen.performed_carrier(Quality.A)[1],
        source_character_ids=madd_chars,
        tier=CellTier.MAIN,
        attached_to_column_id=None,
        status=CellStatus.REPLACED,
        silence=None,
        rule_occurrence_ids=_rules_for(word, vowels),
        owned_sound_ids=vowels,
        presented_sound_ids=(),
    )
    return hamza, carrier, vowels, ()


def _reattach_external_presenters(columns, sounds):
    wanted = set(sounds)
    owner = next((
        column for column in columns
        if column.role is CellRole.MADD
        and wanted.intersection(column.owned_sound_ids)
    ), None)
    if owner is None:
        return
    for index, column in enumerate(columns):
        if wanted.intersection(column.presented_sound_ids):
            columns[index] = replace(column, attached_to_column_id=owner.id)


def split_hamza_madd_carriers(
    words: tuple[CellWord, ...], facts, insc: InscriptionFacts, pen: Pen
) -> tuple[CellWord, ...]:
    """Give a written hamza and its madd evidence separate sound ownership."""
    next_id = next_column_id(words)
    out = []
    for word in words:
        columns = []
        for column in word.columns:
            split = _split_hamza_madd_column(column, word, facts, insc, pen, next_id)
            if split is None:
                columns.append(column)
                continue
            hamza, carrier, vowels, external = split
            _reattach_external_presenters(columns, external)
            columns.extend((hamza, carrier))
            word = replace(
                word,
                sounds=_retarget_sounds(word, column.id, carrier.id, vowels),
            )
            next_id += 1
        out.append(replace(word, columns=tuple(columns)))
    return tuple(out)


def _column_rules(column, facts):
    return {
        facts.occurrences[item.value].rule.value
        for item in column.rule_occurrence_ids
    }


def _is_eased_mark(column, facts):
    values = tuple(
        facts.sounds[sound.value].value for sound in column.owned_sound_ids
    )
    return (
        column.text == "۬"
        and len(values) == 1
        and isinstance(values[0], Consonant)
        and values[0].letter is CanonLetter.HAMZA
        and values[0].eased
        and "tashil" in _column_rules(column, facts)
    )


def _is_inserted_a_badal(column, facts):
    values = tuple(
        facts.sounds[sound.value].value for sound in column.owned_sound_ids
    )
    return (
        column.role is CellRole.MADD
        and column.status is CellStatus.INSERTED
        and not column.source_character_ids
        and len(values) == 1
        and isinstance(values[0], Vowel)
        and values[0].long
        and values[0].quality is Quality.A
        and "madd_badal" in _column_rules(column, facts)
    )


def _triple_hamza_cells(window, facts, pen):
    alif, eased, inserted, dagger = window
    if not (
        alif.text == "ا"
        and alif.status is CellStatus.DROPPED
        and not alif.owned_sound_ids
        and not alif.presented_sound_ids
        and _is_eased_mark(eased, facts)
        and _is_inserted_a_badal(inserted, facts)
        and dagger.text == "ٰ"
        and dagger.presented_sound_ids == inserted.owned_sound_ids
    ):
        return None
    hamza = replace(
        eased, text=pen.seated_hamza(Quality.A), tier=CellTier.MAIN,
        attached_to_column_id=None, status=CellStatus.REPLACED,
    )
    carrier = replace(
        alif, role=CellRole.MADD, text=pen.performed_carrier(Quality.A)[1],
        source_character_ids=_unique(
            (*alif.source_character_ids, *dagger.source_character_ids)
        ),
        source_unit_ids=_unique((*alif.source_unit_ids, *dagger.source_unit_ids)),
        status=CellStatus.REPLACED, silence=None,
        rule_occurrence_ids=inserted.rule_occurrence_ids,
        owned_sound_ids=inserted.owned_sound_ids, presented_sound_ids=(),
        slot_ids=_unique((*alif.slot_ids, *dagger.slot_ids)),
    )
    return hamza, carrier


def fold_triple_hamza_badal(words, facts, pen):
    """Project fixed tashil followed by lexical badal as two source cells."""
    out = []
    for word in words:
        columns, at = list(word.columns), 0
        while at + 3 < len(columns):
            folded = _triple_hamza_cells(columns[at : at + 4], facts, pen)
            if folded is None:
                at += 1
                continue
            inserted, dagger = columns[at + 2 : at + 4]
            columns[at : at + 4] = folded
            _reattach(columns, {inserted.id, dagger.id}, folded[1].id)
            word = replace(word, sounds=_replace_sound_columns(
                word, {inserted.id, dagger.id}, folded[1].id,
            ))
            at += 2
        out.append(replace(word, columns=tuple(columns)))
    return tuple(out)


def fold_combining_hamza_seats(words: tuple[CellWord, ...]) -> tuple[CellWord, ...]:
    """A rasm seat plus combining hamza is one sounded hamza cell."""
    out = []
    for word in words:
        columns = list(word.columns)
        at = 0
        while at + 1 < len(columns):
            seat, hamza = columns[at : at + 2]
            if not (
                seat.text in _SEATS
                and seat.status is CellStatus.DROPPED
                and not seat.owned_sound_ids
                and not seat.presented_sound_ids
                and hamza.role is CellRole.LETTER
                and any(mark in hamza.text for mark in _HAMZA_MARKS)
            ):
                at += 1
                continue
            columns[at] = replace(
                seat,
                text=seat.text + hamza.text,
                source_character_ids=_unique(
                    (
                        *seat.source_character_ids,
                        *hamza.source_character_ids,
                    )
                ),
                source_unit_ids=_unique(
                    (
                        *seat.source_unit_ids,
                        *hamza.source_unit_ids,
                    )
                ),
                status=CellStatus.PRESENT,
                silence=None,
                rule_occurrence_ids=_unique(
                    (
                        *seat.rule_occurrence_ids,
                        *hamza.rule_occurrence_ids,
                    )
                ),
                owned_sound_ids=hamza.owned_sound_ids,
                presented_sound_ids=hamza.presented_sound_ids,
            )
            del columns[at + 1]
            _reattach(columns, {hamza.id}, seat.id)
            word = replace(
                word,
                sounds=_replace_sound_columns(word, {hamza.id}, seat.id),
            )
            at += 1
        out.append(replace(word, columns=tuple(columns)))
    return tuple(out)


def fold_marked_ibdal_carriers(
    words: tuple[CellWord, ...], facts
) -> tuple[CellWord, ...]:
    """Keep a dropped marked hamza inside its sounded moving-ibdal carrier."""
    out = []
    for word in words:
        columns = list(word.columns)
        at = 0
        while at + 1 < len(columns):
            carrier, hamza = columns[at : at + 2]
            rules = {
                facts.occurrences[item.value].rule.value
                for item in carrier.rule_occurrence_ids
            }
            if not (
                carrier.text in _SEATS
                and carrier.status is CellStatus.PRESENT
                and carrier.owned_sound_ids
                and "ibdal_hamza" in rules
                and hamza.text == "۬"
                and hamza.status is CellStatus.DROPPED
                and hamza.attached_to_column_id == carrier.id
                and not hamza.owned_sound_ids
                and not hamza.presented_sound_ids
            ):
                at += 1
                continue
            columns[at] = replace(
                carrier,
                source_character_ids=_unique(
                    (
                        *carrier.source_character_ids,
                        *hamza.source_character_ids,
                    )
                ),
                source_unit_ids=_unique(
                    (
                        *carrier.source_unit_ids,
                        *hamza.source_unit_ids,
                    )
                ),
                rule_occurrence_ids=_unique(
                    (
                        *carrier.rule_occurrence_ids,
                        *hamza.rule_occurrence_ids,
                    )
                ),
                slot_ids=_unique((*carrier.slot_ids, *hamza.slot_ids)),
            )
            del columns[at + 1]
            _reattach(columns, {hamza.id}, carrier.id)
            word = replace(
                word,
                sounds=_replace_sound_columns(word, {hamza.id}, carrier.id),
            )
            at += 1
        out.append(replace(word, columns=tuple(columns)))
    return tuple(out)


def fold_naql_badal_alif_daggers(
    words: tuple[CellWord, ...], facts
) -> tuple[CellWord, ...]:
    """Keep a naql-dropped hamza alif with its surviving badal carrier."""
    out = []
    for word in words:
        columns = list(word.columns)
        at = 0
        while at + 1 < len(columns):
            alif, dagger = columns[at : at + 2]
            alif_rules = {
                facts.occurrences[item.value].rule.value
                for item in alif.rule_occurrence_ids
            }
            dagger_rules = {
                facts.occurrences[item.value].rule.value
                for item in dagger.rule_occurrence_ids
            }
            if not (
                alif.text == "ا"
                and alif.status is CellStatus.DROPPED
                and not alif.owned_sound_ids
                and not alif.presented_sound_ids
                and dagger.role is CellRole.MADD
                and dagger.text.startswith("ٰ")
                and bool(dagger.owned_sound_ids or dagger.presented_sound_ids)
                and "naql" in alif_rules
                and "madd_badal" in dagger_rules
            ):
                at += 1
                continue
            combined = replace(
                alif,
                role=CellRole.MADD,
                text=alif.text + dagger.text,
                source_character_ids=_unique(
                    (
                        *alif.source_character_ids,
                        *dagger.source_character_ids,
                    )
                ),
                source_unit_ids=_unique(
                    (
                        *alif.source_unit_ids,
                        *dagger.source_unit_ids,
                    )
                ),
                status=CellStatus.PRESENT,
                silence=None,
                rule_occurrence_ids=_unique(
                    (
                        *alif.rule_occurrence_ids,
                        *dagger.rule_occurrence_ids,
                    )
                ),
                owned_sound_ids=dagger.owned_sound_ids,
                presented_sound_ids=dagger.presented_sound_ids,
                slot_ids=_unique((*alif.slot_ids, *dagger.slot_ids)),
            )
            columns[at : at + 2] = [combined]
            _reattach(columns, {dagger.id}, alif.id)
            word = replace(
                word,
                sounds=_replace_sound_columns(word, {dagger.id}, alif.id),
            )
        out.append(replace(word, columns=tuple(columns)))
    return tuple(out)


def fold_article_naql_madd(words: tuple[CellWord, ...], facts) -> tuple[CellWord, ...]:
    """Keep the written fatha/qata-alif and its long vowel in one cell."""
    out = []
    for word in words:
        columns = list(word.columns)
        at = 0
        while at + 2 < len(columns):
            haraka, alif, madd = columns[at : at + 3]
            rules = {
                facts.occurrences[item.value].rule.value
                for item in (*haraka.rule_occurrence_ids, *alif.rule_occurrence_ids)
            }
            madd_rules = {
                facts.occurrences[item.value].rule.value
                for item in madd.rule_occurrence_ids
            }
            if not (
                haraka.role is CellRole.HARAKA
                and haraka.text == "َ"
                and alif.text == "ا"
                and alif.status is CellStatus.DROPPED
                and madd.role is CellRole.MADD
                and madd.status is CellStatus.INSERTED
                and "naql" in rules
                and any(rule.startswith("madd_") for rule in madd_rules)
            ):
                at += 1
                continue
            combined = replace(
                alif,
                role=CellRole.MADD,
                text=haraka.text + alif.text,
                source_character_ids=_unique(
                    (*haraka.source_character_ids, *alif.source_character_ids)
                ),
                source_unit_ids=_unique(
                    (*haraka.source_unit_ids, *alif.source_unit_ids)
                ),
                tier=CellTier.MAIN,
                attached_to_column_id=None,
                status=CellStatus.PRESENT,
                silence=None,
                rule_occurrence_ids=_unique(
                    (
                        *haraka.rule_occurrence_ids,
                        *alif.rule_occurrence_ids,
                        *madd.rule_occurrence_ids,
                    )
                ),
                owned_sound_ids=madd.owned_sound_ids,
                presented_sound_ids=madd.presented_sound_ids,
            )
            removed = {haraka.id, madd.id}
            columns[at : at + 3] = [combined]
            _reattach(columns, removed, alif.id)
            word = replace(
                word,
                sounds=_replace_sound_columns(word, removed, alif.id),
            )
            at += 1
        out.append(replace(word, columns=tuple(columns)))
    return tuple(out)


def project_warsh_compounds(words, facts, insc, pen):
    words = fold_naql_badal_alif_daggers(words, facts)
    words = fold_triple_hamza_badal(words, facts, pen)
    words = split_hamza_madd_carriers(words, facts, insc, pen)
    words = fold_combining_hamza_seats(words)
    return fold_marked_ibdal_carriers(words, facts)

__all__ = [
    "fold_article_naql_madd",
    "fold_combining_hamza_seats",
    "fold_marked_ibdal_carriers",
    "fold_naql_badal_alif_daggers",
    "fold_triple_hamza_badal",
    "project_warsh_compounds",
    "split_hamza_madd_carriers",
]
