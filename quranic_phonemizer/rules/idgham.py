"""The idgham families that are not the noon's: like into like, near into near.

Only cross-boundary assimilation. A geminate written in the rasm is canonical
and needs no rule.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..engine.neighbourhood import Neighbourhood
from ..engine.plan import Classify, MergeInto, Phase, Plan, Realize, Verdict, mint
from ..model.address import BoundaryPlan, SlotId
from ..model.canon import CanonLetter, Rule, SlotOrigin
from ..model.canon import CanonLetter as L
from ..model.performance import Aspect, Consonant, Occurrence
from .lam_shamsiyyah import ArticleShape
from .meem_sakinah import NASAL_LETTERS
from .tables import PAIR_OUTCOMES, Pairs


@dataclass(frozen=True, slots=True)
class Idgham:
    """One classifier over the pair table; which family a pair falls in is
    data, so a per-family `look` would be the same body three times."""

    pairs: Pairs
    never_follows: frozenset[CanonLetter] = frozenset()
    article: ArticleShape = field(default_factory=ArticleShape)
    choices: tuple[object, ...] = ()
    stems: frozenset[tuple[CanonLetter, CanonLetter, CanonLetter]] = frozenset()
    """`(previous, first, second)`: a pair named here assimilates only where
    `previous` stands before its first letter in the same word, as Warsh
    merges the dhal of `أَخَذتُّمْ` but not of `نَبَذْتُهَا`."""
    rule: Rule = Rule.IDGHAM_MUTAMATHILAYN
    phase: Phase = Phase.MERGE
    triggers: frozenset = field(default=frozenset())
    emits: frozenset = PAIR_OUTCOMES | {Rule.IDGHAM_MUTAMATHILAYN}

    def __post_init__(self) -> None:
        # Like into like fires on any repeated letter, including the nasal
        # pairs that also receive their dedicated family classification.
        object.__setattr__(
            self,
            "triggers",
            frozenset(set(CanonLetter) - self.never_follows),
        )

    def look(
        self, near: Neighbourhood, plan: Plan, at: SlotId,
        boundaries: BoundaryPlan,
    ) -> Verdict | None:
        del boundaries
        here = near.slot(at)
        if here is None or not here.nucleus.is_silent:
            return None
        word = near.word_of(at)
        if word is not None:
            location = near.score.words[word].location
            choice = next(
                (item for item in self.choices if location in item.locations),
                None,
            )
            if choice is not None and choice.choose(near.score.selection) == "izhar":
                return None
        if self.article(near, at):
            return None  # lam shamsiyyah owns this slot
        following = near.after(at)
        if following is None:
            return None

        if here.letter is following.letter:
            rule = Rule.IDGHAM_MUTAMATHILAYN
        else:
            rule = self.pairs.of(here.letter, following.letter)
            if rule is None or not self._in_stem(near, at, following.letter):
                return None

        if here.letter in NASAL_LETTERS and here.letter is following.letter:
            if (
                here.origin is SlotOrigin.SPELLED
                and following.origin is SlotOrigin.SPELLED
            ):
                return None
            owner = (
                Rule.IDGHAM_BI_GHUNNAH
                if here.letter is L.NOON
                else Rule.IDGHAM_SHAFAWI
            )
            if not plan.removed_by(at, Aspect.CONSONANT, owner):
                return None
            return Verdict(
                Occurrence(mint(rule, at), rule, (at, following.id)),
                (Classify(following.id, Aspect.CONSONANT),),
            )

        if rule is Rule.IDGHAM_MUTAJANISAYN_NAQIS:
            # The first letter survives as a colour on the second, so nothing
            # merges. Both letters are the rule's own: it names a pair, and a
            # projection that shows one half of it shows nothing.
            return Verdict(
                Occurrence(mint(rule, at), rule, (at, following.id)), ()
            )
        return Verdict(
            Occurrence(mint(rule, at), rule, (at,)),
            (
                Realize(
                    following.id,
                    Aspect.CONSONANT,
                    Consonant(
                        following.letter,
                        geminate=True,
                        # A doubled noon or meem is held on its ghunnah
                        # wherever it stands, and one the idgham doubled is
                        # no different: the meem of `ٱرْكَب مَّعَنَا` hums,
                        # exactly as `GhunnahMushaddadah` would have made it
                        # had the rasm written the shadda for itself.
                        ghunnah=following.letter in NASAL_LETTERS,
                    ),
                ),
                MergeInto(at, Aspect.CONSONANT, following.id, Aspect.CONSONANT),
            ),
        )

    def _in_stem(
        self, near: Neighbourhood, at: SlotId, second: CanonLetter
    ) -> bool:
        here = near.slot(at)
        required = {
            previous for previous, first, following in self.stems
            if first is here.letter and following is second
        }
        if not required:
            return True
        previous = near.before(at)
        return (
            previous is not None
            and previous.letter in required
            and near.word_of(previous.id) == near.word_of(at)
        )
