"""Build the source cell columns of a request from its source view.

Role and tier come from the unit kind and the reading; a riding mark attaches to
the main column its written_on names, or of the carrier or seat it qualifies.
"""
from __future__ import annotations

from dataclasses import dataclass

from ...model.address import Option, SlotId
from ...model.performance import Aspect, Consonant, Quality, Vowel
from ...render.alphabet import packaged_alphabet
from ...session import Session
from ..dtos import AnalysisBundle
from ..facts import AnalysisFacts, analyse
from ..ids import CellColumnId
from ..inscription import InscriptionFacts, inscribe
from ..source import build_source_view
from ..source_dtos import LetterUnit, LetterUnitKind, SourceView
from .align import build_cell_sounds
from .dtos import CellColumn, CellRole, CellStatus, CellTier, CellWord
from .laws import validate_cell_columns, validate_cell_sounds
from .spelled import expand_spelled_words

_MINI_MEEM = frozenset({"ۢ", "ۭ"})


@dataclass(frozen=True, slots=True)
class _Reading:
    """What the reading says about the units, keyed for column decisions."""

    long_vowel_orders: frozenset[int]
    consonant_orders: frozenset[int]
    canonical_quality: dict[int, Quality | None]
    slot_of_unit: dict[int, SlotId]
    owner_of_sound: dict[int, int]
    main_units: tuple[int, ...]
    main_unit_set: frozenset[int]
    variant_of_unit: dict[int, Option]
    below_units: frozenset[int]
    written_on: dict[int, int]
    mains_of_slot: dict[SlotId | None, tuple[int, ...]]
    consonant_units: frozenset[int]
    word_of_unit: dict[int, int]


def _reading(view: SourceView, facts: AnalysisFacts, insc: InscriptionFacts,
             session: Session) -> _Reading:
    long_vowel = frozenset(
        i for i, f in enumerate(facts.sounds)
        if isinstance(f.value, Vowel) and f.value.long
    )
    consonant = frozenset(
        i for i, f in enumerate(facts.sounds) if isinstance(f.value, Consonant)
    )
    slot_of_unit = {
        unit.id.value: insc.slot_of[min(c.value for c in unit.character_ids)]
        for unit in view.units if unit.character_ids
    }
    canonical_quality = {
        uid: facts.slots[facts.slot_index[slot]].nucleus.quality
        for uid, slot in slot_of_unit.items()
    }
    owner = {
        s.value: unit.id.value for unit in view.units for s in unit.owned_sound_ids
    }
    consonant_owners = {
        owner[sound] for sound in consonant if sound in owner
    }
    for edge in (*facts.hosts, *facts.insertions):
        if (
            edge.aspect is not Aspect.VOWEL
            or edge.sound not in owner
            or owner[edge.sound] in consonant_owners
        ):
            continue
        slot = edge.slots[0] if hasattr(edge, "slots") else edge.anchor[0]
        slot_of_unit[owner[edge.sound]] = slot
    main = tuple(
        unit.id.value for unit in view.units
        if unit.kind is LetterUnitKind.LETTER and unit.written_on_unit_id is None
    )
    below = frozenset(
        unit.id.value for unit in view.units
        if any(c.value in insc.below for c in unit.character_ids)
    )
    written_on = {
        unit.id.value: unit.written_on_unit_id.value
        for unit in view.units if unit.written_on_unit_id is not None
    }
    mains_of_slot: dict[SlotId | None, list[int]] = {}
    for unit_id in main:
        mains_of_slot.setdefault(slot_of_unit.get(unit_id), []).append(unit_id)
    consonant_units = frozenset(
        unit for sound, unit in owner.items() if sound in consonant
    )
    return _Reading(
        long_vowel, consonant, canonical_quality, slot_of_unit, owner, main,
        frozenset(main), _variant_of_unit(view, session), below, written_on,
        {slot: tuple(units) for slot, units in mains_of_slot.items()},
        consonant_units,
        {unit.id.value: unit.word_id.value for unit in view.units},
    )


