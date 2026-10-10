"""Reviewed source projection and register for Warsh adjacent qata hamzas."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from ...canon.draft import _Draft, nucleus_fact
from ...canon.passes import word_spans, word_texts
from ...dataio import require_keys
from ...model.address import Location
from ...model.canon import Annotation, CanonLetter, Nucleus, Onset, Quality, SlotOrigin
from ...model.inscription import SlotFact

_REGISTER = Path(__file__).resolve().parents[2] / "data/riwayat/warsh/hamza_meetings.json"


@dataclass(frozen=True, slots=True)
class MeetingRow:
    source: str
    canonical: Location
    first: Quality
    second: Quality
    scope: str
    owner: str
    exception: str | None
    previous: Location | None = None
    separated: bool = False
    """A tanwin noon sounds between the two qatas, so the joined boundary
    is ordinary naql rather than a hamza meeting."""


def _location(ref: str) -> Location:
    try:
        return Location(*(int(part) for part in ref.split(":")))
    except (AttributeError, TypeError, ValueError):
        raise ValueError(f"{_REGISTER}: invalid location {ref!r}") from None


@lru_cache(maxsize=1)
def meeting_rows() -> tuple[MeetingRow, ...]:
    raw = json.loads(_REGISTER.read_text(encoding="utf-8"))
    require_keys(raw, {"schema_version", "rows"}, name=str(_REGISTER))
    if raw["schema_version"] != 1:
        raise ValueError(f"{_REGISTER}: unsupported schema {raw['schema_version']!r}")
    rows = []
    for item in raw["rows"]:
        require_keys(
            item,
            {"source", "canonical", "first", "second", "scope", "owner", "exception"},
            name=str(_REGISTER), optional={"previous", "separated"},
        )
        rows.append(MeetingRow(
            source=str(item["source"]),
            canonical=_location(item["canonical"]),
            previous=_location(item["previous"]) if item.get("previous") else None,
            first=Quality[item["first"]], second=Quality[item["second"]],
            scope=str(item["scope"]), owner=str(item["owner"]),
            exception=item["exception"],
            separated=bool(item.get("separated", False)),
        ))
    return tuple(rows)


@lru_cache(maxsize=1)
def rows_by_target() -> dict[Location, MeetingRow]:
    return {row.canonical: row for row in meeting_rows()}


def _source_offset(reading, draft) -> int:
    return reading.clusters[draft.cluster].offset


def _split_collapsed(reading, drafts, scribe, first, quality: Quality):
    length_offsets = scribe.evidence_offsets(first, SlotFact.VOWEL_LENGTH)
    first.nucleus = Nucleus.short(Quality.A)
    for offset in length_offsets:
        scribe.withdraw_evidence(offset, first, SlotFact.VOWEL_LENGTH)
    second = _Draft(
        letter=CanonLetter.HAMZA,
        onset=Onset.PLAIN,
        nucleus=Nucleus.short(quality),
        origin=SlotOrigin.WRITTEN,
        cluster=first.cluster,
        onset_declared=True,
        nucleus_declared=True,
    )
    drafts.insert(drafts.index(first) + 1, second)
    cluster = reading.clusters[first.cluster]
    collapsed = next(
        (mark.offset for mark in cluster.marks if mark.role == "collapsed_hamza"),
        None,
    )
    offset = (
        collapsed
        if collapsed is not None
        else length_offsets[0] if length_offsets else _source_offset(reading, first)
    )
    scribe.evidence(offset, second, SlotFact.LETTER)
    scribe.evidence(offset, second, nucleus_fact(second.nucleus))
    return second


def _one_word(reading, drafts, scribe, span, row: MeetingRow) -> None:
    hamzas = [draft for draft in span if draft.letter is CanonLetter.HAMZA]
    first = hamzas[0] if hamzas else span[0]
    first_index = span.index(first)
    following = span[first_index + 1] if first_index + 1 < len(span) else None
    first.letter = CanonLetter.HAMZA
    first.onset = Onset.PLAIN
    first.nucleus = Nucleus.short(row.first)
    if following is not None and following.letter is CanonLetter.HAMZA:
        second = following
    elif row.exception == "aimma" and len(span) > 1:
        second = span[1]
        second.letter = CanonLetter.HAMZA
    else:
        second = _split_collapsed(reading, drafts, scribe, first, row.second)
    second.nucleus = Nucleus.short(row.second) if row.exception != "triple" else second.nucleus.with_quality(row.second)
    if row.owner == "fixed_tashil":
        second.onset = Onset.TASHIL


def _cluster_offsets(reading, cluster_index: int) -> frozenset[int]:
    cluster = reading.clusters[cluster_index]
    return frozenset((cluster.offset, *(mark.offset for mark in cluster.marks)))


def _restore_right_qata(reading, texts, drafts, scribe, right, row: MeetingRow):
    right_word = reading.words.index(row.canonical)
    if not texts[right_word].startswith(("ا", "أ", "إ", "ء")):
        return None
    first_cluster = next(
        index for index, cluster in enumerate(reading.clusters)
        if cluster.word == right_word
    )
    second = right[0]
    if second.cluster != first_cluster:
        second = _Draft(
            letter=CanonLetter.HAMZA, onset=Onset.PLAIN,
            nucleus=Nucleus.short(row.second), origin=SlotOrigin.WRITTEN,
            cluster=first_cluster, onset_declared=True, nucleus_declared=True,
        )
        drafts.insert(drafts.index(right[0]), second)
        scribe.retarget(_cluster_offsets(reading, first_cluster), right, second)
        cluster = reading.clusters[first_cluster]
        scribe.evidence(cluster.offset, second, SlotFact.LETTER)
        for mark in cluster.marks:
            scribe.decoration(mark.offset, second)
        # A bare selected-source qata can precede a yaa whose explicit shadda
        # was parsed as part of the collapsed carrier shape.  Restoring the
        # qata must leave that following yaa geminated (not turn إِيَّاكم
        # into the impossible /ʔ i: j a:/ sequence).
    following_index = right.index(second) + 1 if second in right else 0
    following = right[following_index] if following_index < len(right) else None
    if (
        following is not None
        and any(
            mark.role == "shadda"
            for mark in reading.clusters[following.cluster].marks
        )
    ):
        following.onset = Onset.GEMINATE
    second.letter = CanonLetter.HAMZA
    second.onset = Onset.PLAIN
    second.nucleus = Nucleus.short(row.second)
    return second


def supply_hamza_meetings(reading, drafts, lexicon, scribe, selection) -> None:
    """Project only rows attested by the checked-in selected-source register."""
    del lexicon, selection
    if scribe is None:
        return
    spans = dict(zip(reading.words, word_spans(reading, drafts)))
    texts = word_texts(reading)
    for row in meeting_rows():
        if row.canonical not in spans:
            continue
        right = spans[row.canonical]
        if not right:
            continue
        if row.scope == "one_word":
            _one_word(reading, drafts, scribe, right, row)
            continue
        joined = row.previous in spans
        second = _restore_right_qata(reading, texts, drafts, scribe, right, row)
        if second is None:
            continue
        if row.exception in {"jaa_aal", "fused_badal"}:
            # The lexical badal long stands in every state: the restored
            # qata carries it rather than a short helping vowel.
            second.nucleus = Nucleus.long(row.second)
            second.annotations |= {Annotation.BADAL}
        if not joined:
            continue
        left = spans[row.previous]
        if not left or left[-1].letter is not CanonLetter.HAMZA:
            continue
        first = left[-1]
        first.letter = CanonLetter.HAMZA
        first.onset = Onset.PLAIN
        first.nucleus = Nucleus.short(row.first)
        if row.exception == "fused_badal":
            second.annotations |= {Annotation.BADAL}


#: Selector owner tags realized through the meetings rule; `hamza_aimma`
#: rows are tagged `fixed_tashil` with the `aimma` exception.
SELECTOR_OWNERS = (
    "hamza_dhat_fath",
    "hamza_muttafiq",
    "hamza_damm_kasr",
    "jaa_aal",
    "hamza_kasr_yaa",
    "hamza_aimma",
)


def _selector_owner(row: MeetingRow) -> str | None:
    if row.exception == "aimma":
        return "hamza_aimma"
    return row.owner if row.owner in SELECTOR_OWNERS else None


def selector_choices(definitions) -> dict[str, object]:
    """Published meeting selectors by owner tag, for the boundary rule."""
    from ...model.address import KhilafId

    choices = {}
    for owner in SELECTOR_OWNERS:
        definition = definitions.get(KhilafId(owner))
        if definition is not None:
            choices[owner] = definition
    return choices


def catalogue_registers():
    """Occurrence spans per meeting selector, in source coordinates."""
    from ..khilaf import VariantSpan

    registers: dict[str, list] = {owner: [] for owner in SELECTOR_OWNERS}
    for row in meeting_rows():
        owner = _selector_owner(row)
        if owner is None or row.separated:
            continue
        second = _location(row.source)
        if row.scope == "one_word":
            registers[owner].append(VariantSpan((second,), "word", "all"))
        else:
            first = Location(second.surah, second.ayah, second.word - 1)
            registers[owner].append(
                VariantSpan((first, second), "boundary", "wasl")
            )
    return {owner: tuple(spans) for owner, spans in registers.items()}


__all__ = [
    "MeetingRow",
    "SELECTOR_OWNERS",
    "catalogue_registers",
    "meeting_rows",
    "rows_by_target",
    "selector_choices",
    "supply_hamza_meetings",
]
