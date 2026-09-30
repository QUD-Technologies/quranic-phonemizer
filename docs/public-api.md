# Public API

The ordinary consumer path is one root import, one configured reader, and one
analysis call:

```python
from quranic_phonemizer import Phonemizer, Result

reader = Phonemizer()
result: Result = reader.analyse("1:1")
```

The facade returns native analysis records. It does not translate them into
an adapter-specific graph or infer presentation semantics.

## Reader configuration

```python
reader = Phonemizer(
    riwayah="hafs",
    script="uthmani",
    variants={"iqlab_nasal": "closed"},
    extra_phonemes=("emphatic_fatha", "emphatic_ikhfaa"),
    stop_edition="1421",
)
```

- `riwayah` selects the reading. The default is `hafs`.
- `script` selects one of that reading's packaged scripts. The default is
  `uthmani`.
- `variants` selects scalar choices from the reading's khilaf catalogue.
- `extra_phonemes` enables optional notation distinctions. Fixed distinctions
  remain active without being listed here.
- `stop_edition` selects which Madinah mushaf printing's waqf marks the text
  carries. Hafs packages `1421` (the default, as written by Digital Khatt) and
  `1405`. They differ only in the marks on about 350 words; the words and
  their spelling are identical. Warsh packages a single edition and accepts
  only `None`. `available_stop_editions(riwayah)` lists the choices, default
  first; an unpackaged name raises `UnknownStopEdition`.

Construction validates riwayah, script, variants, optional phonemes, and stop
edition before a request is run. `UnknownExtraPhoneme`, `UnknownRiwayah`, and
`UnknownStopEdition` are public `ValueError` subclasses.

## Configuration-scoped catalogues

The reader publishes only values applicable to its selected configuration:

```python
reader.available_stop_signs
reader.available_variants
reader.variant_catalogue
reader.tajweed_rules
```

Equivalent metadata queries are available at the package root:

```python
from quranic_phonemizer import (
    available_stop_editions,
    available_stop_signs,
    available_variants,
    variant_catalogue,
    supported_riwayat,
    tajweed_rules,
)

available_stop_editions("hafs")
available_stop_signs("hafs", script="uthmani")
available_variants("hafs")
variant_catalogue("hafs")
tajweed_rules("hafs")
supported_riwayat()
```

`available_variants` is the compact selector contract. `variant_catalogue`
adds producer-owned groups, an optional subgroup for finer website
sectioning, display metadata, visibility, fixed occurrence spans, anchors,
and boundary requirements. A dynamic-scope selector has no fixed spans and a
`None` occurrence count. After a request, `result.variant_occurrences()`
maps matching spans to result-local word and boundary IDs and says whether
each selector is active or masked by the current boundary plan; a
dynamic-scope selector contributes a row for every site it realizes inside
the analysed window.

The packaged stop catalogues are:

| Configuration | Stop classes |
| --- | --- |
| Hafs/Uthmani | `verse`, `preferred_continue`, `preferred_stop`, `optional_stop`, `compulsory_stop`, `prohibited_stop`, `either_stop` |
| Hafs/IndoPak | the Hafs/Uthmani classes plus `permitted_stop` |
| Warsh/Uthmani | `verse`, `optional_stop` |

Warsh Uthmani authors `ۖ` as `optional_stop`. The source character and its
boundary retain that exact glyph and `StopAdvice.OPTIONAL_STOP` whether or not
the caller selects the stop class. `verse` is a synthetic selector shared by
all scripts; it stops at every ayah boundary in the requested range.

## Requests and stop plans

```python
result = reader.analyse(
    "2:255",
    stop_signs=("preferred_stop",),
    stop_refs=("2:255:35",),
)
```

`ref` may address one word, verse, surah, or same-depth range. `stop_signs`
selects `verse` or stop-advice classes. `stop_refs` selects exact word
references. An empty tuple is valid for either option.

References use the selected script's own ayah and word coordinates. The same
passage can therefore have a different reference in another riwayah. Word
records returned by the result use that same coordinate system.

Stop classes are validated against the reader before boundary resolution.
Unknown or unavailable names are collected, sorted, and reported by the public
`UnknownStopSign` error together with the applicable catalogue. Reference
errors continue to use the existing request-domain exceptions.

Callers request stops, not `sakt`. Sakt is authored by the riwayah.

## Eager core result

`analyse()` resolves the request and eagerly builds `result.analysis`, an
immutable `AnalysisResult`. The facade exposes its central records directly:

