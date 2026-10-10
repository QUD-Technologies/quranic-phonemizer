"""Effects, the Plan that accumulates them, and conflict detection.

A rule affects a neighbour only by declaring an effect naming it, never by
writing to it directly -- there is no shared mutable structure to corrupt.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TypeAlias

from ..model.address import OccurrenceId, SlotId
from ..model.canon import Rule
from ..model.inscription import SilenceReason
from ..model.performance import Aspect, Length, Occurrence, Side, Sound, Vowel


class Phase(StrEnum):
    """Closed and ordered. Within a phase, rules are unordered and
    conflicts are errors."""

    BOUNDARY = "boundary"
    MERGE = "merge"
    LENGTH = "length"
    COLOUR = "colour"
    RELEASE = "release"


class SoundFeature(StrEnum):
    EMPHATIC = "emphatic"


@dataclass(frozen=True, slots=True)
class Realize:
    slot: SlotId
    aspect: Aspect
    sound: Sound


@dataclass(frozen=True, slots=True)
class MergeInto:
    slot: SlotId
    aspect: Aspect
    host: SlotId
    host_aspect: Aspect


@dataclass(frozen=True, slots=True)
class Silence:
    """Removes a slot's sound. The occurrence's own rule is the reason;
    there is no separate reason field."""

    slot: SlotId
    aspect: Aspect


@dataclass(frozen=True, slots=True)
class Insert:
    anchor: tuple[SlotId, Side]
    aspect: Aspect
    sound: Sound


@dataclass(frozen=True, slots=True)
class Recolour:
    """Sets one named feature rather than a single boolean, since the
    COLOUR phase decides more than one feature per sound."""

    slot: SlotId
    aspect: Aspect
    feature: SoundFeature
    value: bool


@dataclass(frozen=True, slots=True)
class Relength:
    """Nucleus-only by definition, and keyed on `(SlotId, NUCLEUS)`."""

    slot: SlotId
    length: Length


@dataclass(frozen=True, slots=True)
class Classify:
    """Attach an occurrence to an existing sound of the named aspect."""

    slot: SlotId
    aspect: Aspect


Effect: TypeAlias = (
    Realize | MergeInto | Silence | Insert | Recolour | Relength | Classify
)


@dataclass(frozen=True, slots=True)
class Verdict:
    occurrence: Occurrence
    effects: tuple[Effect, ...]


def conflict_key(effect: Effect) -> tuple:
    """The (target, aspect) an effect claims, for conflict detection.

    `Relength` always keys on NUCLEUS, its only aspect; `Insert` keys on its
    anchor and side instead of a slot and aspect.
    """
    match effect:
        case Relength(slot=slot):
            return (slot, Aspect.VOWEL)
        case Insert(anchor=(slot, side)):
            return (slot, side)
        case _:
            return (effect.slot, effect.aspect)


#: Spaces ordinals by rule, so two rules firing on the same slot mint
#: distinct occurrence ids.
_RULE_SLOT_STRIDE = 1_000_000

#: Separates two classifiers that legitimately declare the same `Rule` on
#: the same slot (different aspects) -- rule plus slot alone is not unique.
_VARIANT_STRIDE = 100_000_000
_RULE_INDEX: dict[Rule | SilenceReason, int] = {
    rule: index for index, rule in enumerate(Rule)
}
_RULE_INDEX.update(
    {reason: len(Rule) + i for i, reason in enumerate(SilenceReason)}
)


def mint(rule: Rule | SilenceReason, at: SlotId, variant: int = 0) -> OccurrenceId:
    """Mint a stable occurrence id from rule, slot, and variant.

    `variant` is a small integer, not the classifier's identity -- ids must
    stay stable across runs.
    """
    ordinal = (
        variant * _VARIANT_STRIDE
        + _RULE_INDEX[rule] * _RULE_SLOT_STRIDE
        + at.ordinal
    )
    return OccurrenceId(at.verse, ordinal)


class ConflictError(ValueError):
    """Names both occurrence tags and both rules. Never last-writer-wins."""


@dataclass(slots=True)
class Plan:
    """Append-only journal: keyed for conflict detection, ordered for replay."""

    entries: list[tuple[Phase, Verdict]] = field(default_factory=list)
    _keys: dict[tuple[Phase, tuple], tuple[OccurrenceId, Rule]] = field(
        default_factory=dict
    )
    _removed: set[tuple[SlotId, Aspect]] = field(default_factory=set)
    _voweled: set[SlotId] = field(default_factory=set)
    _lengthened: set[SlotId] = field(default_factory=set)
    _at: dict[SlotId, list[Verdict]] = field(default_factory=dict)

    def record(self, phase: Phase, verdict: Verdict) -> None:
        for effect in verdict.effects:
            if isinstance(effect, Classify):
                continue
            key = (phase, conflict_key(effect))
            existing = self._keys.get(key)
            if existing is not None:
                if isinstance(effect, MergeInto) and any(
                    recorded_phase is phase and effect in recorded.effects
                    for recorded_phase, recorded in self.entries
                ):
                    continue
                raise ConflictError(
                    f"{phase.value}: two effects on {key[1]} — "
                    f"{existing[1].value} ({existing[0]}) and "
                    f"{verdict.occurrence.rule.value} ({verdict.occurrence.id}). "
                    f"Exactly one rule of a family fires per trigger; this is a "
                    f"found bug, not a precedence question."
                )
            self._keys[key] = (verdict.occurrence.id, verdict.occurrence.rule)
            if isinstance(effect, (MergeInto, Silence)):
                self._removed.add((effect.slot, effect.aspect))
                if (
                    isinstance(effect, MergeInto)
                    and effect.aspect is Aspect.VOWEL
                ):
                    # A vowel merger can make a canonically silent presenter
                    # voweled without making it the shared sound's owner.
                    self._voweled.add(effect.slot)
            elif isinstance(effect, Realize) and effect.aspect is Aspect.VOWEL:
                self._voweled.add(effect.slot)
            elif isinstance(effect, Relength) and effect.length is Length.LONG:
                self._lengthened.add(effect.slot)
        self.entries.append((phase, verdict))
        for slot in dict.fromkeys(
            effect.slot for effect in verdict.effects
            if not isinstance(effect, Insert)
        ):
            self._at.setdefault(slot, []).append(verdict)

    def effects(self, phase: Phase | None = None):
        for recorded_phase, verdict in self.entries:
            if phase is None or recorded_phase is phase:
                yield from verdict.effects

    def verdicts_at(self, slot: SlotId) -> list[Verdict]:
        """Recorded verdicts with an effect naming this slot, in record order."""
        return self._at.get(slot, [])

    def effects_at(self, slot: SlotId):
        """Effects naming this slot, in record order."""
        for verdict in self.verdicts_at(slot):
            for effect in verdict.effects:
                if not isinstance(effect, Insert) and effect.slot == slot:
                    yield effect

    def merged_away(self, slot: SlotId, aspect: Aspect) -> bool:
        return (slot, aspect) in self._removed

    def removed_by(self, slot: SlotId, aspect: Aspect, rule: Rule) -> bool:
        """Whether one named rule removed this aspect in an earlier phase."""
        return any(
            verdict.occurrence.rule is rule
            and any(
                isinstance(effect, (MergeInto, Silence))
                and effect.slot == slot
                and effect.aspect is aspect
                for effect in verdict.effects
            )
            for verdict in self.verdicts_at(slot)
        )

    def realized_consonant(self, slot: SlotId):
        """The consonant an earlier phase realized on this slot, if any."""
        found = None
        for effect in self.effects_at(slot):
            if (
                isinstance(effect, Realize)
                and effect.aspect is Aspect.CONSONANT
            ):
                found = effect.sound
        return found

    def voweled(self, slot: SlotId) -> bool:
        """Has an earlier phase given this slot a vowel it did not have?

        A rule that asks the Score alone still reads a repaired sakin as sakin.
        """
        return slot in self._voweled

    def relengthened_long(self, slot: SlotId) -> bool:
        """Has an earlier phase drawn this slot's vowel out to a long one
        the Score does not carry?"""
        return slot in self._lengthened

    def hamza_meeting_length(self, slot: SlotId) -> bool:
        """Whether ibdal fused the preceding qata vowel into this carrier."""
        previous = SlotId(slot.verse, slot.ordinal - 1)
        return any(
            verdict.occurrence.rule is Rule.IBDAL_HAMZA
            and Relength(slot, Length.LONG) in verdict.effects
            and MergeInto(
                previous, Aspect.VOWEL, slot, Aspect.VOWEL
            ) in verdict.effects
            for verdict in self.verdicts_at(slot)
        )

    def joined_ibdal_length(self, slot: SlotId) -> bool:
        """Whether connected ibdal made this root hamza a long-vowel host."""
        return any(
            verdict.occurrence.rule is Rule.IBDAL_HAMZA
            and any(
                isinstance(effect, Realize)
                and effect.slot == slot
                and effect.aspect is Aspect.VOWEL
                and isinstance(effect.sound, Vowel)
                and effect.sound.long
                for effect in verdict.effects
            )
            and any(
                isinstance(effect, MergeInto)
                and effect.host == slot
                and effect.host_aspect is Aspect.VOWEL
                for effect in verdict.effects
            )
            for verdict in self.verdicts_at(slot)
        )