def _variant_of_unit(view: SourceView, session: Session) -> dict[int, Option]:
    """On both cells of a riding-letter pair, the letter khilaf the authored
    data sites at the pair's word, but only where this request selects that
    khilaf's option."""
    selection = session.performance.selection
    out: dict[int, Option] = {}
    for unit in view.units:
        if unit.kind is not LetterUnitKind.LETTER or unit.written_on_unit_id is None:
            continue
        khilaf = session.letter_khilaf_sites.get(
            session.locations[unit.word_id.value]
        )
        if khilaf is None:
            continue
        choice = selection.chosen(khilaf)
        if choice is None:
            continue
        option = Option(khilaf, choice)
        out[unit.id.value] = option
        out[unit.written_on_unit_id.value] = option
    return out


def _role(unit: LetterUnit, reading: _Reading) -> CellRole:
    if unit.kind is LetterUnitKind.HARAKA:
        return CellRole.HARAKA
    if unit.kind is LetterUnitKind.SUKUN:
        return CellRole.SUKUN
    if unit.kind is LetterUnitKind.TANWEEN:
        return CellRole.TANWEEN
    carries = any(s.value in reading.long_vowel_orders for s in unit.owned_sound_ids)
    carries = carries and not any(
        s.value in reading.consonant_orders for s in unit.owned_sound_ids
    )
    return CellRole.MADD if carries else CellRole.LETTER


def _rides(unit: LetterUnit) -> bool:
    return unit.kind is not LetterUnitKind.LETTER or unit.written_on_unit_id is not None


def _tier(unit: LetterUnit, reading: _Reading) -> CellTier:
    """The written position of a riding mark, invariant of the boundary. A
    riding letter (the mini seen) takes its script's own position; a haraka or
    tanween is below for a kasra or kasratan and above otherwise."""
    if not _rides(unit):
        return CellTier.MAIN
    if unit.kind is LetterUnitKind.LETTER:
        quality = reading.canonical_quality.get(unit.id.value)
        if quality is None:
            target = reading.written_on.get(unit.id.value)
            quality = reading.canonical_quality.get(target)
        if (
            unit.text in _MINI_MEEM
            and quality is Quality.I
        ):
            return CellTier.BELOW
        return CellTier.BELOW if unit.id.value in reading.below_units else CellTier.ABOVE
    quality = reading.canonical_quality.get(unit.id.value)
    return (
        CellTier.BELOW
        if quality is Quality.I or unit.id.value in reading.below_units
        else CellTier.ABOVE
    )


def _main_of_slot(unit_id: int, reading: _Reading) -> int | None:
    slot = reading.slot_of_unit.get(unit_id)
    seats = [
        u for u in reading.mains_of_slot.get(slot, ()) if u != unit_id
    ]
    consonants = [u for u in seats if _owns_consonant(u, reading)]
    picked = consonants or seats
    return picked[0] if picked else None


def _followed_to_main(target: int, reading: _Reading) -> int | None:
    """A written_on target may itself be a riding mark -- the iqlab meem sits on
    the tanween, not the letter. Follow it to the main column it rests on."""
    seen: set[int] = set()
    while target not in reading.main_unit_set:
        nxt = reading.written_on.get(target)
        if nxt is None or nxt in seen:
            return _main_of_slot(target, reading)
        seen.add(target)
        target = nxt
    return target


