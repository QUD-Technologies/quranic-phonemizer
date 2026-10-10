"""Nest the source cell words and their between-word boundaries into one view.

Each internal boundary carries a stop-sign pause column and, for a cross-word
merger, a bridge that holds the shared sound; that sound leaves the host word.
"""

from __future__ import annotations

from dataclasses import replace

from ...model.address import Riwayah
from ...model.inscription import StopAdvice
from ...orthography.write import Pen
from ...render.alphabet import effective_extra_phonemes, packaged_alphabet
from ...riwayat import quality_fallbacks_for
from ...session import Session
from ..build import build_bundle
from ..dtos import Boundary, Merger
from ..facts import analyse
from ..ids import BoundaryId, CellColumnId
from ..inscription import inscribe
from ..source import build_source_view
from ..source_dtos import Character, CharacterKind, SourceView
from .align import next_column_id
from .boundary_hosting import move_boundary_sounds
from .columns import build_cell_words
from .dtos import (
    CellBoundary,
    CellBridge,
    CellColumn,
    CellRole,
    CellSound,
    CellStatus,
    CellTier,
    CellView,
    CellWord,
)
from .laws import CellValidationError
from .projection import project_words
from .projection_naql import (
    move_tanween_naql_haraka_to_boundary,
    place_tanween_naql_on_written_haraka,
)
from .projection_naql_badal import project_naql_badal_bridges
from .projection_semantics import (
    assign_native_iqlab_meem,
    keep_carrier_identity_off_harakas,
    keep_ibdal_off_harakas,
    keep_madd_rules_on_carriers,
    keep_taqlil_on_carriers,
    keep_waqf_drop_on_silenced_cells,
    separate_tanween_vowel_colours,
)
from .projection_weight import (
    keep_weight_labels_off_short_vowels,
    keep_weight_labels_on_sound_owners,
)
from .transform import transform_words
from .transform_laws import validate_transformed
from .view_laws import validate_cell_view, validate_spoken_hamza_glyphs


def _extract_merger_sounds(
    words: tuple[CellWord, ...], mergers: tuple[Merger, ...]
) -> tuple[tuple[CellWord, ...], dict[int, CellSound]]:
    """Pull each merger's shared CellSound out of its host word; the sound now
    lives in the bridge and renders once between the words, not inside the host."""
    held = {word.word_id.value: list(word.sounds) for word in words}
    shared: dict[int, CellSound] = {}
    for merger in mergers:
        cells = held[merger.after_word_id.value]
        cell = next((c for c in cells if c.sound_id == merger.sound_id), None)
        if cell is None:
            raise CellValidationError(
                f"merger {merger.id.value} names sound {merger.sound_id.value} "
                f"with no cell left in its host word"
            )
        cells.remove(cell)
        shared[merger.id.value] = cell
    remaining = {
        w.word_id.value: {s.sound_id for s in held[w.word_id.value]} for w in words
    }
    out = tuple(
        replace(
            w,
            sounds=tuple(held[w.word_id.value]),
            groups=tuple(
                replace(
                    g,
                    sound_ids=tuple(
                        s for s in g.sound_ids if s in remaining[w.word_id.value]
                    ),
                )
                for g in w.groups
            ),
        )
        for w in words
    )
    return out, shared


def _bridge(
    merger: Merger,
    words: tuple[CellWord, ...],
    sound: CellSound,
) -> CellBridge:
    before_word = next(word for word in words if word.word_id == merger.before_word_id)
    after_word = next(word for word in words if word.word_id == merger.after_word_id)
    before = tuple(
        column.id
        for column in before_word.columns
        if merger.sound_id in column.presented_sound_ids
    )
    after = tuple(
        column.id
        for column in after_word.columns
        if merger.sound_id in column.owned_sound_ids
    )
    return CellBridge(
        merger_id=merger.id,
        before_column_ids=before,
        after_column_ids=after,
        sound=replace(sound, column_ids=(*before, *after)),
    )


