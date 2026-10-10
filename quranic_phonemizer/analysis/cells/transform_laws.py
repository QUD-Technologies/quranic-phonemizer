"""Validation the transformed cell view must pass before a consumer reads it.

An inserted column invents no source and anchors validly, a replaced or dropped
column keeps its provenance, and variant fields match the resolved selection.
"""

from __future__ import annotations

from ...model.address import VariantSelection
from ...render.alphabet import is_eased_hamza_token
from ..checks import requirer
from ..dtos import AnalysisBundle
from ..source_dtos import SourceView
from .dtos import CellColumn, CellRole, CellStatus, CellTier, CellView, CellWord
from .laws import CellValidationError

_require = requirer(CellValidationError)


def _all_columns(view: CellView) -> list[CellColumn]:
    out = [col for word in view.words for col in word.columns]
    for boundary in view.boundaries:
        out.extend(boundary.columns)
    return out


def _check_inserted(col: CellColumn, units: int) -> None:
    _require(
        not col.source_character_ids and not col.source_unit_ids,
        f"inserted column {col.id.value} invents a source character or unit",
    )
    _require(
        col.anchor_unit_id is not None and col.side is not None,
        f"inserted column {col.id.value} has no unit and side anchor",
    )
    _require(
        col.anchor_unit_id.value < units,
        f"inserted column {col.id.value} anchors to no source unit",
    )


def _check_replaced_dropped(
    col: CellColumn, source: SourceView, split_units: set[int]
) -> None:
    _require(
        bool(col.source_unit_ids),
        f"{col.status.value} column {col.id.value} spans no source unit",
    )
    units = [source.units[uid.value] for uid in col.source_unit_ids]
    split = any(unit.id.value in split_units for unit in units)
    expected = tuple(character for unit in units for character in unit.character_ids)
    if split:
        _require(
            bool(col.source_character_ids)
            and set(col.source_character_ids).issubset(expected),
            f"{col.status.value} column {col.id.value} names characters outside its source unit",
        )
    else:
        _require(
            col.source_character_ids == expected,
            f"{col.status.value} column {col.id.value} loses its source characters",
        )
    if col.status is CellStatus.DROPPED:
        text = (
            "".join(
                source.characters[item.value].text for item in col.source_character_ids
            )
            if split
            else "".join(unit.text for unit in units)
        )
        _require(
            col.text == text,
            f"dropped column {col.id.value} loses its source text",
        )


def _is_partitioned_unit(
    unit_id: int, columns: list[CellColumn], source: SourceView
) -> bool:
    """Recognize projections that partition one written compound by glyph."""
    roles = {column.role.value for column in columns}
    text = source.units[unit_id].text
    pair = len(columns) == 2 and (
        (text in {"َا", "ُا", "ِا"} and roles == {"haraka", "letter"})
        or (text == "ا۟" and roles == {"haraka", "letter"})
        or (text == "آ" and roles == {"haraka", "letter"})
        or (text == "آٰ" and roles == {"haraka", "letter"})
        or (text in {"ٰ࢜", "ٰٓ"} and roles == {"haraka", "letter"})
        or ("ٓ" in text and roles == {"letter", "madd"})
    )
    compact_tashil = (
        len(columns) == 3
        and text.startswith("ا")
        and sum(column.role is CellRole.LETTER for column in columns) == 2
        and sum(column.role is CellRole.HARAKA for column in columns) == 1
    )
    if (
        any(not column.source_character_ids for column in columns)
        or not (pair or compact_tashil)
    ):
        return False
    expected = sorted(
        character.value for character in source.units[unit_id].character_ids
    )
    got = sorted(
        character.value
        for column in columns
        for character in column.source_character_ids
    )
    return got == expected


def _variant_dependent(col: CellColumn) -> bool:
    return (
        bool(col.owned_sound_ids or col.presented_sound_ids)
        or col.status is CellStatus.DROPPED
        or col.variant_id is not None
    )


def _check_variant(col: CellColumn, selection: VariantSelection) -> None:
    if col.variant_id is None:
        _require(
            col.variant_choice is None,
            f"column {col.id.value} names a variant choice with no variant",
        )
        return
    _require(
        col.variant_choice == selection.chosen(col.variant_id),
        f"column {col.id.value} variant choice is not the resolved selection",
    )
    _require(
        _variant_dependent(col),
        f"column {col.id.value} carries a variant on no dependent state",
    )


_VOWEL_RIDERS = frozenset({CellRole.HARAKA, CellRole.SUKUN, CellRole.TANWEEN})


def _check_no_duplicate_vowel_riders(columns: tuple[CellColumn, ...]) -> None:
    seen: dict[tuple[object, CellRole, str], CellColumn] = {}
    for column in columns:
        if (
            column.role not in _VOWEL_RIDERS
            or column.attached_to_column_id is None
            or column.status is CellStatus.DROPPED
        ):
            continue
        key = (column.attached_to_column_id, column.role, column.text)
        previous = seen.get(key)
        _require(
            previous is None,
            f"vowel rider {column.id.value} duplicates column "
            f"{previous.id.value if previous is not None else '?'}",
        )
        seen[key] = column


def _check_no_raw_eased_hamza_marks(
    columns: tuple[CellColumn, ...], bundle: AnalysisBundle
) -> None:
    for column in columns:
        _require(
            column.text != "۬"
            or not any(
                is_eased_hamza_token(bundle.sounds[sound.value].token)
                for sound in column.owned_sound_ids
            ),
            f"eased hamza mark column {column.id.value} was not transformed",
        )


def _check_no_redundant_dropped_riders(word: CellWord, rules: dict) -> None:
    columns = {column.id: column for column in word.columns}
    for rider in word.columns:
        if (
            rider.tier is CellTier.MAIN
            or rider.status is not CellStatus.DROPPED
            or rider.attached_to_column_id is None
            or rider.owned_sound_ids
            or rider.presented_sound_ids
        ):
            continue
        host = columns[rider.attached_to_column_id]
        cause = rules.get(rider.silence)
        if cause != "naql":
            continue
        _require(
            host.status is not CellStatus.DROPPED or host.silence != rider.silence,
            f"dropped rider {rider.id.value} duplicates its silenced host",
        )


def validate_transformed(
    view: CellView,
    source: SourceView,
    selection: VariantSelection,
    *,
    bundle: AnalysisBundle | None = None,
) -> None:
    units = len(source.units)
    columns_by_unit: dict[int, list[CellColumn]] = {}
    for column in _all_columns(view):
        for unit in column.source_unit_ids:
            columns_by_unit.setdefault(unit.value, []).append(column)
    split_units = {
        unit_id
        for unit_id, columns in columns_by_unit.items()
        if _is_partitioned_unit(unit_id, columns, source)
    }
    rules = {} if bundle is None else {
        occurrence.id: occurrence.rule_id.value
        for occurrence in bundle.rule_occurrences
    }
    for word in view.words:
        if bundle is not None:
            _check_no_raw_eased_hamza_marks(word.columns, bundle)
        _check_no_duplicate_vowel_riders(word.columns)
        if bundle is not None:
            _check_no_redundant_dropped_riders(word, rules)
    for col in _all_columns(view):
        if col.status is CellStatus.INSERTED:
            _check_inserted(col, units)
        elif col.status in (CellStatus.REPLACED, CellStatus.DROPPED):
            _check_replaced_dropped(col, source, split_units)
        _check_variant(col, selection)


__all__ = ["validate_transformed"]
