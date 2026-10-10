"""Inclination registers and selected-script canonical supplies."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from ...canon.passes import word_spans, word_texts
from ...model.address import KhilafId, Location
from ...model.canon import CanonLetter, Nucleus, Quality, SlotOrigin, VowelState
from ...model.inscription import SlotFact
from ..khilaf import VariantSpan

_DATA = Path(__file__).resolve().parents[2] / "data" / "riwayat" / "warsh"

FIXED_KUBRA = frozenset({Location(20, 1, 1)})
HAA_OPENINGS = frozenset(Location(surah, 1, 1) for surah in range(40, 47))
RAA_OPENINGS = frozenset(Location(surah, 1, 1) for surah in range(10, 16))
VERSE_HEAD_SURAHS = frozenset({20, 53, 70, 75, 79, 80, 87, 91, 92, 93, 96})

HAA_VERSE_HEADS = frozenset(
    {
        Location(79, 27, 6), Location(79, 28, 3), Location(79, 29, 4),
        Location(79, 30, 4), Location(79, 31, 4), Location(79, 32, 2),
        Location(79, 42, 5), Location(79, 44, 3), Location(79, 45, 5),
        Location(79, 46, 9),
        Location(91, 1, 2), Location(91, 2, 3), Location(91, 3, 3),
        Location(91, 4, 3), Location(91, 5, 3), Location(91, 6, 3),
        Location(91, 7, 3), Location(91, 8, 3), Location(91, 9, 4),
        Location(91, 10, 4), Location(91, 11, 3), Location(91, 12, 3),
        Location(91, 13, 7), Location(91, 14, 7), Location(91, 15, 3),
    }
)

LAM_DHAT_YAA = frozenset({
    Location(2, 125, 11), Location(17, 18, 16), Location(84, 12, 1),
    Location(87, 12, 2), Location(88, 4, 1), Location(92, 15, 2),
    Location(111, 3, 1),
})
LAM_VERSE_HEADS = frozenset({
    Location(75, 31, 4), Location(87, 15, 4), Location(96, 10, 3),
})
#: Wasl deletes or suppresses the inclined alif at these two coupled sites,
#: so the selection manifests only at waqf.
LAM_COUPLED_WAQF_ONLY = frozenset({Location(2, 125, 11), Location(87, 12, 2)})
_NAML_YAA_ZAWAID = Location(27, 36, 8)
_YASEEN = Location(36, 1, 1)

#: Named quality-only selectors over marked sites, keyed by canonical word.
NAMED_SITES = {
    Location(8, 43, 8): KhilafId.ARAKAHUM,
    Location(4, 36, 13): KhilafId.AL_JAR,
    Location(4, 36, 16): KhilafId.AL_JAR,
    Location(5, 22, 6): KhilafId.JABBARIN,
    Location(26, 130, 4): KhilafId.JABBARIN,
    Location(19, 1, 1): KhilafId.MARYAM_HAA_YAA,
}

#: Unbound fallbacks equal the fixed reading each supply already produced.
_DEFAULTS = {
    KhilafId.DHAT_YAA: "taqlil",
    KhilafId.ARAKAHUM: "taqlil",
    KhilafId.AL_JAR: "taqlil",
    KhilafId.JABBARIN: "taqlil",
    KhilafId.MARYAM_HAA_YAA: "taqlil",
    KhilafId.YASEEN_YAA: "fath",
    KhilafId.HAA_VERSE_HEADS: "fath",
    KhilafId.LAM_DHAT_YAA: "fath_tafkheem",
    KhilafId.LAM_VERSE_HEADS: "taqlil_tarqiq",
}

_OPENING_TEXTS = frozenset({
    "أَلَٓر۪ۖ", "أَلَٓمِّٓر۪ۖ", "كَٓه۪ي۪عَٓصَٓۖ", "طَه۪ۖ",
    "ح۪مِٓۖ", "ح۪مِٓ",
})
_STOP_SIGNS = frozenset("ۖۗۘۙۚۛۜ۩ٓ")

# `رأى` before a following-word sakin is written without either inclination
# witness in the connected Warsh source. Both qualities return at a stop.
# These are canonical/internal corpus coordinates. Their Warsh public refs are
# 6:78:2, 6:79:2, 16:85:2, 16:86:2, 18:52:1, and 33:22:2.
RAA_SEEN_BEFORE_SAKIN = frozenset({
    Location(6, 77, 2), Location(6, 78, 2),
    Location(16, 85, 2), Location(16, 86, 2),
    Location(18, 53, 1), Location(33, 22, 2),
})


def mark_sequence_family(text: str, offset: int) -> str:
    """Classify one U+06EA by its complete local sequence family."""
    if text.startswith("ا") and offset in {1, 2}:
        return "initial_alif"
    following = text[offset + 1:offset + 2]
    if following in {"ا", "ى", "ي", "ے"}:
        return "carrier"
    if following == "ٰ":
        return "dagger"
    return "special"


def is_inclination_witness(text: str, offset: int) -> bool:
    family = mark_sequence_family(text, offset)
    if family in {"carrier", "dagger"}:
        return text[offset + 1:offset + 2] != "ے"
    return family == "special" and (
        text in _OPENING_TEXTS or _is_raa_short_witness(text, offset)
    )


def _is_raa_short_witness(text: str, offset: int) -> bool:
    """The first of the two marks in the exact `رأى` sequence family."""
    before = text[:offset]
    return (
        (before.endswith("ر") or before.endswith("رّ"))
        and text[offset + 1:offset + 4] in {"ء۪ا", "أ۪ى"}
    )


def _marked_clusters(reading) -> list[list[tuple[int, int]]]:
    """Per word, each (cluster, offset) of an inclination witness mark."""
    marked: list[list[tuple[int, int]]] = [[] for _ in reading.words]
    for index, cluster in enumerate(reading.clusters):
        for mark in cluster.marks:
            if mark.role == "inclination_witness":
                marked[cluster.word].append((index, mark.offset))
    return marked


def _target_for_cluster(span, cluster: int):
    candidates = [
        draft for draft in span
        if draft.cluster == cluster and draft.nucleus.quality is Quality.A
    ]
    if not candidates:
        return None
    return next((draft for draft in candidates if draft.nucleus.sounds_long), candidates[-1])


@lru_cache(maxsize=None)
def dhat_yaa_register() -> tuple[dict, ...]:
    with open(_DATA / "inclination.json", encoding="utf-8") as handle:
        data = json.load(handle)
    return tuple(data["dhat_yaa"])


@lru_cache(maxsize=None)
def dhat_yaa_locations() -> frozenset[Location]:
    return frozenset(
        Location(*(int(part) for part in row["canonical"].split(":")))
        for row in dhat_yaa_register()
    )


def _choices(definitions, selection) -> dict[KhilafId, str]:
    resolved = {}
    for khilaf, fallback in _DEFAULTS.items():
        definition = definitions.get(khilaf)
        default = definition.default if definition is not None else fallback
        resolved[khilaf] = selection.chosen(khilaf) or default
    return resolved


def _pair_quality(name: str) -> Quality:
    return Quality.TAQLIL if name == "taqlil_tarqiq" else Quality.A


def _named_quality(name: str) -> Quality:
    return Quality.TAQLIL if name == "taqlil" else Quality.A


def _quality(location: Location, choices) -> Quality:
    if location in FIXED_KUBRA:
        return Quality.KUBRA
    if location in LAM_DHAT_YAA:
        return _pair_quality(choices[KhilafId.LAM_DHAT_YAA])
    if location in LAM_VERSE_HEADS:
        return _pair_quality(choices[KhilafId.LAM_VERSE_HEADS])
    named = NAMED_SITES.get(location)
    if named is not None:
        return _named_quality(choices[named])
    if location in dhat_yaa_locations():
        return _named_quality(choices[KhilafId.DHAT_YAA])
    return Quality.TAQLIL


def _supply_marked(
    marked, span, location: Location, scribe, choices
) -> None:
    for cluster, offset in marked:
        target = _target_for_cluster(span, cluster)
        if target is None:
            continue
        target.nucleus = target.nucleus.with_quality(_quality(location, choices))
        if target.origin is SlotOrigin.SPELLED:
            scribe.evidence(offset, target, SlotFact.VOWEL_QUALITY)


def _supply_raa_before_sakin(span, location: Location) -> None:
    """Restore both `رأى` inclinations only in the stopped state."""
    if location not in RAA_SEEN_BEFORE_SAKIN:
        return
    raa = next((draft for draft in span if draft.letter is CanonLetter.RA), None)
    hamza = next(
        (
            draft for draft in span
            if draft.letter is CanonLetter.HAMZA and draft.nucleus.sounds_long
        ),
        None,
    )
    if raa is None or hamza is None:
        raise ValueError(f"{location}: incomplete رأى before-sakin projection")
    raa.nucleus = Nucleus(
        raa.nucleus.joined,
        VowelState(raa.nucleus.stopped.form, Quality.TAQLIL),
    )
    hamza.nucleus = Nucleus(
        hamza.nucleus.joined,
        VowelState(hamza.nucleus.stopped.form, Quality.TAQLIL),
    )


def _supply_fathatan_dhat_yaa(text: str, span, location: Location, choices) -> None:
    plain = text.rstrip("".join(_STOP_SIGNS))
    if not plain.endswith("ىٗ") or location in LAM_DHAT_YAA:
        return
    if choices[KhilafId.DHAT_YAA] != "taqlil":
        return
    if not span or span[-1].origin is not SlotOrigin.NUNATION:
        return
    target = span[-2]
    if target.nucleus.quality is Quality.A:
        target.nucleus = Nucleus(
            target.nucleus.joined,
            VowelState(target.nucleus.stopped.form, Quality.TAQLIL),
        )


def _supply_lam_coupled(span, location: Location, choices) -> None:
    """The inclination half of the coupled dhat-yaa lam selector.

    Verse-head coupled sites are mark-supplied; these seven are not written
    with a witness, so the taqlil face is supplied from the register.
    """
    if location not in LAM_DHAT_YAA:
        return
    if _pair_quality(choices[KhilafId.LAM_DHAT_YAA]) is not Quality.TAQLIL:
        return
    lam_index = max(
        index for index, draft in enumerate(span)
        if draft.letter is CanonLetter.LAM
    )
    lam = span[lam_index]
    target = lam if lam.nucleus.sounds_long else next(
        (
            draft for draft in span[lam_index + 1:]
            if draft.nucleus.sounds_long and draft.nucleus.quality is Quality.A
        ),
        lam,
    )
    if location in LAM_COUPLED_WAQF_ONLY:
        target.nucleus = Nucleus(
            target.nucleus.joined,
            VowelState(target.nucleus.stopped.form, Quality.TAQLIL),
        )
    else:
        target.nucleus = target.nucleus.with_quality(Quality.TAQLIL)


def _supply_haa_verse_heads(span, location: Location, choices) -> None:
    """The taqlil face inclines the pre-haa alif together with the ending."""
    if location not in HAA_VERSE_HEADS:
        return
    if choices[KhilafId.HAA_VERSE_HEADS] != "taqlil":
        return
    for target in span:
        if target.nucleus.sounds_long and target.nucleus.quality is Quality.A:
            target.nucleus = target.nucleus.with_quality(Quality.TAQLIL)


def _supply_yaseen(span, location: Location, choices) -> None:
    if location != _YASEEN or choices[KhilafId.YASEEN_YAA] != "taqlil":
        return
    target = next(
        draft for draft in span
        if draft.letter is CanonLetter.YA and draft.nucleus.sounds_long
    )
    target.nucleus = target.nucleus.with_quality(Quality.TAQLIL)


def _collapse_final_yaa(drafts, span, scribe):
    if len(span) < 2:
        return None
    carrier, target = span[-1], span[-2]
    if not (
        carrier.letter is CanonLetter.YA
        and carrier.nucleus.is_silent
        and target.nucleus.is_short
        and target.nucleus.quality is Quality.A
    ):
        return None
    offsets = scribe.evidence_offsets(carrier, SlotFact.LETTER)
    scribe.withdraw((carrier,))
    drafts.remove(carrier)
    target.nucleus = Nucleus.long(Quality.TAQLIL)
    for offset in offsets:
        scribe.evidence(offset, target, SlotFact.VOWEL_LENGTH)
    return target


def _supply_verse_head(reading, drafts, span, word: int, location, scribe) -> None:
    if (
        location.surah not in VERSE_HEAD_SURAHS
        or word != len(reading.words) - 1
        or location in HAA_VERSE_HEADS
        or location in LAM_DHAT_YAA
        or location in LAM_VERSE_HEADS
    ):
        return
    if any(draft.nucleus.quality in {Quality.TAQLIL, Quality.KUBRA} for draft in span):
        return
    target = _collapse_final_yaa(drafts, span, scribe)
    if target is not None:
        return
    target = span[-1]
    if target.nucleus.is_long and target.nucleus.quality is Quality.A:
        target.nucleus = target.nucleus.with_quality(Quality.TAQLIL)


def _repair_naml_badal_carrier(drafts, span, location, scribe) -> None:
    """Restore Naml's plain alif before the marked medial dhat-yaa as badal.

    This exact interaction was deferred by the yaa-zawaid vertical.
    """
    if location != _NAML_YAA_ZAWAID or len(span) < 3:
        return
    vowel, carrier = span[:2]
    if not (
        vowel.letter is CanonLetter.HAMZA
        and vowel.nucleus.is_short
        and vowel.nucleus.quality is Quality.A
        and carrier.letter is CanonLetter.HAMZA
    ):
        return
    offsets = scribe.evidence_offsets(carrier, SlotFact.LETTER)
    scribe.withdraw((carrier,))
    drafts.remove(carrier)
    span.remove(carrier)
    vowel.nucleus = Nucleus.long(Quality.A)
    for offset in offsets:
        scribe.evidence(offset, vowel, SlotFact.VOWEL_LENGTH)


def supply_inclination(definitions):
    """Build the pass applying the al-Azraq profile under one selection."""

    def supply(reading, drafts, lexicon, scribe, selection) -> None:
        del lexicon
        if scribe is None:
            return
        choices = _choices(definitions, selection)
        spans = word_spans(reading, drafts)
        texts = word_texts(reading)
        marked = _marked_clusters(reading)
        for word, (location, span) in enumerate(zip(reading.words, spans)):
            if not span:
                continue
            _repair_naml_badal_carrier(drafts, span, location, scribe)
            text = texts[word]
            _supply_marked(marked[word], span, location, scribe, choices)
            _supply_lam_coupled(span, location, choices)
            _supply_haa_verse_heads(span, location, choices)
            _supply_yaseen(span, location, choices)
            _supply_raa_before_sakin(span, location)
            _supply_fathatan_dhat_yaa(text, span, location, choices)
            _supply_verse_head(reading, drafts, span, word, location, scribe)

    return supply


#: Source-coordinate occurrence rows for the named quality selectors, in the
#: same shape as the lam and raa registers.
_NAMED_SOURCES = {
    "arakahum": ((8, 44, 8),),
    "al_jar": ((4, 36, 13), (4, 36, 16)),
    "jabbarin": ((5, 24, 6), (26, 130, 4)),
    "maryam_haa_yaa": ((19, 1, 1),),
    "yaseen_yaa": ((36, 1, 1),),
    "haa_verse_heads": (
        (79, 27, 6), (79, 28, 3), (79, 29, 4), (79, 30, 4), (79, 31, 4),
        (79, 32, 2), (79, 41, 5), (79, 43, 3), (79, 44, 5), (79, 45, 9),
        (91, 1, 2), (91, 2, 3), (91, 3, 3), (91, 4, 3), (91, 5, 3),
        (91, 6, 3), (91, 7, 3), (91, 8, 3), (91, 9, 4), (91, 10, 4),
        (91, 11, 3), (91, 12, 3), (91, 13, 7), (91, 14, 7), (91, 15, 3),
    ),
}


def catalogue_registers() -> dict[str, tuple[VariantSpan, ...]]:
    """Occurrence spans per inclination selector, in source coordinates."""
    registers = {
        owner: tuple(
            VariantSpan((Location(*site),), "word", "all") for site in sites
        )
        for owner, sites in _NAMED_SOURCES.items()
    }
    registers["dhat_yaa"] = tuple(
        VariantSpan(
            (Location(*(int(part) for part in row["source"].split(":"))),),
            "word",
            row["requires"],
        )
        for row in dhat_yaa_register()
    )
    return registers


__all__ = [
    "FIXED_KUBRA",
    "HAA_OPENINGS",
    "HAA_VERSE_HEADS",
    "LAM_COUPLED_WAQF_ONLY",
    "LAM_DHAT_YAA",
    "LAM_VERSE_HEADS",
    "NAMED_SITES",
    "RAA_OPENINGS",
    "RAA_SEEN_BEFORE_SAKIN",
    "VERSE_HEAD_SURAHS",
    "catalogue_registers",
    "dhat_yaa_locations",
    "dhat_yaa_register",
    "is_inclination_witness",
    "mark_sequence_family",
    "supply_inclination",
]