def _boundary_signs(source: SourceView) -> dict[BoundaryId, tuple[Character, ...]]:
    """Every written stop or sakt sign by boundary ID, in text order; a boundary
    may carry more than one."""
    signs: dict[BoundaryId, list[Character]] = {}
    for c in source.characters:
        if c.kind is CharacterKind.STOP_SIGN:
            signs.setdefault(c.boundary_id, []).append(c)
    return {boundary: tuple(found) for boundary, found in signs.items()}


def _stop_sign_column(signs: tuple[Character, ...], new_id: int) -> CellColumn:
    return CellColumn(
        id=CellColumnId(new_id),
        role=CellRole.STOP_SIGN,
        text="".join(c.text for c in signs),
        source_character_ids=tuple(c.id for c in signs),
        source_unit_ids=(),
        tier=CellTier.MAIN,
        attached_to_column_id=None,
        status=CellStatus.PRESENT,
        rule_occurrence_ids=(),
        silence=None,
        variant_id=None,
        variant_choice=None,
        owned_sound_ids=(),
        presented_sound_ids=(),
        anchor_unit_id=None,
        side=None,
    )


def _boundaries(
    bundle,
    source: SourceView,
    words: tuple[CellWord, ...],
    shared: dict[int, CellSound],
    next_id: int,
    verse_ends: frozenset[str] | None,
) -> tuple[CellBoundary, ...]:
    bridges: dict[int, list[CellBridge]] = {}
    for merger in bundle.mergers:
        if merger.boundary_id is None:
            continue
        bridges.setdefault(merger.boundary_id.value, []).append(
            _bridge(merger, words, shared[merger.id.value])
        )
    exclusive = _exclusive_groups(bundle.boundaries)
    words = {word.id.value: word for word in bundle.words}
    signs = _boundary_signs(source)
    out: list[CellBoundary] = []
    for boundary in bundle.boundaries:
        if boundary.before is None:
            continue
        column = _stop_sign_column(signs.get(boundary.id, ()), next_id)
        next_id += 1
        out.append(
            CellBoundary(
                boundary_id=boundary.id,
                columns=(column,),
                bridges=tuple(bridges.get(boundary.id.value, ())),
                state=boundary.state,
                verse_end=_verse_end(boundary, words, verse_ends),
                exclusive_group=exclusive.get(boundary.id.value),
            )
        )
    return tuple(out)


def _word_bridges(
    words: tuple[CellWord, ...],
    mergers: tuple[Merger, ...],
    shared: dict[int, CellSound],
) -> tuple[CellWord, ...]:
    words_by_id = {word.word_id.value: word for word in words}
    by_word: dict[int, list[CellBridge]] = {}
    for merger in mergers:
        if merger.boundary_id is not None:
            continue
        word = words_by_id[merger.before_word_id.value]
        before = tuple(
            column.id
            for column in word.columns
            if merger.sound_id in column.presented_sound_ids
        )
        after = tuple(
            column.id
            for column in word.columns
            if merger.sound_id in column.owned_sound_ids
        )
        by_word.setdefault(merger.before_word_id.value, []).append(
            CellBridge(
                merger_id=merger.id,
                before_column_ids=before,
                after_column_ids=after,
                sound=replace(shared[merger.id.value], column_ids=(*before, *after)),
            )
        )
    return tuple(
        replace(word, bridges=tuple(by_word.get(word.word_id.value, ())))
        for word in words
    )


def _ayah(ref: str) -> int:
    return int(ref.split(":", 2)[1])


def _verse_end(
    boundary: Boundary, words, verse_ends: frozenset[str] | None
) -> int | None:
    if boundary.before is None:
        return None
    before = words[boundary.before.value]
    if boundary.after is None:
        return (
            _ayah(before.ref)
            if verse_ends is None or before.ref in verse_ends
            else None
        )
    after = words[boundary.after.value]
    return _ayah(before.ref) if _ayah(before.ref) != _ayah(after.ref) else None


def _exclusive_groups(boundaries: tuple[Boundary, ...]) -> dict[int, int]:
    pending = None
    group = 0
    out: dict[int, int] = {}
    for boundary in boundaries:
        if boundary.stop_advice is not StopAdvice.EITHER_STOP:
            continue
        if pending is None:
            pending = boundary.id.value
            continue
        out[pending] = group
        out[boundary.id.value] = group
        pending = None
        group += 1
    return out


