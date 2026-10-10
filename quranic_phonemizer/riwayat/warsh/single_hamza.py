"""Selected-script supplies for Warsh single-hamza replacement sites."""

from __future__ import annotations

import unicodedata
from functools import lru_cache
from pathlib import Path

from ...canon.draft import _Draft, nucleus_fact
from ...canon.passes import word_spans, word_texts
from ...dataio import load_yaml, require_keys
from ...model.address import KhilafId, Location
from ...model.canon import (
    Annotation,
    CanonLetter,
    Nucleus,
    Onset,
    Quality,
    SlotOrigin,
)
from ...model.inscription import SlotFact

_REGISTER = (
    Path(__file__).resolve().parents[2]
    / "data" / "riwayat" / "warsh" / "single_hamza.yaml"
)

_IGNORED = frozenset("ـۥۦۧۨ")


def _location(ref) -> Location:
    try:
        surah, ayah, word = (int(part) for part in ref.split(":"))
    except (AttributeError, TypeError, ValueError):
        raise ValueError(f"{_REGISTER}: invalid canonical ref {ref!r}") from None
    return Location(surah, ayah, word)


@lru_cache(maxsize=1)
def _raw_register() -> dict:
    raw = load_yaml(_REGISTER)
    require_keys(
        raw,
        {
            "schema_version",
            "fixed_counts",
            "tahqiq_exclusions",
            "canonical_absence",
            "supplied",
            "arayta",
            "arayta_bare",
            "ha_antum",
            "allai",
        },
        name=str(_REGISTER),
    )
    if raw["schema_version"] != 1:
        raise ValueError(
            f"{_REGISTER}: schema_version {raw['schema_version']!r}, expected 1"
        )
    return raw


@lru_cache(maxsize=1)
def supplied_ibdal() -> dict[Location, int]:
    """The reviewed regular sites and their selected-script host slots."""
    return {
        _location(ref): int(index)
        for ref, index in _raw_register()["supplied"].items()
    }


@lru_cache(maxsize=None)
def authored_locations(name: str) -> frozenset[Location]:
    """One closed fixed lexical register consumed by this owner."""
    raw = _raw_register()
    values = raw.get(name)
    if not isinstance(values, list):
        raise ValueError(f"{_REGISTER}: unknown location register {name!r}")
    return frozenset(_location(ref) for ref in values)


@lru_cache(maxsize=1)
def canonical_absence() -> dict[Location, str]:
    return {
        _location(ref): text
        for ref, text in _raw_register()["canonical_absence"].items()
    }


@lru_cache(maxsize=1)
def fixed_ibdal_counts() -> dict[str, int]:
    return {
        name: int(count)
        for name, count in _raw_register()["fixed_counts"].items()
    }


def _skeleton(text: str) -> str:
    return "".join(
        char for char in text
        if not unicodedata.combining(char) and char not in _IGNORED
    )


def fixed_ibdal_family(text: str) -> str | None:
    """The reviewed fixed family written by one selected-source token."""
    skeleton = _skeleton(text)
    if skeleton == "وبير":
        return "bir"
    if "بيس" in skeleton:
        return "bis"
    if skeleton == "الذيب":
        return "dhib"
    if skeleton == "سال":
        return "saal"
    if skeleton == "النسي":
        return "nasi"
    if skeleton == "ليلا" and "۬" in text:
        return "liila"
    if skeleton == "لاهب":
        return "lahab"
    if skeleton == "منساته":
        return "minsa"
    if skeleton in {"ياجوج", "وماجوج"}:
        return "yajuj"
    return None


def _fixed_target(family: str, span):
    if family == "nasi":
        return next(
            draft for draft in reversed(span)
            if draft.letter is CanonLetter.YA
        )
    if family in {"liila", "lahab"}:
        target = next(
            draft for draft in span
            if draft.nucleus.quality is Quality.A
            and draft.letter in {CanonLetter.YA, CanonLetter.HAMZA}
        )
        target.letter = CanonLetter.YA
        return target
    return next(draft for draft in span if draft.nucleus.is_long)


def _eased_hamza(after, quality: Quality) -> _Draft:
    return _Draft(
        letter=CanonLetter.HAMZA,
        onset=Onset.TASHIL,
        nucleus=Nucleus.short(quality),
        origin=SlotOrigin.WRITTEN,
        cluster=after.cluster,
        onset_declared=True,
        nucleus_declared=True,
    )


def _split_length(scribe, host, drafts, quality: Quality) -> _Draft:
    """Shorten the written long and seat an eased qata on its length marks."""
    offsets = scribe.evidence_offsets(host, SlotFact.VOWEL_LENGTH)
    host.nucleus = Nucleus.short(host.nucleus.quality)
    for offset in offsets:
        scribe.withdraw_evidence(offset, host, SlotFact.VOWEL_LENGTH)
    eased = _eased_hamza(host, quality)
    drafts.insert(drafts.index(host) + 1, eased)
    for offset in offsets[:1]:
        scribe.evidence(offset, eased, SlotFact.LETTER)
        scribe.evidence(offset, eased, nucleus_fact(eased.nucleus))
    for offset in offsets[1:]:
        scribe.decoration(offset, eased)
    return eased


