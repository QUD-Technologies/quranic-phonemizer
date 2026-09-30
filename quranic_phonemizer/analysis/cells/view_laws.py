"""Validation the nested cell view must pass before a consumer reads it.

One stop-sign column per internal boundary, every core sound in exactly one
cell, a bridge that resolves to its merger, no bridge on an iltiqa, and closure.
"""

from __future__ import annotations

from ...model.canon import ILTIQA_RULES
from ...render.alphabet import (
    is_eased_hamza_token,
    is_hamza_token,
)
from ..checks import requirer
from ..dtos import AnalysisBundle
from ..source_dtos import SourceView
from .cardinality_laws import check_cell_cardinality
from .dtos import CellRole, CellSound, CellStatus, CellView
from .laws import CellValidationError
from .view_identity_laws import (
    check_carrier_identity_placement,
    check_weight_identity_placement,
)

_require = requirer(CellValidationError)
_HAMZA_GLYPHS = frozenset("ءأإؤئٕٔ")


def _all_columns(view: CellView) -> dict[int, object]:
    out: dict[int, object] = {}
    for word in view.words:
        for col in word.columns:
            out[col.id.value] = col
    for boundary in view.boundaries:
        for col in boundary.columns:
            out[col.id.value] = col
    return out


def _check_attachments(view: CellView) -> None:
    """A mark sits on a column that exists; a fold must carry it along."""
    columns = _all_columns(view)
    for column in columns.values():
        host = column.attached_to_column_id
        _require(
            host is None or host.value in columns,
            f"column {column.id.value} is attached to missing column {getattr(host, 'value', host)}",
        )


def _all_cells(view: CellView) -> list[CellSound]:
    cells: list[CellSound] = [c for word in view.words for c in word.sounds]
    for word in view.words:
        cells.extend(bridge.sound for bridge in word.bridges)
    for boundary in view.boundaries:
        cells.extend(boundary.sounds)
        cells.extend(bridge.sound for bridge in boundary.bridges)
    return cells


def _check_stop_signs(view: CellView, bundle: AnalysisBundle) -> None:
    after_words = {b.id.value for b in bundle.boundaries if b.before is not None}
    got = {cb.boundary_id.value for cb in view.boundaries}
    _require(
        got == after_words, "the cell boundaries are not the after-word boundaries"
    )
    for cb in view.boundaries:
        signs = [c for c in cb.columns if c.role is CellRole.STOP_SIGN]
        _require(len(signs) == 1, "an internal boundary has not one stop-sign column")
        _require(
            not signs[0].owned_sound_ids and not signs[0].presented_sound_ids,
            "a stop-sign column owns a sound",
        )


def _check_one_cell_per_sound(view: CellView, bundle: AnalysisBundle) -> None:
    held: dict[int, int] = {}
    for cell in _all_cells(view):
        sid = cell.sound_id.value
        held[sid] = held.get(sid, 0) + 1
    _require(
        set(held) == {s.id.value for s in bundle.sounds},
        "the cells are not exactly the core sounds",
    )
    _require(all(n == 1 for n in held.values()), "a core sound has two cells")


def _mergers_at(bundle: AnalysisBundle) -> dict[int, set[int]]:
    out: dict[int, set[int]] = {}
    for merger in bundle.mergers:
        if merger.boundary_id is None:
            continue
        out.setdefault(merger.boundary_id.value, set()).add(merger.id.value)
    return out


def _check_one_bridge(
    bridge,
    merger,
    columns,
    rules: dict[int, object],
) -> None:
    _require(bridge.sound.sound_id == merger.sound_id, "a bridge owns another sound")
    endpoints = (*bridge.before_column_ids, *bridge.after_column_ids)
    _require(
        all(column.value in columns for column in endpoints),
        "a bridge endpoint names no column",
    )
    _require(
        all(
            merger.sound_id in columns[c.value].presented_sound_ids
            for c in bridge.before_column_ids
        ),
        "a bridge contributor does not present its sound",
    )
    _require(
        all(
            merger.sound_id in columns[c.value].owned_sound_ids
            for c in bridge.after_column_ids
        ),
        "a bridge host does not own its sound",
    )
    _require(
        set(bridge.sound.column_ids)
        == {*bridge.before_column_ids, *bridge.after_column_ids},
        "a bridge sound does not span its endpoints",
    )
    _require(
        bridge.sound.rule_occurrence_ids == rules[merger.sound_id.value],
        "a bridge sound's rules are not its sound's",
    )


