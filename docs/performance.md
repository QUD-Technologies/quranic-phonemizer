# Performance

The public facade separates eager analysis from lazy selective projections.
Measure the operation your consumer actually performs rather than assuming a
cell-heavy request represents a phoneme-only caller.

## Reproducible benchmark

From the repository root:

```bash
python tools/benchmark.py
python tools/benchmark.py 1:1 2:255 55 --repeats 5
```

The JSON report records:

- Python and platform details;
- reader construction time;
- median eager `analyse()` time and Python allocation measurements;
- the schema-v2 analysis document digest;
- first and cached timings for source, highlights, source cells, and
  transformed cells.

Use `python tools/compare_perf.py <base> [<candidate>]` to compare two git
revisions on the same host. It alternates execution order and reports a
regression when the median request ratio exceeds the configured tolerance.

## Work performed by each call

| Call | Work |
| --- | --- |
| `reader.analyse(ref)` | Reference resolution, canonical build, boundary resolution, performance, native facts, inscription facts, bundle, and `AnalysisResult`. |
| `result.phonemes()` | Reads eager core tokens only. |
| `result.source()` | Builds and caches source characters, units, and placements. |
| `result.highlights()` | Reuses the source view and builds highlight groups. |
| `result.cells(spelling="source")` | Reuses shared state and builds native source cells. |
| `result.cells(spelling="transformed")` | Reuses shared state and applies the configured pen to native cells. |
| `result.document(kind)` | Builds only the selected typed projection, then serializes its native envelope. |

The projection cache is result-local and guarded for concurrent access.
Repeated calls return the same immutable value and do not rerun the engine or
boundary resolver.

## Whole-surah scaling

A request's cost should grow linearly with its word count. Two patterns break
that and are kept out of the hot path:

- A rule that asks what earlier phases did to one slot reads
  `Plan.effects_at(slot)` or `Plan.verdicts_at(slot)`, not a scan of every
  recorded effect.
- A canonical pass that needs each word's written text calls
  `canon.passes.word_texts(reading)` once, not a per-word scan of every
  cluster in the request.

Measured on one Windows 11 host (Python 3.13, 12 cores, shared with other
work, so treat single runs as approximate), one `analyse()` call per surah
plus `phonemes(by="word")`, wall time and process peak working set:

| Request | Before | After |
| --- | --- | --- |
| Warsh 18 (1579 words) | 97 s, 156 MB | 2.8 s, 156 MB |
| Hafs 18 | 50 s, 66 MB | 1.1 s, 66 MB |
| Warsh 2 (6117 words) | 1113 s, 238 MB | 11.2 s, 240 MB |
| Hafs 2 | 346 s, 148 MB | 6.9 s, 147 MB |

Peak memory is dominated by the retained score and documents, not by the
removed scans. A single verse remains about 0.02 s.

## Large requests

One whole-surah or whole-Quran request keeps its complete score, inscription,
performance, bundle, and any requested projection cache alive for as long as
the `Result` remains reachable. Prefer verse or bounded-range requests unless
cross-verse behavior requires a larger span. Do not request transformed cells
for a caller that only needs phonemes or continuous-text highlights.

When comparing retained memory, release the result and run collection before
measuring the next case. Loaded riwayah resources and the alphabet are cached
process-locally and intentionally remain shared across readers.
