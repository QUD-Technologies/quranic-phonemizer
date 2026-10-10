# CLAUDE.md

## Project

Quranic Phonemizer converts Quran references into recitation-aware phonemes.
It currently ships the Hafs reading in Uthmani and IndoPak scripts, applies
tajweed across word boundaries, and supports connected reading, stopping, and
starting. Its result preserves the written text, canonical reading, performed
sounds, rule occurrences, and the alignments between them.

The central distinction is between what a script writes, what the riwayah
reads, and what is actually pronounced under a boundary plan.

## Repository map

- `orthography/` reads script-specific graphemes and marks without deciding
  the recitation.
- `canon/` and `model/` build the script-independent reading and preserve how
  it is spelled.
- `engine/`, `rules/`, and `riwayat/` apply boundary-sensitive tajweed and
  bind the data and classifiers for a reading.
- `render/` owns phoneme tokens; `phonemize/` assembles the public result.
- `data/riwayat/` holds reading-specific corpora and authored facts;
  `data/shared/` is only for facts demonstrated to be reading-independent.

## Documentation

- Start with `docs/architecture.md`; use `docs/public-api.md` for the result
  contract and `docs/conformance.md` for known corpus-gate residue.
- `docs/variants.md` is the cross-riwayah selector contract;
  `docs/{hafs/warsh}/research/` contains research and domain facts. For warsh, use v2.
- Use `docs/performance.md` for reproducible benchmarks, profiling findings,
  full-Quran resource measurements, and large-batch guidance.

## Working principles

- The runtime is riwayah-aware but only Hafs is implemented. Do not present
  the tentative new-riwayah notes as an established abstraction.
- Raw Unicode and script conventions stay in `orthography/`. Tajweed rules
  operate on canonical or performed structures, not script codepoints.
- For a riwayah with one supported script, a reviewed mark-sequence family may
  directly supply the canonical fact it writes; an unreviewed sequence fails
  projection rather than being guessed. Research-derived predicates and counts
  remain conformance reconciliation, not required runtime derivations. Hafs is
  the deliberate two-script exception: its facts stay script-independent.
  Genuine closed exceptions belong in authored data.
- Phoneme strings belong in `render/`; other layers use typed model values.
- Treat wasl, waqf, and ibtidaa as explicit boundary state. Never infer them
  from array position or mutate neighbouring words to simulate a join.

- Source comments explain only non-obvious constraints; docstrings state the
  contract not visible from the signature. Keep both short.
- Source must describe current behaviour only. Do not reference design docs,
  numbered sections, project phases, reviews, history, or corpus measurements.
- Use ASCII transliteration in prose. Arabic script is allowed when quoting a
  word or mark. Avoid typographic punctuation in source.
- Do not write essays in comments, keep them short and to the point and only complement the code; which should be self-explanatory anyways. You do not need to explain general domain knowledge in comments, a reader is already familiar with that, but you can bring up specific domain knowledge that is relevant to the code.
- Respect the import, role, transform, and phoneme-ownership boundaries checked
  by `tools/structure_lint.py`. Comment and size guidance is review advice.

## Validation

Before writing or modifying tests, read `tests/README.md` and follow its
semantic-case, source-span, boundary, and file-ownership conventions.

Use `python tools/quick.py <targeted tests...>` while iterating; it never infers
or expands the test scope. Pull requests run the full ordinary suite, essential
structure checks, and exact Arabic source-context validation. The PR suite uses
two pytest workers to bound corpus memory while parallelizing independent cases.

## Deploy

Releases are annotated `v*` tags. The version comes from the tag
(setuptools-scm), so there is no version commit. Pushing the tag runs
`.github/workflows/publish.yml`, which builds and uploads to PyPI; do not
also upload by hand.

Before tagging, run the precheck and read its report:

```bash
python tools/prerelease.py --web ../phonemizer-web
```

It reports and never blocks. Three things are reported: that every reading the
site draws, and every variant option, still produces a payload its renderer can
join; the per-word phoneme differences against the newest release on PyPI,
across both readings and both boundary plans; and the same sweep over the typed
analysis and cell documents, which compares rule placements, phoneme and
character attributions, roles, and cell status whenever the baseline publishes
those documents too. A reading the baseline does not publish is reported as
having no baseline rather than as a difference.

The corpus is walked one verse at a time in short-lived shard processes, and
only digests are held; the readings that moved are re-read for their detail.
Keep it that way -- a surah-wide or corpus-wide request holds its whole score
alive.

Release once the report reads as intended:

```bash
python tools/gates.py
python -m pytest tests/conformance/test_warsh_cell_projection.py --runslow -q
git tag -a vX.Y.Z -m "vX.Y.Z: <summary>" && git push origin vX.Y.Z
```

The site pins the release in `requirements.txt`, and merging to its main
deploys the Space, so bump that pin only after the version is on PyPI.

Cross-script, L1, roundtrip, attestation, and legacy snapshot tools are manual
audits. Run pytest-based audits explicitly with
`python -m pytest --runaudit -m audit`; do not treat them as routine gates.

Ruff checks imports and objective Python hygiene in pull requests and releases.
Run `python -m ruff check . --fix` for its safe automatic cleanup.