def _check_internal_bridge(bridge, merger, columns, rules) -> None:
    _require(
        bridge.sound.sound_id == merger.sound_id, "a word bridge owns another sound"
    )
    _require(
        all(
            merger.sound_id in columns[c.value].presented_sound_ids
            for c in bridge.before_column_ids
        ),
        "a word bridge contributor does not present its sound",
    )
    _require(
        all(
            merger.sound_id in columns[c.value].owned_sound_ids
            for c in bridge.after_column_ids
        ),
        "a word bridge host does not own its sound",
    )
    _require(
        set(bridge.sound.column_ids)
        == {*bridge.before_column_ids, *bridge.after_column_ids},
        "a word bridge sound does not span its endpoints",
    )
    _require(
        bridge.sound.rule_occurrence_ids == rules[merger.sound_id.value],
        "a word bridge sound's rules are not its sound's",
    )


def _check_word_bridges(view, bundle, mergers, columns, rules) -> None:
    internal = {
        word: {
            m.id.value
            for m in bundle.mergers
            if m.boundary_id is None and m.before_word_id.value == word
        }
        for word in range(len(bundle.words))
    }
    for word in view.words:
        seen: set[int] = set()
        for bridge in word.bridges:
            merger = mergers.get(bridge.merger_id.value)
            _require(merger is not None, "a word bridge resolves to no merger")
            _require(merger.boundary_id is None, "a word bridge names a boundary")
            _require(
                merger.before_word_id == word.word_id,
                "a word bridge sits in another word",
            )
            _require(
                bridge.merger_id.value not in seen,
                "an intra-word merger has two bridges",
            )
            seen.add(bridge.merger_id.value)
            _check_internal_bridge(bridge, merger, columns, rules)
        _require(
            seen == internal[word.word_id.value],
            "a word's bridges are not its internal mergers",
        )


def _check_bridges(view: CellView, bundle: AnalysisBundle, source: SourceView) -> None:
    mergers = {m.id.value: m for m in bundle.mergers}
    del source
    rules = {s.id.value: s.rule_occurrence_ids for s in bundle.sounds}
    at = _mergers_at(bundle)
    columns = _all_columns(view)
    for cb in view.boundaries:
        seen: set[int] = set()
        for bridge in cb.bridges:
            merger = mergers.get(bridge.merger_id.value)
            _require(merger is not None, "a bridge resolves to no merger")
            _require(
                merger.boundary_id == cb.boundary_id, "a bridge sits off its boundary"
            )
            _require(bridge.merger_id.value not in seen, "a merger has two bridges")
            seen.add(bridge.merger_id.value)
            _check_one_bridge(
                bridge,
                merger,
                columns,
                rules,
            )
        _require(
            seen == at.get(cb.boundary_id.value, set()),
            "a boundary's bridges are not its mergers",
        )
    _check_word_bridges(view, bundle, mergers, columns, rules)


def _iltiqa_binds(bundle: AnalysisBundle) -> tuple[set[int], set[int]]:
    """The boundaries and sounds an iltiqa occurrence binds. Its connecting vowel
    is a host word's own sound, not a merger, so neither may back a bridge."""
    boundaries: set[int] = set()
    sounds: set[int] = set()
    iltiqa = frozenset(rule.value for rule in ILTIQA_RULES)
    for occ in bundle.rule_occurrences:
        if occ.rule_id.value in iltiqa:
            boundaries.update(b.value for b in occ.boundary_ids)
            sounds.update(s.value for s in occ.sound_ids)
    return boundaries, sounds


def _check_no_iltiqa_bridge(view: CellView, bundle: AnalysisBundle) -> None:
    """An iltiqa is never a merger: its boundary carries no bridge, its host-owned
    sound backs none, and no boundary insertion column is a bridge endpoint."""
    iltiqa_boundaries, iltiqa_sounds = _iltiqa_binds(bundle)
    for cb in view.boundaries:
        inserted = {c.id.value for c in cb.columns if c.status is CellStatus.INSERTED}
        for bridge in cb.bridges:
            _require(
                cb.boundary_id.value not in iltiqa_boundaries,
                "a bridge sits on an iltiqa boundary",
            )
            _require(
                bridge.sound.sound_id.value not in iltiqa_sounds,
                "a bridge holds an iltiqa sound",
            )
            endpoints = {
                c.value for c in (*bridge.before_column_ids, *bridge.after_column_ids)
            }
            _require(
                inserted.isdisjoint(endpoints),
                "a bridge endpoint is a boundary insertion column",
            )


