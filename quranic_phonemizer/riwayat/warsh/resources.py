"""Warsh through al-Azraq: corpus, adapter, and shared package resources."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from ...canon import derive
from ...canon.ledger import EMPTY as EMPTY_LEDGER
from ...canon.ledger import Ledger, load_ledger
from ...canon.lexicon import Lexicon, load_affixes, load_lexicon
from ...canon.passes import LEXEME_PASSES
from ...canon.spell import Muqattaat, load_muqattaat, spell_muqattaat
from ...corpus import AlignedCorpus, load_aligned_corpus
from ...model.address import Location, Riwayah, Script, VerseRef
from ...model.canon import Quality
from ...orthography.adapter import Reading
from ...orthography.cluster import read_verse
from ...orthography.inventory import Inventory, load_inventory
from ..khilaf import Khilaf, load_khilaf
from ..tables import RuleTables, load_rule_tables
from .hamza_meetings import supply_hamza_meetings
from .inclination import supply_inclination
from .joined_pausal import supply_joined_pausal
from .relative_pronoun import supply_relative_pronoun
from .sequence import entries_for_words
from .single_hamza import supply_single_hamza

RIWAYAH = Riwayah.WARSH
SCRIPTS = (Script.UTHMANI,)

#: Warsh collapses kubra to taqlil when the `imala` extra phoneme is not
#: spent. The separate `taqlil_short` control is handled by the renderer and
#: never changes this canonical quality mapping.
QUALITY_FALLBACKS = {Quality.KUBRA: Quality.TAQLIL}
ARTIFACT = "king-fahd-warsh-v2"
DATA = Path(__file__).resolve().parents[2] / "data" / "riwayat" / "warsh"


@dataclass(frozen=True, slots=True)
class Adapter:
    script: Script
    inventory: Inventory
    corpus: AlignedCorpus

    def read(
        self, verse: VerseRef, words: tuple[tuple[Location, str], ...]
    ) -> Reading:
        prepared = iter(
            entries_for_words(
                self.inventory, tuple(text for _, text in words)
            )
        )
        return read_verse(
            self.inventory,
            verse,
            words,
            entries_for=lambda text: next(prepared),
            sources_for=self.corpus.sources_for,
        )


#: Warsh packages the one edition its source writes; it has no alternative.
STOP_EDITIONS: tuple[str, ...] = ()
DEFAULT_STOP_EDITION = None


@lru_cache(maxsize=None)
def corpus(stop_edition: str | None = None) -> AlignedCorpus:
    return load_aligned_corpus(
        DATA / "corpus" / "alignment.jsonl.gz", artifact=ARTIFACT
    )


@lru_cache(maxsize=None)
def _inventory(script: Script) -> Inventory:
    return load_inventory(
        DATA / "scripts" / f"{script.value}.yaml",
        riwayah=RIWAYAH,
        script=script,
        derivations=frozenset(derive.registered()),
        roles=derive.required_roles(),
    )


def script_adapter(script: Script) -> Adapter:
    if script not in SCRIPTS:
        raise ValueError(f"{RIWAYAH.value} is not packaged for {script.value}")
    return Adapter(script, _inventory(script), corpus())


def adapters_for(riwayah: Riwayah) -> dict[Script, Adapter]:
    if riwayah is not RIWAYAH:
        raise ValueError(f"{__name__} assembles {RIWAYAH.value}, not {riwayah.value}")
    return {script: script_adapter(script) for script in SCRIPTS}


@lru_cache(maxsize=None)
def ledger() -> Ledger:
    path = DATA / "ledger.yaml"
    return load_ledger(path, riwayah=RIWAYAH) if path.exists() else EMPTY_LEDGER


@lru_cache(maxsize=None)
def lexicon() -> Lexicon:
    path = DATA.parents[1] / "shared" / "lexicon.yaml"
    affixes = load_affixes(DATA.parents[1] / "shared" / "morphology.yaml")
    return load_lexicon(path, affixes=affixes)


@lru_cache(maxsize=None)
def rule_tables() -> RuleTables:
    return load_rule_tables(
        DATA.parents[1] / "shared" / "rules.yaml", DATA / "rules.yaml"
    )


@lru_cache(maxsize=None)
def khilaf() -> Khilaf:
    from dataclasses import replace

    from . import article_start, hamza_meetings, inclination, lam, raa
    from . import single_hamza as single_hamza_module

    loaded = load_khilaf(
        DATA / "khilaf.yaml",
        registers={
            **raa.catalogue_registers(),
            **lam.catalogue_registers(),
            **inclination.catalogue_registers(),
            **hamza_meetings.catalogue_registers(),
            **single_hamza_module.catalogue_registers(),
        },
    )
    return replace(
        loaded,
        dynamic_sites={
            **raa.dynamic_sites(raa.selector_profile(loaded.variants)),
            **lam.dynamic_sites(lam.selector_profile(loaded.variants)),
            **article_start.dynamic_sites(loaded.variants),
        },
    )


@lru_cache(maxsize=None)
def muqattaat() -> Muqattaat:
    return load_muqattaat(DATA.parents[1] / "shared" / "muqattaat.yaml")


@lru_cache(maxsize=None)
def lexeme_passes() -> tuple:
    from ...canon.khilaf import apply_canonical_khilaf

    return (
        *LEXEME_PASSES,
        supply_relative_pronoun,
        supply_single_hamza(khilaf().variants),
        supply_hamza_meetings,
        supply_joined_pausal,
        spell_muqattaat(muqattaat(), vocalized_compact=True),
        supply_inclination(khilaf().variants),
        apply_canonical_khilaf(khilaf().canonical),
    )


__all__ = [
    "ARTIFACT",
    "RIWAYAH",
    "SCRIPTS",
    "adapters_for",
    "corpus",
    "khilaf",
    "ledger",
    "lexeme_passes",
    "lexicon",
    "muqattaat",
    "rule_tables",
    "script_adapter",
]
