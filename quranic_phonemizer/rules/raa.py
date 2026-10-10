"""Raa weight from structural predicates and riwayah-owned registers."""
from __future__ import annotations

from dataclasses import dataclass, field

from ..engine.neighbourhood import Neighbourhood
from ..engine.plan import Phase, Plan, Realize, Recolour, SoundFeature, Verdict, mint
from ..model.address import BoundaryPlan, KhilafId, Location, SlotId
from ..model.canon import CanonLetter as L
from ..model.canon import Onset, Quality, Rule, Score, SlotOrigin, VowelForm
from ..model.performance import Aspect, Occurrence, Vowel
from .khilaf import HEAVY

RaaKey = tuple[Location, int]


@dataclass(frozen=True, slots=True)
class RaaChoice:
    """One selector-owned raa site and the junction its dispute lives in."""

    khilaf: KhilafId
    junction: str
    default: str

    def active(self, stopped: bool) -> bool:
        if self.junction == "all":
            return True
        if self.junction == "waqf":
            return stopped
        return not stopped


@dataclass(frozen=True, slots=True)
class SystematicChoice:
    """The fathatan or damma consumer over otherwise-eligible raa."""

    khilaf: KhilafId
    default: str


@dataclass(frozen=True, slots=True)
class RaaProfile:
    by_owner: dict[str, frozenset[RaaKey]]
    heavy: frozenset[RaaKey]
    light: frozenset[RaaKey]
    always_heavy: frozenset[L] = frozenset()
    selected: dict[RaaKey, RaaChoice] = field(default_factory=dict)
    fathatan: SystematicChoice | None = None
    damma: SystematicChoice | None = None

    def rule(self, near: Neighbourhood, at: SlotId, plan, boundaries) -> Rule:
        slot = near.slot(at)
        word = near.word_of(at)
        assert slot is not None and word is not None
        key = _key(near, word, at)
        if key in self.heavy:
            return Rule.TAFKHEEM
        if key in self.light:
            return Rule.TARQEEQ
        stopped = boundaries.stopped_on(word)
        choice = self.selected.get(key)
        if choice is not None and choice.active(stopped):
            name = near.score.selection.chosen(choice.khilaf) or choice.default
            return Rule.TAFKHEEM if HEAVY[name] else Rule.TARQEEQ
        systematic = self._systematic(near, slot, plan, stopped)
        if systematic is not None:
            return systematic
        return (
            Rule.TAFKHEEM
            if _ordinary_is_heavy(
                near, slot, plan, boundaries, self.always_heavy
            )
            else Rule.TARQEEQ
        )

    def _systematic(self, near, slot, plan, stopped) -> Rule | None:
        owner = systematic_owner(near, slot, self)
        if owner is None:
            return None
        if stopped and plan.merged_away(slot.id, Aspect.VOWEL):
            return Rule.TARQEEQ
        name = near.score.selection.chosen(owner.khilaf) or owner.default
        if name == "heavy_wasl":
            return Rule.TARQEEQ if stopped else Rule.TAFKHEEM
        return Rule.TAFKHEEM if HEAVY[name] else Rule.TARQEEQ


@dataclass(frozen=True, slots=True)
class RaaWeight:
    profile: RaaProfile
    rule: Rule = Rule.TAFKHEEM
    phase: Phase = Phase.COLOUR
    triggers: frozenset = frozenset({L.RA})
    emits: frozenset = frozenset({Rule.TAFKHEEM, Rule.TARQEEQ})

    def look(
        self, near: Neighbourhood, plan: Plan, at: SlotId,
        boundaries: BoundaryPlan,
    ) -> Verdict | None:
        slot = near.slot(at)
        if slot is None or slot.letter is not L.RA:
            return None
        rule = self.profile.rule(near, at, plan, boundaries)
        value = rule is Rule.TAFKHEEM
        effects = []
        if not plan.merged_away(at, Aspect.CONSONANT):
            effects.append(Recolour(at, Aspect.CONSONANT, SoundFeature.EMPHATIC, value))
        if _performed_quality(slot, at, plan, near, boundaries) is Quality.A:
            effects.append(Recolour(at, Aspect.VOWEL, SoundFeature.EMPHATIC, value))
        elif (
            plan.merged_away(at, Aspect.VOWEL)
            and slot.nucleus.quality is Quality.A
        ):
            # An ibdal face folded the raa's dependent A into the following
            # carrier; the colour follows that presented long.
            following = near.after(at)
            if following is not None and plan.relengthened_long(following.id):
                effects.append(
                    Recolour(
                        following.id, Aspect.VOWEL, SoundFeature.EMPHATIC,
                        value,
                    )
                )
        if not effects:
            return None
        return Verdict(
            Occurrence(mint(rule, at), rule, (at,)),
            tuple(effects),
        )


