"""Mushaf editions that differ only in their waqf marks.

A corpus is packaged with one edition's marks. Another edition is an overlay:
for each word whose trailing mark differs, the mark that edition writes there,
or an empty string where it writes none. The words themselves never change.
"""
from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path

from .corpus import PackedCorpus

#: The waqf marks a word may end with: U+06D6 to U+06DB. The small high seen
#: (U+06DC) is a sakt or spelling sign written inside words, not a waqf mark.
STOP_MARKS = "ۖۗۘۙۚۛ"
_TRAILING = re.compile(f"\\s*[{STOP_MARKS}]\\s*$")


class UnknownStopEdition(ValueError):
    """A mushaf edition the selected riwayah does not package."""


def trailing_mark(text: str) -> str:
    match = _TRAILING.search(text)
    return match.group().strip() if match else ""


def remark(text: str, mark: str) -> str:
    """The word with its trailing waqf mark replaced, written as the packaged
    corpus writes one: after a space."""
    bare = _TRAILING.sub("", text)
    return f"{bare} {mark}" if mark else bare


def load_overlay(path: Path) -> dict[str, str]:
    with path.open(encoding="utf-8") as fh:
        overlay = json.load(fh)
    for ref, mark in overlay.items():
        if mark and (len(mark) != 1 or mark not in STOP_MARKS):
            raise ValueError(f"{path.name}: {ref} carries {mark!r}, not a waqf mark")
    return overlay


def with_marks(corpus: PackedCorpus, overlay: Mapping[str, str]) -> PackedCorpus:
    """The same corpus with each overlaid word's trailing mark replaced."""
    texts = list(corpus.texts)
    indices = list(corpus.word_indices)
    for ref, mark in overlay.items():
        surah, ayah, word = map(int, ref.split(":"))
        slot = corpus.verse_starts[(surah, ayah)] + word - 1
        texts.append(remark(texts[indices[slot]], mark))
        indices[slot] = len(texts) - 1
    return replace(corpus, texts=tuple(texts), word_indices=tuple(indices))