def _supply_arayta(reading, span, drafts, scribe) -> None:
    """Canonicalize the tashil-able structure behind the written ibdal.

    The raa's written long is a fatha plus dagger alif; the dagger and the
    madda over it become the restored qata's seat."""
    raa = next(
        draft for draft in span
        if draft.letter is CanonLetter.RA and draft.nucleus.sounds_long
    )
    quality_offsets = scribe.evidence_offsets(raa, SlotFact.VOWEL_QUALITY)
    raa.nucleus = Nucleus.short(Quality.A)
    eased = _eased_hamza(raa, Quality.A)
    drafts.insert(drafts.index(raa) + 1, eased)
    for offset in quality_offsets[1:]:
        scribe.withdraw_evidence(offset, raa, SlotFact.VOWEL_QUALITY)
        scribe.evidence(offset, eased, SlotFact.LETTER)
        scribe.evidence(offset, eased, nucleus_fact(eased.nucleus))
    cluster = reading.clusters[raa.cluster]
    for mark in cluster.marks:
        if mark.char == "ٓ":
            scribe.decoration(mark.offset, eased)


def _supply_ha_antum(span, drafts, scribe, chosen: str) -> None:
    heh = span[0]
    if chosen == "ibdal":
        heh.annotations |= {Annotation.IBDAL}
        return
    _split_length(scribe, heh, drafts, Quality.A)
    if chosen == "ithbat":
        heh.nucleus = Nucleus.long(Quality.A)
        heh.annotations |= {Annotation.JOINED_PARTICLE}


def _supply_allai(span, drafts, scribe) -> None:
    """The continuation reading: geminate lam, inclined long, eased qata,
    and the written yaa the faces dispute at waqf."""
    lam = next(draft for draft in span if draft.letter is CanonLetter.LAM)
    yaa = span[-1]
    lam.onset = Onset.GEMINATE
    lam.onset_declared = True
    lam.nucleus = Nucleus.long(Quality.TAQLIL)
    lam.nucleus_declared = True
    if lam is not span[0] and span[0].letter is CanonLetter.WAW:
        span[0].nucleus = Nucleus.short(Quality.A)
        length_offsets = scribe.evidence_offsets(
            span[0], SlotFact.VOWEL_LENGTH
        )
        for offset in length_offsets:
            scribe.withdraw_evidence(offset, span[0], SlotFact.VOWEL_LENGTH)
    eased = _eased_hamza(lam, Quality.I)
    drafts.insert(drafts.index(yaa), eased)
    offsets = scribe.evidence_offsets(yaa, SlotFact.LETTER)
    for offset in offsets[:1]:
        scribe.evidence(offset, eased, SlotFact.LETTER)
        scribe.evidence(offset, eased, nucleus_fact(eased.nucleus))


def supply_single_hamza(definitions):
    """Build the pass supplying the reviewed single-hamza structures."""

    def supply(reading, drafts, lexicon, scribe, selection) -> None:
        del lexicon
        if scribe is None:
            return
        antum = definitions.get(KhilafId.HA_ANTUM)
        chosen_antum = (
            antum.choose(selection) if antum is not None else "ibdal"
        )
        texts = word_texts(reading)
        for word, (location, span) in enumerate(
            zip(reading.words, word_spans(reading, drafts))
        ):
            if not span:
                continue
            if location in authored_locations("arayta"):
                _supply_arayta(reading, span, drafts, scribe)
                continue
            if location in authored_locations("ha_antum"):
                _supply_ha_antum(span, drafts, scribe, chosen_antum)
                continue
            if location in authored_locations("allai"):
                _supply_allai(span, drafts, scribe)
                continue
            text = texts[word]
            family = fixed_ibdal_family(text)
            if family is not None:
                _fixed_target(family, span).annotations |= {Annotation.IBDAL}
                continue
            index = supplied_ibdal().get(location)
            if index is not None:
                span[index].annotations |= {Annotation.IBDAL}
                if "وَ۬ا" in text:
                    span[index].annotations |= {Annotation.BADAL}

    return supply


#: Source-coordinate occurrence rows for the single-hamza selectors.
_SELECTOR_SOURCES = {
    "hamza_arayta": ("all", (
        (6, 41, 2), (6, 47, 2), (6, 48, 2), (10, 50, 2), (10, 59, 2),
        (11, 28, 3), (11, 62, 3), (11, 88, 3), (17, 62, 2), (18, 62, 2),
        (19, 78, 1), (25, 43, 1), (26, 75, 2), (26, 205, 1), (28, 71, 2),
        (28, 72, 2), (35, 40, 2), (39, 36, 10), (41, 51, 2), (45, 22, 1),
        (46, 3, 2), (46, 9, 2), (53, 19, 1), (53, 32, 1), (56, 61, 1),
        (56, 66, 1), (56, 71, 1), (56, 74, 1), (67, 29, 2), (67, 31, 2),
        (96, 9, 1), (96, 11, 1), (96, 13, 1), (107, 1, 1),
    )),
    "ha_antum": ("all", (
        (3, 65, 1), (3, 119, 1), (4, 108, 1), (47, 39, 1),
    )),
    "allai_waqf": ("waqf", (
        (33, 4, 12), (58, 2, 12), (65, 4, 1), (65, 4, 12),
    )),
}


def catalogue_registers():
    """Occurrence spans per single-hamza selector, in source coordinates."""
    from ..khilaf import VariantSpan

    return {
        owner: tuple(
            VariantSpan((Location(*site),), "word", requires)
            for site in sites
        )
        for owner, (requires, sites) in _SELECTOR_SOURCES.items()
    }


__all__ = [
    "authored_locations",
    "catalogue_registers",
    "canonical_absence",
    "fixed_ibdal_family",
    "fixed_ibdal_counts",
    "supplied_ibdal",
    "supply_single_hamza",
]
