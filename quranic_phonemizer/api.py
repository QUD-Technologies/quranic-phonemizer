"""The composition root: one riwayah, assembled, and the calls it answers.

Nothing here decides anything. It exists so that a caller states a riwayah
once instead of gathering its adapters, data and rules by hand.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .canon.build import Built, Provenance, build
from .canon.ledger import Ledger
from .canon.lexicon import Lexicon
from .canon.passes import LexemePass
from .canon.spell import Muqattaat
from .corpus import Corpus
from .engine.classifier import RuleSet
from .engine.run import perform
from .model.address import (
    BoundaryPlan,
    Location,
    Riwayah,
    Script,
    UnknownRiwayah,
    VariantSelection,
    VerseRef,
)
from .model.canon import Score
from .model.performance import Performance
from .orthography.adapter import Reading, ScriptAdapter
from .orthography.inventory import Inventory
from .render.alphabet import Alphabet, load_alphabet
from .riwayat import PACKAGES, ruleset_for
from .riwayat.khilaf import Khilaf
from .stop_editions import UnknownStopEdition

DATA = Path(__file__).resolve().parent / "data"


@dataclass(frozen=True, slots=True)
class Recitation:
    """One riwayah's scripts, data and rules, already loaded."""

    riwayah: Riwayah
    scripts: tuple[Script, ...]
    rules: RuleSet
    corpus: Corpus
    khilaf: Khilaf
    muqattaat: Muqattaat
    lexicon: Lexicon
    ledger: Ledger
    passes: tuple[LexemePass, ...]
    adapters: dict[Script, ScriptAdapter]
    quality_fallbacks: dict

    def read(
        self,
        script: Script,
        verse: VerseRef,
        words: tuple[tuple[Location, str], ...],
    ) -> Reading:
        if script not in self.adapters:
            raise UnknownRiwayah(
                f"{self.riwayah.value} is packaged for "
                f"{[s.value for s in self.scripts]}, not {script.value}"
            )
        return self.adapters[script].read(verse, words)

    def inventory(self, script: Script) -> Inventory:
        return self.adapters[script].inventory

    def build(
        self,
        reading: Reading,
        *,
        selection: VariantSelection = VariantSelection(),
        right_context: Reading | None = None,
        provenance: Provenance | None = None,
    ) -> Built:
        self.khilaf.validate(selection)
        return build(
            reading,
            lexicon=self.lexicon,
            ledger=self.ledger,
            passes=self.passes,
            selection=selection,
            right_context=right_context,
            provenance=provenance,
        )

    def perform(
        self,
        score: Score,
        boundaries: BoundaryPlan,
        *,
        selection: VariantSelection = VariantSelection(),
    ) -> Performance:
        return perform(score, self.rules, boundaries, selection=selection)

    def words(self, verse: VerseRef) -> tuple[tuple[Location, str], ...]:
        """The words at one internal canonical verse address."""
        return self.corpus.words(verse)


def recitation(riwayah: Riwayah, stop_edition: str | None = None) -> Recitation:
    """Load everything one riwayah needs. One call, one process-local copy.

    `stop_edition` selects which mushaf printing's waqf marks the corpus
    carries; None is the riwayah's default."""
    package = PACKAGES.get(riwayah)
    if package is None:
        raise UnknownRiwayah(
            f"{riwayah.value} is not packaged; this build ships "
            f"{[r.value for r in PACKAGES]}"
        )
    edition = stop_edition or package.DEFAULT_STOP_EDITION
    if stop_edition is not None and stop_edition not in package.STOP_EDITIONS:
        raise UnknownStopEdition(
            f"{stop_edition!r} is not a stop edition of {riwayah.value}; "
            f"available: {list(package.STOP_EDITIONS)}"
        )
    return Recitation(
        riwayah=package.RIWAYAH,
        scripts=package.SCRIPTS,
        rules=package.rules_for(riwayah),
        corpus=package.corpus(edition),
        khilaf=package.khilaf(),
        muqattaat=package.muqattaat(),
        lexicon=package.lexicon(),
        ledger=package.ledger(),
        passes=package.lexeme_passes(),
        adapters=package.adapters_for(riwayah),
        quality_fallbacks=package.QUALITY_FALLBACKS,
    )


@lru_cache(maxsize=None)
def alphabet(notation: str = "ipa") -> Alphabet:
    """The output notation. Shared across riwayat: it names sounds, not
    readings, so it is not part of a `Recitation`."""
    return load_alphabet(DATA / "render" / f"{notation}.yaml")


__all__ = ["PACKAGES", "Recitation", "alphabet", "recitation", "ruleset_for"]