def _seat_unit(unit: LetterUnit, reading: _Reading) -> int | None:
    """The main letter or carrier a riding mark attaches to: the unit its
    written_on names, the carrier owning a long vowel it presents, or the
    consonant seat of its own slot."""
    if unit.written_on_unit_id is not None:
        return _followed_to_main(unit.written_on_unit_id.value, reading)
    for sound in unit.presented_sound_ids:
        if sound.value not in reading.long_vowel_orders:
            continue
        owner = reading.owner_of_sound.get(sound.value)
        if (
            owner is not None
            and reading.word_of_unit.get(owner)
            == reading.word_of_unit.get(unit.id.value)
        ):
            return _followed_to_main(owner, reading)
        # A cross-word long-vowel merger is rendered as a boundary bridge.
        # Its presenter remains seated on its own word; it must not attach
        # across the boundary to the carrier that owns the shared sound.
    same_slot = _main_of_slot(unit.id.value, reading)
    if same_slot is not None:
        return same_slot
    # A trailing source sukun can be assigned the following empty canonical
    # slot even though it is visibly written on the preceding rasm carrier.
    if unit.text == "ْ" and not unit.owned_sound_ids and not unit.presented_sound_ids:
        prior = [
            candidate for candidate in reading.main_units
            if candidate < unit.id.value
            and reading.word_of_unit.get(candidate) == unit.word_id.value
        ]
        return prior[-1] if prior else None
    return None


def _owns_consonant(unit_id: int, reading: _Reading) -> bool:
    return unit_id in reading.consonant_units


def _column(unit: LetterUnit, reading: _Reading,
            column_of_unit: dict[int, int]) -> CellColumn:
    role = _role(unit, reading)
    tier = _tier(unit, reading)
    attached = None
    if tier is not CellTier.MAIN:
        seat = _seat_unit(unit, reading)
        attached = None if seat is None else CellColumnId(column_of_unit[seat])
    option = reading.variant_of_unit.get(unit.id.value)
    status = CellStatus.DROPPED if unit.silence is not None else CellStatus.PRESENT
    return CellColumn(
        id=CellColumnId(column_of_unit[unit.id.value]),
        role=role,
        text=unit.text,
        source_character_ids=unit.character_ids,
        source_unit_ids=(unit.id,),
        tier=tier,
        attached_to_column_id=attached,
        status=status,
        rule_occurrence_ids=unit.rule_occurrence_ids,
        silence=unit.silence,
        variant_id=None if option is None else option.khilaf,
        variant_choice=None if option is None else option.name,
        owned_sound_ids=unit.owned_sound_ids,
        presented_sound_ids=unit.presented_sound_ids,
        anchor_unit_id=None,
        side=None,
    )


def _anchor(unit: LetterUnit) -> int:
    return min(c.value for c in unit.character_ids)


def _words(view: SourceView, reading: _Reading) -> tuple[CellWord, ...]:
    by_word: dict[int, list[LetterUnit]] = {}
    for unit in view.units:
        by_word.setdefault(unit.word_id.value, []).append(unit)
    ordered = {w: sorted(units, key=_anchor) for w, units in by_word.items()}

    column_of_unit: dict[int, int] = {}
    for word in sorted(ordered):
        for unit in ordered[word]:
            column_of_unit[unit.id.value] = len(column_of_unit)

    out: list[CellWord] = []
    for word in sorted(ordered):
        columns = tuple(
            _column(unit, reading, column_of_unit) for unit in ordered[word]
        )
        out.append(CellWord(
            view.units[ordered[word][0].id.value].word_id, columns, ()
        ))
    return tuple(out)


def build_cell_words(
    session: Session,
    *,
    bundle: AnalysisBundle,
    view: SourceView | None = None,
    facts: AnalysisFacts | None = None,
    insc: InscriptionFacts | None = None,
    pen=None,
) -> tuple[CellWord, ...]:
    if facts is None:
        from ...riwayat import quality_fallbacks_for

        facts = analyse(
            session, packaged_alphabet(), extra_phonemes=bundle.extra_phonemes,
            quality_fallbacks=quality_fallbacks_for(bundle.riwayah),
        )
    if insc is None:
        insc = inscribe(session)
    if view is None:
        view = build_source_view(session, bundle=bundle, facts=facts, insc=insc)
    reading = _reading(view, facts, insc, session)
    words = build_cell_sounds(_words(view, reading), bundle.sounds)
    validate_cell_columns(words, view, reading.slot_of_unit)
    validate_cell_sounds(words, bundle.sounds)
    if pen is not None:
        words = expand_spelled_words(words, facts, bundle, session.score, pen)
        validate_cell_sounds(words, bundle.sounds)
    return words


__all__ = ["build_cell_words"]
