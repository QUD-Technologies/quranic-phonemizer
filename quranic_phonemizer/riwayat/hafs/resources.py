"""Hafs: where its data lives, and how its adapters are assembled.

Resources are process-local and cached by their riwayah or script key, so
multiple facades share the same immutable loaded data.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from ...canon import derive
from ...canon.ledger import EMPTY as EMPTY_LEDGER
from ...canon.ledger import Ledger, load_ledger
from ...canon.lexicon import EMPTY as EMPTY_LEXICON
from ...canon.lexicon import Lexicon, load_affixes, load_lexicon
from ...canon.spell import Muqattaat, load_muqattaat
from ...corpus import PackedCorpus, load_corpus
from ...model.address import Location, Riwayah, Script, VerseRef
from ...model.canon import Quality
from ...orthography.adapter import Reading
from ...orthography.cluster import read_verse
from ...orthography.inventory import Inventory, load_inventory
from ...stop_editions import load_overlay, with_marks
from ..khilaf import Khilaf, load_khilaf
from ..tables import RuleTables, load_rule_tables

RIWAYAH = Riwayah.HAFS

#: The scripts this riwayah is packaged for. Listed rather than taken from
#: `Script`, so a script added for another riwayah does not appear here.
SCRIPTS = (Script.UTHMANI, Script.INDOPAK)

#: How a collapsed inclined vowel reads when the `imala` extra phoneme is
#: not spent. The typed quality and rule are unchanged by the collapse.
QUALITY_FALLBACKS = {Quality.KUBRA: Quality.I}

DATA = Path(__file__).resolve().parents[2] / "data" / "riwayat" / "hafs"

#: Madinah mushaf printings whose waqf marks this riwayah packages, by the
#: hijri year of the printing. The corpus binary carries the 1405 marks; the
#: 1421 marks, which Digital Khatt writes, are an overlay and the default.
STOP_EDITIONS = ("1421", "1405")
DEFAULT_STOP_EDITION = "1421"
STOP_OVERLAY_DIR = DATA / "corpus" / "stop_editions"


@dataclass(frozen=True, slots=True)
class Adapter:
    """One script of one riwayah. The whole of its script knowledge is the
    `Inventory` it holds; the code below is shared with every other script."""

    script: Script
    inventory: Inventory

    def read(
        self, verse: VerseRef, words: tuple[tuple[Location, str], ...]
    ) -> Reading:
        return read_verse(self.inventory, verse, words)


@lru_cache(maxsize=None)
def _inventory(script: Script) -> Inventory:
    """The assembly point is where the two halves of the role contract meet.

    `orthography` cannot import `canon`, so what a derivation needs from an
    inventory is passed in here rather than looked up there.
    """
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
    return Adapter(script=script, inventory=_inventory(script))


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
    """The affixes are shared: which pronouns attach to a word, and which
    letters may stand before one, are facts about Arabic rather than about
    how this riwayah recites it."""
    path = DATA.parents[1] / "shared" / "lexicon.yaml"
    if not path.exists():
        return EMPTY_LEXICON
    affixes = load_affixes(DATA.parents[1] / "shared" / "morphology.yaml")
    return load_lexicon(path, affixes=affixes)


@lru_cache(maxsize=None)
def rule_tables() -> RuleTables:
    """Shared tajweed tables, plus whatever this riwayah overrides."""
    shared = DATA.parents[1] / "shared" / "rules.yaml"
    return load_rule_tables(shared, DATA / "rules.yaml")


@lru_cache(maxsize=None)
def khilaf() -> Khilaf:
    """Where this riwayah disagrees with itself, and by default how."""
    return load_khilaf(DATA / "khilaf.yaml")


@lru_cache(maxsize=None)
def muqattaat() -> Muqattaat:
    """Shared across riwayat: which openings are named, and what each letter is
    called, are facts about Arabic."""
    return load_muqattaat(DATA.parents[1] / "shared" / "muqattaat.yaml")


@lru_cache(maxsize=None)
def lexeme_passes() -> tuple:
    """Hafs' verse-level passes, in order.

    `canon` supplies the shared two; spelling the muqattaat needs the
    opening and letter-name tables, so it is bound here instead.
    """
    from ...canon.khilaf import apply_canonical_khilaf
    from ...canon.passes import LEXEME_PASSES
    from ...canon.spell import spell_muqattaat

    return (
        *LEXEME_PASSES,
        spell_muqattaat(muqattaat()),
        apply_canonical_khilaf(khilaf().canonical),
    )


@lru_cache(maxsize=None)
def base_corpus() -> PackedCorpus:
    """The packaged binary, carrying the 1405 waqf marks."""
    return load_corpus(DATA / "corpus" / "quran_db.bin",
                       DATA / "corpus" / "surah_info.json")


@lru_cache(maxsize=None)
def corpus(stop_edition: str = DEFAULT_STOP_EDITION) -> PackedCorpus:
    if stop_edition == "1405":
        return base_corpus()
    return with_marks(base_corpus(), load_overlay(STOP_OVERLAY_DIR / f"{stop_edition}.json"))