```python
result.words
result.boundaries
result.sounds
result.rule_occurrences
result.mergers

result.text()
result.phonemes()
result.phonemes(by="word")
```

`text()` is the exact source spelling. There is no general recited-text
projection. Use transformed cells when a consumer needs a spelling delta with
status and provenance.

`result.analysis` also carries `ref`, `riwayah`, `script`, the resolved
`variant`, `extra_phonemes`, `schema_version`, and `canon_digest`.

## Boundaries

For `N` words, `result.boundaries` has `N + 1` records.

| State | Meaning |
| --- | --- |
| `start` | Leading request boundary before the first word. |
| `join` | Ordinary continuation across an internal boundary. |
| `sakt` | Authored breathless pause that blocks cross-boundary interaction without applying waqf or ibtidaa. |
| `stop` | Waqf before the boundary; an internal stop also starts the following word. The trailing boundary is always a stop. |

Each boundary identifies its before and after word IDs, exact written stop sign
when present, and authored stop advice when present. These are resolved results,
not a menu of possible states.

## Rule catalogue and occurrences

```python
result.rule_catalogue
result.rule_definition("idgham_bi_ghunnah")
result.rule_occurrences
```

The catalogue contains only identifiers the selected riwayah declares it can
emit, followed by its published silence reasons. It is additive metadata and
is not embedded in the schema-versioned analysis document. `UnknownRule` is
raised when a lookup is outside that catalogue.

Occurrences are the source of truth for what happened in this request. Their
unit and sound references answer different questions and may both be present.

## Source view

```python
source = result.source()

for character in source.characters:
    print(character.index, character.text, character.kind)

for unit in source.units:
    print(unit.text, unit.kind, unit.silence, unit.rule_occurrence_ids)

for token in source.animation_tokens:
    print(token.text, token.sound_ids, token.policy, token.target_token_id)
```

`source()` returns the native `SourceView`. Characters are exact Unicode
scalars. Units are the producer-tokenized letter surface. Stop signs and sakt
marks belong to boundaries rather than lexical units. Animation tokens are
foundation-level paint targets derived from source units and sound ownership.
A timed token owns sound IDs; a soundless token names the previous or next
timed token it co-highlights through its policy and target ID.
One source unit can supply multiple character-disjoint paint targets when its
Unicode scalars need different highlight ownership. In particular, a sounded
dagger alef is timed separately from its silent rasm carrier.

## Highlights

```python
for group in result.highlights():
    print(group.unit_ids, group.sound_ids, group.ranges)
```

Highlight groups are generated from the source view without constructing
cells. They share source-unit and sound IDs with the core result.

## Cells

```python
source_cells = result.cells(spelling="source")
transformed_cells = result.cells(spelling="transformed")
```

Both calls return native `CellView` values. The transformed view uses the pen
selected by the reader internally. A caller never imports or constructs it.

Cell status is one of `present`, `inserted`, `replaced`, `dropped`, or `gap`.
Roles, tiers, attachments, source units, rule occurrences, sound ownership,
runs, and merger bridges are producer fields. The facade does not reconstruct
or reinterpret them.

## Lazy caching and identity

Source, highlights, and each cell spelling are built on first use and cached.
Repeated calls return the same immutable value. Concurrent access is guarded so
one result does not build a projection twice.

Every view reuses the session, facts, inscription, bundle, and result-local ID
space created by `analyse()`. References therefore close across all native
documents.

## Versioned documents

```python
analysis = result.document("analysis_result")
source = result.document("source_view")
highlights = result.document("highlight_groups")
cells = result.document("cell_view", spelling="transformed")
```

Each call returns a JSON-compatible dictionary stamped with
`schema_version == 4`:

| Kind | Contents |
| --- | --- |
| `analysis_result` | Metadata, source text, words, boundaries, sounds, rule occurrences, and mergers. |
| `source_view` | Source characters, letter units, animation tokens, silence, and placements. |
| `highlight_groups` | Source ranges and unit IDs grouped by active sound IDs. |
| `cell_view` | Source or transformed educational cells, runs, boundaries, and merger bridges. |

There is no `document("all")`. An unknown kind or invalid cell spelling raises
a user-facing `ValueError`. Low-level document constructors and serializers
remain available from `quranic_phonemizer.analysis` for specialist consumers.

The `@quranic-phonemizer/cells` 2.x package parses schema 2 and owns renderer
layout. The Python producer owns semantics and IDs.
