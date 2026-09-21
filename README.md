# Quranic Phonemizer

<p align="center">
  <a href="https://pypi.org/project/quranic-phonemizer/"><img src="https://img.shields.io/pypi/v/quranic-phonemizer" alt="PyPI version"></a>
  <a href="https://phonemizer.qud.dev/"><img src="https://img.shields.io/badge/Demo-Website-blue" alt="Website"></a>
  <a href="https://openreview.net/forum?id=hZt0JK28iV"><img src="https://img.shields.io/badge/Paper-OpenReview-red" alt="Paper"></a>
  <a href="https://github.com/Hetchy/Quranic-Phonemizer/blob/main/LICENSE"><img src="https://img.shields.io/pypi/l/quranic-phonemizer" alt="License"></a>
</p>

Quranic Grapheme-to-Phoneme (G2P) converter and tajweed annotator for the riwayat of Hafs 'An Asim and Warsh 'An Nafi' that converts text to phoneme sequences with comprehensive support for waqf/ibtidaa transformations and tajweed breakdowns.

Use cases:

- **Speech Recognition**: Phonetically transcribe recitations, create training data for machine learning systems
- **Text-to-Speech**: Develop accurate TTS systems for Qurʾanic Arabic
- **Linguistic & Tajweed Analysis**: Study phonological patterns and tajweed rule distributions across the Qurʾan, apply tajweed rule labels and colors
- **Educational Tools**: Build interactive applications for assessing Quranic and tajweed pronunciation
- **Timing Analysis**: Generate word-by-word timestamps for recitations, analyse madd/ghunnah durations

