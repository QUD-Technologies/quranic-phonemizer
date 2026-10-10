"""Classifiers for facts already decided on the Slot: imala, tashil and
ishmam. Each gets a named occurrence so a projection can find it; none of
them emits an effect on the sound.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..engine.neighbourhood import Neighbourhood
from ..engine.plan import (
    Classify,
    Phase,
    Plan,
    Realize,
    Recolour,
    Relength,
    Verdict,
    mint,
)
from ..model.address import BoundaryPlan, SlotId
from ..model.canon import Annotation, Onset, Quality, Rule, VowelForm
from ..model.canon import CanonLetter as L
from ..model.performance import Aspect, Length, Occurrence, Vowel
from .tafkheem import Weight


def _classification(rule: Rule, at: SlotId) -> Verdict:
    return Verdict(Occurrence(mint(rule, at), rule, (at,)), ())


@dataclass(frozen=True, slots=True)
class Inclination:
    """Classify the effective sounded taqlil or kubra quality."""

    rule: Rule = Rule.TAQLIL
    phase: Phase = Phase.COLOUR
    emits: frozenset = frozenset({Rule.TAQLIL, Rule.IMALA})
    triggers: frozenset = frozenset({VowelForm.SHORT, VowelForm.LONG})

    def look(
        self, near: Neighbourhood, plan: Plan, at: SlotId,
        boundaries: BoundaryPlan,
    ) -> Verdict | None:
        slot, word = near.slot(at), near.word_of(at)
        if slot is None or word is None or plan.merged_away(at, Aspect.VOWEL):
            return None
        state = (
            slot.nucleus.stopped
            if boundaries.stopped_on(word)
            else slot.nucleus.joined
        )
        rule = {
            Quality.TAQLIL: Rule.TAQLIL,
            Quality.KUBRA: Rule.IMALA,
        }.get(state.quality)
        if rule is None:
            return None
        realized = next(
            (
                effect.sound for effect in plan.effects_at(at)
                if isinstance(effect, Realize)
                and effect.aspect is Aspect.VOWEL
            ),
            None,
        )
        if isinstance(realized, Vowel) and realized.quality is not state.quality:
            return None
        return _classification(rule, at)


@dataclass(frozen=True, slots=True)
class CanonicalColour:
    """Imala, tashil and ishmam in one classifier: each is a quality or
    onset the slot already carries, so the same lookup finds all three.
    """

    rule: Rule = Rule.IMALA
    phase: Phase = Phase.COLOUR
    emits: frozenset = frozenset({Rule.IMALA, Rule.TASHIL, Rule.ISHMAM})
    triggers: frozenset = frozenset(
        {Annotation.IMALA, Annotation.ISHMAM, Onset.TASHIL}
    )

    def look(
        self, near: Neighbourhood, plan: Plan, at: SlotId,
        boundaries: BoundaryPlan,
    ) -> Verdict | None:
        del boundaries
        slot = near.slot(at)
        if slot is None:
            return None
        if slot.onset is Onset.TASHIL:
            realized = plan.realized_consonant(at)
            if realized is not None and not realized.eased:
                # An ibdal face replaced the eased onset with a consonant.
                return None
            if plan.removed_by(at, Aspect.CONSONANT, Rule.IBDAL_HAMZA):
                # An ibdal face folded the eased onset into a long.
                return None
            return _classification(Rule.TASHIL, at)
        if Annotation.IMALA in slot.annotations:
            return _classification(Rule.IMALA, at)
        if Annotation.ISHMAM in slot.annotations:
            following = near.after(at)
            if following is not None and following.letter is L.NOON:
                return _classification(Rule.ISHMAM, following.id)
            return _classification(Rule.ISHMAM, at)
        return None


@dataclass(frozen=True, slots=True)
class Tarqeeq:
    """Every pronounced raa and lam has explicit light/heavy identity."""

    weight: Weight = field(default_factory=Weight)
    rule: Rule = Rule.TARQEEQ
    phase: Phase = Phase.COLOUR
    triggers: frozenset = field(default=frozenset({L.RA, L.LAM}))
    emits: frozenset = frozenset({Rule.TARQEEQ})

    def look(
        self, near: Neighbourhood, plan: Plan, at: SlotId,
        boundaries: BoundaryPlan,
    ) -> Verdict | None:
        slot = near.slot(at)
        if slot is None or slot.letter not in {L.RA, L.LAM}:
            return None
        if plan.merged_away(at, Aspect.CONSONANT):
            return None
        if self.weight.is_heavy(near, slot, plan, boundaries):
            return None
        return _classification(Rule.TARQEEQ, at)


@dataclass(frozen=True, slots=True)
class CarrierTarqeeq:
    """Name a light long-A carrier when no letter-weight rule already does."""

    rule: Rule = Rule.TARQEEQ
    phase: Phase = Phase.COLOUR
    # Madd iwad starts short; joined ibdal realizes a canonically absent qata
    # nucleus. Both become long A before COLOUR and need the same identity.
    triggers: frozenset = frozenset(
        {VowelForm.ABSENT, VowelForm.SHORT, VowelForm.LONG}
    )
    emits: frozenset = frozenset({Rule.TARQEEQ})

    @staticmethod
    def _performed_a_is_long(plan: Plan, at: SlotId, state) -> bool:
        """Return whether final performance realizes a long A.

        Carrier identity follows final performance, not canonical shape.
        """
        quality = state.quality
        long = state.form is VowelForm.LONG
        for effect in plan.effects_at(at):
            if (
                isinstance(effect, Realize)
                and effect.aspect is Aspect.VOWEL
                and isinstance(effect.sound, Vowel)
            ):
                quality = effect.sound.quality
                long = effect.sound.long
            elif isinstance(effect, Relength):
                long = effect.length is Length.LONG
        return quality is Quality.A and long

    def look(
        self, near: Neighbourhood, plan: Plan, at: SlotId,
        boundaries: BoundaryPlan,
    ) -> Verdict | None:
        slot, word = near.slot(at), near.word_of(at)
        if slot is None or word is None:
            return None
        state = (
            slot.nucleus.stopped
            if boundaries.stopped_on(word)
            else slot.nucleus.joined
        )
        if (
            not self._performed_a_is_long(plan, at, state)
            or plan.merged_away(at, Aspect.VOWEL)
        ):
            return None
        if any(
            verdict.occurrence.rule in {Rule.TAFKHEEM, Rule.TARQEEQ}
            and any(
                isinstance(effect, (Classify, Recolour))
                and effect.slot == at
                and effect.aspect is Aspect.VOWEL
                for effect in verdict.effects
            )
            for verdict in plan.verdicts_at(at)
        ):
            return None
        occurrence = Occurrence(
            mint(Rule.TARQEEQ, at, variant=1), Rule.TARQEEQ, (at,)
        )
        return Verdict(occurrence, (Classify(at, Aspect.VOWEL),))


__all__ = ["CanonicalColour", "CarrierTarqeeq", "Inclination", "Tarqeeq"]