def _words(
    session, bundle, source, facts, insc, spelling, pen, extra_phonemes, riwayah
):
    words = build_cell_words(
        session,
        bundle=bundle,
        view=source,
        facts=facts,
        insc=insc,
        pen=pen if spelling == "transformed" else None,
    )
    if spelling != "transformed":
        return words
    if pen is None:
        raise ValueError("the transformed spelling needs a pen")
    words = transform_words(
        words,
        session,
        source,
        pen,
        extra_phonemes=extra_phonemes,
        facts=facts,
        insc=insc,
    )
    return project_words(words, facts, source, insc, pen, riwayah=riwayah)


def _facts_with_rendering(session, riwayah, extra_phonemes):
    active = effective_extra_phonemes(Riwayah(riwayah), extra_phonemes)
    facts = analyse(
        session,
        packaged_alphabet(),
        extra_phonemes=active,
        quality_fallbacks=quality_fallbacks_for(riwayah),
    )
    return facts, active


def _check_spelling(spelling: str) -> None:
    if spelling not in ("source", "transformed"):
        raise ValueError(f"spelling must be source or transformed, got {spelling!r}")


def _shared_projection(session, metadata, extra_phonemes, bundle, source, facts, insc):
    active = effective_extra_phonemes(Riwayah(metadata["riwayah"]), extra_phonemes)
    if facts is None:
        facts, active = _facts_with_rendering(
            session, metadata["riwayah"], extra_phonemes
        )
    if insc is None:
        insc = inscribe(session)
    if bundle is None:
        bundle = build_bundle(
            session,
            **metadata,
            extra_phonemes=extra_phonemes,
            facts=facts,
            insc=insc,
        )
    if source is None:
        source = build_source_view(session, bundle=bundle, facts=facts, insc=insc)
    return facts, active, insc, bundle, source


def build_cell_view(
    session: Session,
    *,
    ref: str,
    riwayah: str,
    script: str,
    variant: dict,
    extra_phonemes: frozenset[str] = frozenset(),
    spelling: str = "source",
    pen: Pen | None = None,
    bundle=None,
    source: SourceView | None = None,
    facts=None,
    insc=None,
) -> CellView:
    _check_spelling(spelling)
    metadata = dict(ref=ref, riwayah=riwayah, script=script, variant=variant)
    facts, active, insc, bundle, source = _shared_projection(
        session, metadata, extra_phonemes, bundle, source, facts, insc
    )
    words = _words(session, bundle, source, facts, insc, spelling, pen, active, riwayah)
    words = assign_native_iqlab_meem(words, facts, riwayah, source)
    words = separate_tanween_vowel_colours(words, facts)
    words = keep_madd_rules_on_carriers(words, facts)
    words = keep_waqf_drop_on_silenced_cells(words, facts)
    words = keep_ibdal_off_harakas(words, facts, pen)
    words = keep_taqlil_on_carriers(words, facts)
    words = keep_carrier_identity_off_harakas(words, facts)
    words = keep_weight_labels_off_short_vowels(words, facts)
    words = keep_weight_labels_on_sound_owners(words, facts)
    words = project_naql_badal_bridges(words, bundle, facts)
    words = place_tanween_naql_on_written_haraka(words, bundle)
    words, shared = _extract_merger_sounds(words, bundle.mergers)
    words = _word_bridges(words, bundle.mergers, shared)
    boundaries = _boundaries(
        bundle,
        source,
        words,
        shared,
        next_column_id(words),
        (None if session.verse_ends is None else session.verse_ends),
    )
    words, boundaries = move_tanween_naql_haraka_to_boundary(
        words, boundaries, bundle, source
    )
    if spelling == "transformed":
        words, boundaries = move_boundary_sounds(words, boundaries, facts, bundle, pen)
    view = CellView(words=words, boundaries=boundaries)
    validate_cell_view(view, bundle, source)
    if spelling == "transformed":
        validate_spoken_hamza_glyphs(view, bundle)
        validate_transformed(
            view,
            source,
            session.performance.selection,
            bundle=bundle,
        )
    return view


__all__ = ["build_cell_view"]