## Table of Contents
- [Phoneme Inventory](#phoneme-inventory)
- [Quick start](#quick-start)
- [Waqf](#waqf)
- [Analysis](#analysis)
- [Tajweed rules](#tajweed-rules)
- [Variants](#variants)
- [Contributing](#contributing)
- [Credits](#credits)
- [Citing](#citing)

## Phoneme Inventory

The phoneme inventory uses the standard International Phonetic Alphabet (IPA) [Arabic phonemes](https://en.wikipedia.org/wiki/Help%3AIPA/Arabic?utm_source=chatgpt.com) alongside custom phonemes for Tajweed rules. Hafs has 68 base phonemes plus 5 optional tokens; Warsh has 71 base phonemes plus 5 optional tokens.

### Foundational Phonemes

| **Letter**               | **Phoneme**              | **Letter** | **Phoneme**               | **Letter** | **Phoneme**              | **Letter** | **Phoneme**              |
|:------------------------:|:------------------------|:----------:|:-------------------------|:----------:|:------------------------|:----------:|:------------------------|
| أ , إ , ء , ؤ , ئ        | `ʔ`                      | د          | `d` / `dd`                | ض          | `dˤ` / `dˤdˤ`            | ك          | `k` / `kk`              |
| ب                        | `b` / `bb`               | ذ          | `ð` / `ðð`                | ط          | `tˤ` / `tˤtˤ`            | ل          | `l` / `lˤ` / `ll` /  `lˤlˤ` |
| ت                        | `t` / `tt`               | ر          | `r` / `rˤ` / `rr` / `rˤrˤ`| ظ          | `ðˤ` / `ðˤðˤ`            | م          | `m`                      |
| ث                        | `θ` / `θθ`               | ز          | `z` / `zz`                | ع          | `ʕ` / `ʕʕ`               | ن          | `n`                      |
| ج                        | `ʒ` / `ʒʒ`               | س          | `s` / `ss`                | غ          | `ɣ`                      | هـ         | `h` / `hh`               |
| ح                        | `ħ` / `ħħ`               | ش          | `ʃ` / `ʃʃ`                | ف          | `f` / `ff`               | و          | `w` / `ww`               |
| خ                        | `x` / `xx`               | ص          | `sˤ` / `sˤsˤ`             | ق          | `q` / `qq`               | ي , ى      | `j` / `jj`               |

`lˤ` is the single emphatic lam used in Warsh. Gemination (shaddah) is represented by repeating the phoneme to create distinct phonemes. Note that there is no gemination for `m` / `n` (modelled as tajweed instead), and for `ʔ` / `ɣ` (do not exist in the Qurʾān).

### Vowel Phonemes

| **Vowel**                      | **Phoneme**            |
|:--------------------------------|:------------------------|
| َ                              | `a`                    |
| ُ                              | `u`                    |
| ِ                              | `i`                    |
| ا , ى                          | `aː` / `aˤː`           |
| و                              | `uː`                   |
| ي , ى                          | `iː`                   |
| Warsh Taqlil (Imala Sughra) | `ɛ` / `ɛː`                   |

### Tajweed Phonemes

| **Rule**       | **Phoneme**                   |
|----------------|:------------------------------|
| Ikhfaa         | `ŋ`                           |
| Ikhfaa shafawi | `ŋ` / `m̃`                    |
| Iqlab          | `ŋ` / `m̃`                    |
| Idgham         | `ñ` / `m̃` / `j̃` / `w̃`     |
| Qalqala        | `Q`                           |

Iqlab and ikhfaa shafawi use the open-lip nasal `ŋ` by default. Their nasal variants can instead select the closed-lip bilabial realization `m̃`, since both alternatives exist in recitations (see [Variants](#variants)).

### Extra Phonemes

`extra_phonemes` selects toggleable output distinctions. Its default is empty to keep the default inventory compact; the underlying reading rule is unchanged.

| **API option**              | **Phoneme**        | **Default** | **Notes** |
|-----------------------------|:------------------|:-----------:|:---------|
| `emphatic_fatha`            | `aˤ`              | Off         | Allophone |
| `emphatic_ikhfaa`           | `ŋˤ`              | Off         | Heavy nasal allophone before the 5 ikhfaa-isti'la letters |
| `qalqala_degree`            | `QQ`              | Off         | Stronger Qalqala kubra/akbar allophone |
| `imala` (kubra)             | `e:`              | Off         | Hafs: `مَجْر۪ىٰهَا` (11:41), off -> `i:` <br> Warsh: `طَه۪` (20:1), off -> `ɛ:` |
| `tashil` (Hafs only)        | `ʔ̞`              | Off         | One case Hafs: `ءَا۬عْجَمِيٌّ` (41:44), off -> `ʔ` <br>Warsh always applies Tashil as `ʔ̞` since it is common |
| `taqlil_short` (Warsh only) | `ɛ`               | Off         | The short taqlil on the raa of the fixed `رأى` family, off -> `a`<br> The `taqlil` rule and light raa always apply |

## Quick start

Install the package and create a reader for the riwayah you need:

```bash
pip install quranic-phonemizer
```

```python
from quranic_phonemizer import Phonemizer

hafs = Phonemizer()
warsh = Phonemizer(riwayah="warsh")

for name, reader, ref in (
    ("Hafs 1:4", hafs, "1:4"),
    ("Warsh 1:3", warsh, "1:3"),
):
    result = reader.analyse(ref)
    print(name)
    print(result.text())
    print(" ".join(result.phonemes()))
```

```text
Hafs 1:4
مَـٰلِكِ يَوْمِ ٱلدِّينِ
m a: l i k i j a w m i dd i: n

Warsh 1:3
مَلِكِ يَوْمِ اِ۬لدِّينِۖ
m a l i k i j a w m i dd i: n
```

### References

`analyse()` accepts words, verses, surahs, and ranges:

| Reference | Selection |
| :--- | :--- |
| `"1"` | Surah 1 |
| `"1:3"` | Ayah 3 of surah 1 |
| `"1:3:1"` | Word 1 of ayah 1:3 |
| `"1:3-1:4"` | Ayahs 1:3 through 1:4 |
| `"1:3-1:4:2"` | Ayah 1:3 through word 2 of 1:4 |
| `"1-2:2"` | Surah 1 through ayah 2:2 |

## Waqf

Use `verse` to stop at every ayah end in a range. Mushaf sign keys and exact
word references can add other stops:

```python
hafs.analyse("68:33", stop_signs=("optional_stop",))
hafs.analyse("2:255", stop_refs=("2:255:7",))
```

This applies waqf to `2:255:7` and ibtidaa to `2:255:8`, or to any words marked with `ۚ ` in `68:33`, changing phonemes and tajweed rules accordingly.

Note the first and last word of a request always apply ibtidaa and waqf respectively.

`reader.available_stop_signs` gives the keys valid for that reader. Hafs uses:

| Stop key | Sign |
| :--- | :---: |
| `verse` | ۝ |
| `preferred_continue` | ۖ |
| `preferred_stop` | ۗ |
| `optional_stop` | ۚ |
| `compulsory_stop` | ۘ |
| `prohibited_stop` | ۙ |
| `either_stop` | ۛ |

Warsh exposes only `optional_stop` ۖ

## Analysis

The phonemizer exposes more detailed analysis, breakdowns, relationships and rules, as shown below. See the [public API reference](docs/public-api.md) for the full details.

```python
result = hafs.analyse("112:2")

print(result.text())
print(" ".join(result.phonemes()))
print(sorted({occurrence.rule_id.value for occurrence in result.rule_occurrences}))
```

```text
ٱللَّهُ ٱلصَّمَدُ
ʔ a lˤlˤ aˤ: h u sˤsˤ a m a d Q
['hamza_wasl_fatha', 'hamza_wasl_silent', 'lam_shamsiyyah', 'madd_tabii',
 'qalqala_kubra', 'tafkheem', 'waqf_diacritic_drop']
```

The core records are available directly:

```python
result.words
result.boundaries
result.sounds
result.rule_occurrences
result.mergers
```

The same result provides its source units, highlight groups, and transformed cells:

```python
source = result.source()
highlights = result.highlights()
cells = result.cells(spelling="transformed")
```

The cell view is the render-ready alignment between transformed spelling,
phonemes, and tajweed. It informs what to draw, what changed, where a
sound is presented, and which rules belong to each cell:

| Word | Transformed cell | Role and placement | Status | Sound relationship | Rules |
| :---: | :---: | :--- | :--- | :--- | :--- |
| `ٱللَّهُ` | `أ` | Letter on the main row | Replaced | Owns `ʔ` | `hamza_wasl_fatha` |
| `ٱللَّهُ` | `َ` | Haraka above `أ`; inserted after it | Inserted | Owns `a` | — |
| `ٱللَّهُ` | `ل` | Letter on the main row | Present | Presents `lˤlˤ` with the next cell | `lam_shamsiyyah` |
| `ٱللَّهُ` | `لّ` | Letter on the main row | Present | Owns the shared `lˤlˤ` | `tafkheem` |
| `ٱللَّهُ` | `َ` | Haraka above `لّ` | Present | Presents `aˤː` with the following madd cell | `tafkheem` |
| `ٱللَّهُ` | `ٰ` | Madd inserted after the fatha | Inserted | Owns the shared `aˤː` | `madd_tabii`, `tafkheem` |
| `ٱللَّهُ` | `ه` | Letter on the main row | Present | Owns `h` | — |
| `ٱللَّهُ` | `ُ` | Haraka above `ه` | Present | Owns `u` | — |
| `ٱلصَّمَدُ` | `ٱ` | Letter on the main row | Dropped | No phoneme | `hamza_wasl_silent` |
| `ٱلصَّمَدُ` | `ل` | Letter on the main row | Present | Presents `sˤsˤ` with the next cell | `lam_shamsiyyah` |
| `ٱلصَّمَدُ` | `صّ` | Letter on the main row | Present | Owns the shared `sˤsˤ` | `tafkheem` |
| `ٱلصَّمَدُ` | `َ` | Haraka above `صّ` | Present | Owns `a` | `tafkheem` |
| `ٱلصَّمَدُ` | `م` | Letter on the main row | Present | Owns `m` | — |
| `ٱلصَّمَدُ` | `َ` | Haraka above `م` | Present | Owns `a` | — |
| `ٱلصَّمَدُ` | `دْ` | Letter on the main row | Replaced | Owns `d` and the qalqala release `Q` | `qalqala_kubra` |
| `ٱلصَّمَدُ` | ~~`ُ`~~ | Haraka above `د` | Dropped | No phoneme | `waqf_diacritic_drop` |

`document()` returns JSON-compatible schema 2 documents for the analysis and its projections.

## Tajweed rules

The catalogue is scoped to the reader. Each definition provides an ID, English name, Arabic name, and summary:

```python
for rule in hafs.tajweed_rules:
    print(rule.id.value, rule.name, rule.arabic_name, rule.summary)

result.rule_definition("idgham_bila_ghunnah")
result.rule_occurrences
```

`rule_occurrences` contains the rules applied to that request. Hafs and Warsh share these published rule IDs:

- Noon / Meem: `izhar`, `izhar_shafawi`, `ikhfaa`, `ikhfaa_shafawi`, `iqlab`, `idgham_bi_ghunnah`, `idgham_bila_ghunnah`, `idgham_shafawi`, `ghunnah_mushaddadah`
- Assimilation and definite articles: `idgham_mutamathilayn`, `idgham_mutaqaribayn`, `idgham_mutajanisayn_kamil`, `idgham_mutajanisayn_naqis`, `lam_shamsiyyah`, `lam_qamariyyah`
- Qalqala and Emphasis: `qalqala_sughra`, `qalqala_kubra`, `qalqala_akbar`, `tafkheem`, `tarqeeq`
- Madd: `madd_tabii`, `madd_muttasil`, `madd_munfasil`, `madd_lazim`, `madd_arid_lissukun`, `madd_leen`, `madd_iwad`, `madd_badal`, `madd_silah`
- Hamza and adjacent sakin letters: `ibdal_hamza`, `hamza_wasl_silent`, `hamza_wasl_fatha`, `hamza_wasl_damma`, `hamza_wasl_kasra`, `iltiqa_haraka`, `iltiqa_shortening`
- Waqf and silence: `waqf_diacritic_drop`, `waqf_silah_drop`, `waqf_taa_marbuta`, `pausal_alif` (seven alifs), `orthographic_silence` (rasm)
- Special: `imala`, `tashil`, `ishmam`

Warsh adds five unique rules:

- `taqlil`
- `naql`
- `madd_leen_mahmuz`
- `madd_mim_al_jam`
- `madd_yaa_zawaid`

## Variants

A riwayah carries authenticated khilaf in awjuh and turuq: places where more than one
performance is transmitted for the same text. These are lexical words, systematic
patterns, and junctions between words. Each variant is one selector taking one
scalar value, chosen at construction:

```python
from quranic_phonemizer import Phonemizer, available_variants

available_variants("hafs")["man_raq"]

sakt = Phonemizer(variants={"man_raq": "sakt"})
idraj = Phonemizer(variants={"man_raq": "idraj"})

sakt_res = sakt.analyse("75:27")
idraj_res = idraj.analyse("75:27")

print(sakt_res.text())
print(" ".join(sakt_res.phonemes()))
print(" ".join(idraj_res.phonemes()))
```

```text
وَقِيلَ مَنْ ۜ رَاقٍ

w a q i: l a m a n rˤ aˤ: q Q
w a q i: l a m a rˤrˤ aˤ: q Q
```

`available_variants(riwayah)` gives the legal values and the default for each ID,
`variant_catalogue(riwayah)` adds presentation and applicability metadata, and
`result.variant_occurrences()` reports the sites contained in one analysis. See
the [variants contract](docs/variants.md) for details, options, scopes, examples and research sources.

Hafs publishes 26 selectors:

- Word readings: `daaf_haraka`, `yabsut`, `bastah`, `almusaytirun`, `bimusaytir`, `istifham_article`, `tamanna_noon`
- Joined readings: `noon_wasl`, `yaseen_wasl`, `irkab_maana`, `yalhath_dhalik`
- Stopping and starting: `yaa_aatani_waqf`, `salasila_waqf`, `alism_ibtidaa`
- Sakt: `maliyah_halak`, `iwaja_qayyima`, `man_raq`, `bal_ran`
- Raa: `raa_firq`, `raa_alqitr_waqf`, `raa_misr_waqf`, `raa_wanuthur_waqf`, `raa_yasr_waqf`, `raa_asr_waqf`
- Nasal: `iqlab_nasal`, `ikhfaa_shafawi_nasal`

Warsh publishes 57:

- Word readings: `tamanna_noon`, `istifham_article`
- Joined readings: `noon_wasl`, `maliyah_halak`, `kitabiyah_inni`
- Stopping and starting: `article_ibtidaa`
- Inclination: `dhat_yaa`, `arakahum`, `al_jar`, `jabbarin`, `haa_verse_heads`, `maryam_haa_yaa`, `yaseen_yaa`
- Hamza: `hamza_dhat_fath`, `hamza_muttafiq`, `hamza_damm_kasr`, `jaa_aal`, `hamza_kasr_yaa`, `hamza_aimma`, `hamza_arayta`, `ha_antum`, `allai_waqf`
- Lam: `lam_dhat_yaa`, `lam_verse_heads`, `lam_separated_by_alif`, `lam_final_waqf`, `lam_salsal`, `lam_after_taa`, `lam_after_zhaa`
- Raa: the six Hafs raa selectors, plus `raa_ishruna_kibr`, `raa_alishraq`, `raa_hayran`, `raa_bisharar`, `raa_five_words`, `raa_sihra`, `raa_iram`, `raa_alif_ayn`, `raa_alif_hamza`, `raa_dual_alif`, `raa_ashiratukum`, `raa_wizraka`, `raa_dhikraka`, `raa_wizra_ukhra`, `raa_ijrami`, `raa_hidhrakum`, `raa_ibrah_kibrahu`, `raa_hasirat_suduruhum`, `raa_fathatan`, `raa_damma`
- Nasal: `iqlab_nasal`, `ikhfaa_shafawi_nasal`

The two readings share 12 IDs. A shared ID may carry a
different default or cover different positions in each riwayah.

## Contributing

If you find any issues or have feature suggestions, please open an issue or submit a pull request.

Future plans include extending the phonemizer to other riwayat, beginning with Qalun 'An Nafi' and Shu'ba 'An Asim. Contributions are welcome!

## Credits

The project makes use of the [Quranic Universal Library's (QUL) Quran script](https://qul.tarteel.ai/resources/quran-script/312).

## Citing

If you use this phonemizer in your work, please cite [the paper](https://openreview.net/pdf?id=hZt0JK28iV) as follows:

```bibtex
@inproceedings{
ibrahim2025quranic,
title={Qur{\textquoteright}anic Phonemizer: Bringing Tajweed-Aware Phonemes to Qur{\textquoteright}anic Machine Learning},
author={Ahmed Ibrahim},
booktitle={5th Muslims in ML Workshop co-located with NeurIPS 2025},
year={2025},
url={https://openreview.net/forum?id=hZt0JK28iV}
}
```
