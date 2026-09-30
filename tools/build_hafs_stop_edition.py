"""Regenerate the Hafs 1421 stop-mark overlay from the Digital Khatt text.

The packaged Hafs corpus writes the waqf marks of the 1405 Madinah mushaf.
Digital Khatt follows the 1421 printing, which moves, changes, adds or drops
about three hundred of them. Only the marks differ; the words are the same.
The overlay records, for every word whose trailing mark differs, the mark the
1421 edition writes there (an empty string when it writes none).

Run: python tools/build_hafs_stop_edition.py --dk path/to/digital_khatt.json

The Digital Khatt file maps `surah:ayah:word` to `{"text": ...}` and carries
one extra end-of-ayah slot per verse, which is skipped.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from quranic_phonemizer.corpus import VerseRef  # noqa: E402
from quranic_phonemizer.riwayat.hafs.resources import (  # noqa: E402
    STOP_OVERLAY_DIR,
    base_corpus,
)
from quranic_phonemizer.stop_editions import STOP_MARKS, trailing_mark  # noqa: E402

EDITION = "1421"
VERSE_MARKER = "۝"
MARK = re.compile(f"[{STOP_MARKS}]")


def _dk_verses(path: Path) -> dict[tuple[int, int], list[str]]:
    with path.open(encoding="utf-8") as fh:
        raw = json.load(fh)
    verses: dict[tuple[int, int], list[tuple[int, str]]] = {}
    for ref, entry in raw.items():
        surah, ayah, word = map(int, ref.split(":"))
        if entry["text"].startswith(VERSE_MARKER):
            continue
        verses.setdefault((surah, ayah), []).append((word, entry["text"]))
    return {key: [text for _, text in sorted(words)] for key, words in verses.items()}


def _dk_mark(text: str, ref: str) -> str:
    marks = MARK.findall(text)
    if len(marks) > 1 or (marks and not text.endswith(marks[0])):
        raise SystemExit(f"{ref}: expected at most one trailing mark in {text!r}")
    return marks[0] if marks else ""


def build_overlay(dk_path: Path) -> dict[str, str]:
    corpus = base_corpus()
    dk = _dk_verses(dk_path)
    overlay: dict[str, str] = {}
    for surah, counts in corpus.surah_info.items():
        for ayah in range(1, len(counts) + 1):
            words = corpus.words(VerseRef(int(surah), ayah))
            dk_words = dk[(int(surah), ayah)]
            if len(dk_words) != len(words):
                # 37:130 is the one verse Digital Khatt writes as fewer words.
                # Its only mark is the final one, which both editions agree on.
                _check_unsplit(words, dk_words)
                continue
            for (location, text), dk_text in zip(words, dk_words):
                ref = f"{location.surah}:{location.ayah}:{location.word}"
                wanted = _dk_mark(dk_text, ref)
                if wanted != trailing_mark(text):
                    overlay[ref] = wanted
    return overlay


def _check_unsplit(words, dk_words) -> None:
    ours = [trailing_mark(text) for _, text in words]
    theirs = [_dk_mark(text, "unsplit verse") for text in dk_words]
    if [m for m in ours if m] != [m for m in theirs if m]:
        raise SystemExit(f"{words[0][0]}: word counts differ and so do the marks")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dk", type=Path, required=True)
    args = parser.parse_args()
    overlay = build_overlay(args.dk)
    dst = STOP_OVERLAY_DIR / f"{EDITION}.json"
    ordered = dict(sorted(overlay.items(), key=lambda kv: tuple(map(int, kv[0].split(":")))))
    dst.write_text(
        json.dumps(ordered, ensure_ascii=False, indent=0) + "\n", encoding="utf-8"
    )
    print(f"{len(ordered)} words differ from the packaged corpus; wrote {dst}")


if __name__ == "__main__":
    main()