def systematic_owner(
    near: Neighbourhood, slot, profile: RaaProfile
) -> SystematicChoice | None:
    """The fathatan or damma consumer owning this raa, from joined facts.

    Fixed and selector-owned keys are excluded, so the resolver and the
    classifier agree on ownership without consulting the boundary state.
    """
    word = near.word_of(slot.id)
    if word is None or slot.letter is not L.RA:
        return None
    key = _key(near, word, slot.id)
    if (
        key in profile.heavy
        or key in profile.light
        or key in profile.selected
    ):
        return None
    quality = slot.nucleus.joined.quality
    if quality is Quality.U:
        owner = profile.damma
    elif quality is Quality.A and _nunation_follows(near, slot):
        owner = profile.fathatan
    else:
        return None
    if owner is None or not _moving_trigger(near, slot, profile.always_heavy):
        return None
    return owner


def systematic_sites(
    score: Score, boundaries: BoundaryPlan, profile: RaaProfile
) -> tuple[tuple[str, int], ...]:
    """Every (selector id, word index) the systematic consumers own."""
    near = Neighbourhood(score, boundaries)
    sites = []
    for index, word in enumerate(score.words):
        for slot in word.slots:
            owner = systematic_owner(near, slot, profile)
            if owner is not None:
                sites.append((owner.khilaf.value, index))
    return tuple(sites)


def _nunation_follows(near: Neighbourhood, slot) -> bool:
    following = near.after(slot.id)
    return (
        following is not None
        and not near.crosses_word(slot.id)
        and following.origin is SlotOrigin.NUNATION
    )


def _key(near: Neighbourhood, word: int, at: SlotId) -> RaaKey:
    score_word = near.score.words[word]
    ordinal = sum(
        slot.letter is L.RA
        for slot in score_word.slots
        if slot.id.ordinal <= at.ordinal
    )
    return score_word.location, ordinal


def _performed_quality(slot, at, plan, near, boundaries):
    realized = next((
        effect.sound for effect in plan.effects_at(at)
        if isinstance(effect, Realize)
        and effect.aspect is Aspect.VOWEL
        and isinstance(effect.sound, Vowel)
    ), None)
    if realized is not None:
        return realized.quality
    word = near.word_of(at)
    state = slot.nucleus.stopped if boundaries.stopped_on(word) else slot.nucleus.joined
    if state.form is VowelForm.ABSENT or plan.merged_away(at, Aspect.VOWEL):
        return None
    return state.quality


def _ordinary_is_heavy(near, slot, plan, boundaries, always_heavy) -> bool:
    word = near.word_of(slot.id)
    state = (
        slot.nucleus.stopped
        if word is not None and boundaries.stopped_on(word)
        else slot.nucleus.joined
    )
    own = None if plan.merged_away(slot.id, Aspect.VOWEL) else state.quality
    if own in {Quality.I, Quality.TAQLIL, Quality.KUBRA}:
        return False
    if own is Quality.U:
        return True
    if own is Quality.A:
        following = near.after(slot.id)
        if following is not None and following.origin is SlotOrigin.NUNATION:
            return True
        return not _moving_trigger(near, slot, always_heavy)
    before = near.before(slot.id)
    if (
        before is not None
        and before.letter is L.YA
        and before.nucleus.joined.form is VowelForm.ABSENT
    ):
        return False
    if before is not None and before.onset is Onset.WASL:
        return True
    following = near.after(slot.id)
    if (
        following is not None
        and not near.crosses_word(slot.id)
        and following.letter in always_heavy
    ):
        return True
    governing = _governing(near, slot, plan)
    return governing is not None and governing.nucleus.quality in {Quality.A, Quality.U}


def _moving_trigger(near, slot, always_heavy) -> bool:
    word = near.word_of(slot.id)
    after = near.after(slot.id)
    while after is not None and near.word_of(after.id) == word:
        if after.letter in always_heavy:
            return False
        after = near.after(after.id)
    before = near.before(slot.id)
    if before is None or near.word_of(before.id) != word:
        return False
    if before.letter is L.YA and before.nucleus.joined.form is VowelForm.ABSENT:
        return True
    if before.nucleus.quality is Quality.I and before.onset is not Onset.WASL:
        return True
    trigger = near.before(before.id)
    return (
        trigger is not None
        and near.word_of(trigger.id) == word
        and before.nucleus.joined.form is VowelForm.ABSENT
        and (before.letter not in always_heavy or before.letter is L.KHA)
        and trigger.nucleus.quality is Quality.I
        and trigger.onset is not Onset.WASL
    )


def _governing(near, slot, plan):
    before = near.before(slot.id)
    for _ in range(3):
        if before is None:
            return None
        if (
            before.nucleus.joined.form is not VowelForm.ABSENT
            and not plan.merged_away(before.id, Aspect.VOWEL)
        ):
            return before
        before = near.before(before.id)
    return None


__all__ = [
    "RaaChoice",
    "RaaKey",
    "RaaProfile",
    "RaaWeight",
    "SystematicChoice",
    "systematic_owner",
    "systematic_sites",
]
