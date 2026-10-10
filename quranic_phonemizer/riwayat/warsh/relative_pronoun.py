"""Canonical projection for Warsh relative-pronoun spellings."""

from __future__ import annotations

import unicodedata

from ...canon.passes import word_spans, word_texts
from ...model.canon import CanonLetter, Nucleus, Onset, Quality
from ...model.inscription import SlotFact

_IGNORED = frozenset("ـۥۦۧۨ")
_FORMS = {
    CanonLetter.THAL: frozenset({
        "الذين",
        "الذے",
        "الذن",
        "والذن",
        "والذين",
        "والذے",
        "بالذين",
        "بالذے",
        "فالذين",
        "كالذين",
        "كالذے",
        "للذين",
        "للذے",
        "وبالذے",
        "وللذين",
    }),
    CanonLetter.TA: frozenset({
        "التے",
        "بالتے",
        "والتے",
        "كالتے",
        "للتے",
    }),
}
_ALL_FORMS = frozenset().union(*_FORMS.values())


def _skeleton(text: str) -> str:
    return "".join(
        char
        for char in text
        if not unicodedata.combining(char) and char not in _IGNORED
    )


def relative_pronoun_form(text: str) -> bool:
    """Whether the selected token is one reviewed relative-pronoun form."""
    return _skeleton(text) in _ALL_FORMS


def supply_relative_pronoun(reading, drafts, lexicon, scribe, selection) -> None:
    """Restore the pronounced geminate lam omitted by the selected script."""
    del lexicon, selection
    texts = word_texts(reading)
    for word, span in enumerate(word_spans(reading, drafts)):
        skeleton = _skeleton(texts[word])
        following_letter = next(
            (letter for letter, forms in _FORMS.items() if skeleton in forms),
            None,
        )
        if following_letter is None:
            continue
        lam = next(
            current
            for current, following in zip(span, span[1:])
            if current.letter is CanonLetter.LAM
            and following.letter is following_letter
        )
        lam.onset = Onset.GEMINATE
        lam.onset_declared = True
        lam.nucleus = Nucleus.short(Quality.A)
        lam.nucleus_declared = True
        offset = scribe.evidence_offsets(lam, SlotFact.LETTER)[0]
        scribe.evidence(offset, lam, SlotFact.ONSET)
        scribe.evidence(offset, lam, SlotFact.VOWEL_QUALITY)


__all__ = ["relative_pronoun_form", "supply_relative_pronoun"]