def _check_closure(view: CellView, bundle: AnalysisBundle) -> None:
    columns = set(_all_columns(view))
    sounds = {s.id.value for s in bundle.sounds}
    mergers = {m.id.value for m in bundle.mergers}
    for cell in _all_cells(view):
        _require(cell.sound_id.value in sounds, "a cell names an unknown sound")
        for cid in cell.column_ids:
            _require(cid.value in columns, "a cell spans an unknown column")
    for cb in view.boundaries:
        for bridge in cb.bridges:
            _require(
                bridge.merger_id.value in mergers, "a bridge names an unknown merger"
            )
            for cid in (*bridge.before_column_ids, *bridge.after_column_ids):
                _require(cid.value in columns, "a bridge endpoint is an unknown column")
    for word in view.words:
        for bridge in word.bridges:
            _require(
                bridge.merger_id.value in mergers,
                "a word bridge names an unknown merger",
            )
            for cid in (*bridge.before_column_ids, *bridge.after_column_ids):
                _require(
                    cid.value in columns, "a word bridge endpoint is an unknown column"
                )


def validate_spoken_hamza_glyphs(
    view: CellView,
    bundle: AnalysisBundle,
) -> None:
    """Every plain hamza sound has a visible original or replacement glyph."""
    columns = _all_columns(view).values()
    rules = {
        occurrence.id: occurrence.rule_id.value
        for occurrence in bundle.rule_occurrences
    }
    for sound in bundle.sounds:
        if not is_hamza_token(sound.token):
            continue
        owners = [column for column in columns if sound.id in column.owned_sound_ids]
        _require(owners, f"spoken hamza {sound.id.value} has no owning column")
        _require(
            any(
                any(glyph in column.text for glyph in _HAMZA_GLYPHS)
                or any(
                    is_eased_hamza_token(bundle.sounds[item.value].token)
                    for item in column.owned_sound_ids
                )
                or any(
                    rules[occurrence] == "tashil"
                    for occurrence in column.rule_occurrence_ids
                )
                for column in owners
            ),
            f"spoken hamza {sound.id.value} has no visible hamza glyph",
        )


def _check_groups(view: CellView) -> None:
    if not any(word.groups for word in view.words):
        return
    for word in view.words:
        columns_by_id = {column.id: column for column in word.columns}
        columns = set(columns_by_id)
        sounds = {sound.sound_id for sound in word.sounds}
        claimed_columns = [item for group in word.groups for item in group.column_ids]
        claimed_sounds = [item for group in word.groups for item in group.sound_ids]
        _require(
            set(claimed_columns) == columns and len(claimed_columns) == len(columns),
            "the groups do not partition a word's columns",
        )
        _require(
            set(claimed_sounds) == sounds and len(claimed_sounds) == len(sounds),
            "the groups do not partition a word's sounds",
        )
        _require(
            all(group.key in group.column_ids for group in word.groups),
            "a group key is not one of its columns",
        )


def _check_tanween_naql_bridges(
    view: CellView,
    bundle: AnalysisBundle,
) -> None:
    """Tanween Naql labels its boundary haraka and sound, not the tanween."""
    columns = _all_columns(view)
    rules = {
        occurrence.id: occurrence.rule_id.value
        for occurrence in bundle.rule_occurrences
    }
    for boundary in view.boundaries:
        for bridge in boundary.bridges:
            naql = {
                occurrence
                for occurrence in bridge.sound.rule_occurrence_ids
                if rules[occurrence] == "naql"
            }
            before = [columns[item.value] for item in bridge.before_column_ids]
            if not naql or not any(
                column.role is CellRole.TANWEEN for column in before
            ):
                continue
            if bundle.sounds[bridge.sound.sound_id.value].token.endswith(":"):
                # Naql + Badal is a distinct long merger whose written owner
                # is the carrier; this law is for the transferred short
                # haraka created at a tanween boundary.
                continue
            after = [columns[item.value] for item in bridge.after_column_ids]
            _require(
                after and all(column.role is CellRole.HARAKA for column in after),
                "a tanween Naql bridge does not end on its written haraka",
            )
            _require(
                all(column in boundary.columns for column in after),
                "a tanween Naql haraka does not live in its boundary",
            )
            _require(
                all(naql.isdisjoint(column.rule_occurrence_ids) for column in before),
                "a tanween glyph is labelled with Naql",
            )
            _require(
                all(naql.issubset(column.rule_occurrence_ids) for column in after),
                "a tanween Naql boundary haraka lacks its Naql label",
            )


def validate_cell_view(
    view: CellView, bundle: AnalysisBundle, source: SourceView
) -> None:
    _check_stop_signs(view, bundle)
    _check_attachments(view)
    _check_one_cell_per_sound(view, bundle)
    _check_no_iltiqa_bridge(view, bundle)
    _check_bridges(view, bundle, source)
    _check_closure(view, bundle)
    check_cell_cardinality(view)
    _check_groups(view)
    check_carrier_identity_placement(view, bundle)
    check_weight_identity_placement(view, bundle)
    _check_tanween_naql_bridges(view, bundle)


__all__ = ["validate_cell_view", "validate_spoken_hamza_glyphs"]
