# Variants

This is the public selector contract for authenticated pronunciation choices in
Hafs 'an Asim and Warsh 'an Nafi through al-Azraq. It covers choices that alter
the phonemizer's sounds, canonical reading, or named rules. It does not model
recitation counts.

The Hafs catalogue includes authenticated paths beyond Shatibiyya. The Warsh
catalogue likewise includes authenticated al-Azraq faces beyond one teaching
profile. The selectors expose those faces without claiming that arbitrary
combinations reconstruct a transmitted route.

Each variant ID takes one scalar value. Selectors are independent: the API does
not validate whether a set of choices reconstructs one historical tariq. A
single ID may have different defaults or cover different positions in each
riwayah when the domain choice is the same but its transmission differs.

`available_variants(riwayah)` returns the legal values and the default for that
riwayah. The default is always the first published option, so numbered controls
use face 1 consistently in Hafs and Warsh. An explicit selection overrides only
its own scope.

`variant_catalogue(riwayah)` adds producer-owned presentation and applicability
metadata: semantic group, display name, optional description, website
visibility, occurrence count, representative occurrence, every fixed word
span, selector anchor, and required boundary state. The two corpus-wide nasal
selectors publish a dynamic scope rather than a fixed occurrence register.
Rows are published in each riwayah's semantic category order. Raa and Warsh
Lam rows additionally publish lexical or systematic subgroup metadata.

`Phonemizer(...).analyse(ref).variant_occurrences()` returns the fixed
occurrences wholly contained in that analysis, with result-local word and
boundary anchors plus `active` and `masked` flags. A choice remains selected
when its required boundary is absent, but it is masked and cannot change that
performance. This keeps Quran coordinates and boundary semantics in the
producer; renderers only display the returned controls.

## Reading the catalogue

- **All states** means wasl, waqf, and ibtidaa unless the row states a lexical
  boundary exception.
- **Wasl** means the relevant words are joined. Stopping before the boundary or
  starting after it makes the selector inactive.
- **Waqf** means a complete stop with sukun. Rawm and ishmam at an ordinary word
  ending are outside this boundary model.
- **Ibtidaa** means beginning at the stated word.
- References use canonical surah and ayah numbering. A script adapter maps
  source-corpus coordinates to canonical/public coordinates while preserving
  the source address as separate provenance.
- Arabic examples identify the domain form. ASCII IDs and option values are
  the API spelling.

Defaults select a coherent popular baseline on the dimensions this phonemizer
models: a Shatibiyya-facing Hafs profile and a popular Moroccan/Shatibiyya-
facing al-Azraq profile. They are not compatibility aliases and do not imply
that another legal value is weak. Because duration choices and some fine route
correlations are intentionally absent, the default vector is not a complete
reconstruction of a historical tariq.

## Shared performance choices

These selectors have the same meaning and default in both riwayat.

| ID | Options and default | Scope and examples | Effect | Source |
| --- | --- | --- | --- | --- |
| `iqlab_nasal` | `open`, `closed`; default `open` | Every realized iqlab, such as `مِنۢ بَعْدِ` | `open` renders the project's generic nasal token `/ŋ/` with a slight lip opening. `closed` renders the bilabial nasal token `/m̃/` with light lip closure. The ghunnah, named iqlab rule, participants, and source ownership are unchanged. | [Transmitted lip postures and their attribution](https://www.islamweb.net/amp/ar/fatwa/52856/) |
| `ikhfaa_shafawi_nasal` | `open`, `closed`; default `open` | Every realized ikhfaa shafawi, such as `تَرْمِيهِم بِحِجَارَةٍ` | `open` renders the project's generic nasal token `/ŋ/` with a slight lip opening. `closed` renders the bilabial nasal token `/m̃/` with light lip closure. The ghunnah, named ikhfaa shafawi rule, participants, and source ownership are unchanged. | [Transmitted lip postures and their attribution](https://www.islamweb.net/amp/ar/fatwa/52856/) |
| `tamanna_noon` | `ishmam`, `ikhtilas`; default `ishmam` | `تَأْمَنَّا`, 12:11; all states | `ishmam` merges the two noons and signals the original damma by the lips. `ikhtilas` keeps both noons and gives the first `/u/` reduced duration; the phoneme quality remains `u`. | [Al-Nashr scan, both faces](https://quranpedia.net/book-attachment/19547/77771), [sound distinction](https://quranpedia.net/book/302/1/260) |

The nasal selectors are rendering choices, not a change to the identity,
participants, or source ownership of the tajwid rule.

## Shared openings, hamza, and word boundaries

| ID | Options and default | Scope and examples | Effect | Source |
| --- | --- | --- | --- | --- |
| `noon_wasl` | `izhar`, `idgham`; default `izhar` in Hafs and Warsh | `نٓ` joined to `وَٱلْقَلَمِ` inside 68:1; wasl only | Keeps the final noon clear or merges it into waw with ghunnah. | [Hafs alternatives](https://quranpedia.net/book-attachment/17989/76549), [Warsh alternatives and preference](https://islamweb.net/ar/library/content/243/280/) |
| `istifham_article` | `ibdal`, `tashil`; default `ibdal` in Hafs and Warsh | `ءَآلذَّكَرَيْنِ` at 6:143 and 6:144, `ءَآلْـَٔـٰنَ` at 10:51 and 10:91, and `ءَآللَّهُ` at 10:59 and 27:59; all states | `ibdal` replaces the article hamza. Both `ibdal_hamza` and `madd_lazim` reach the replacement sound and responsible source character. `tashil` keeps an eased hamza and always classifies tashil. | [Six forms and both faces](https://ablibrary.net/book_content/7278/72) |
| `maliyah_halak` | `sakt`, `idgham`; default `sakt` in Hafs, `idgham` in Warsh, whose mushaf writes the shadda of `هَّلَكَ` | `مَالِيَهْ هَلَكَ`, 69:28 -> 69:29; wasl only | `sakt` realizes the izhar face by keeping the two haa sounds apart with a breathless pause. `idgham` merges them into one geminated haa. | [Both faces and their route correlation](https://islamweb.net/ar/library/index.php?ID=18&bk_no=245), [Hafs performance account](https://www.islamweb.net/ar/library/content/231/68/) |

The `tashil` extra phoneme is a Hafs-only rendering control. Warsh always
renders an eased hamza as `ʔ̞`, so `tashil` is not accepted in its
`extra_phonemes` set.

`taqlil_short` is the converse riwayah-specific rendering control: it is
accepted only for Warsh and defaults off. It exposes the short intermediate
vowel on the raa of the fixed `رأى` family as `/ɛ/`; when disabled that sound
renders as `/a/`. This is not a transmitted face and therefore has no variant
selector. The canonical vowel remains `TAQLIL`, retains the `taqlil` rule, and
keeps the raa light under both renderings.

When ibdal creates a long vowel, `ibdal_hamza` and the applicable madd rule
both reach the resulting sound and the responsible source character. The madd
is normally `madd_tabii`; a following fixed sukun instead yields
`madd_lazim`. An ibdal face that produces a moving consonant does not invent a
madd classification.

## Shared raa choices

Every `light` value emits tarqiq and every `heavy` value emits tafkheem on the
raa sound and source character. When the raa is what gives its following fatha
or alif an emphatic quality, that vowel follows the selected raa: `heavy`
keeps it emphatic and `light` makes it plain. An independent emphasis cause is
not removed.

| ID | Options and default | Scope in Hafs | Scope in Warsh | Source |
| --- | --- | --- | --- | --- |
| `raa_firq` | `light`, `heavy`; default `light` | `فِرْقٍ`, 26:63; wasl only. At waqf the raa is fixed heavy | Same form and scope | [Both faces](https://www.islamweb.net/ar/library/content/245/30/), [tarqiq preference](https://www.islamweb.net/ar/library/content/231/24/) |
| `raa_alqitr_waqf` | `light`, `heavy`; default `light` | `ٱلْقِطْرِ`, 34:12; waqf only | Same form and scope | [Both pausal faces and preference](https://www.islamweb.org/ar/library/content/245/30/) |
| `raa_misr_waqf` | `heavy`, `light`; default `heavy` | The four non-tanwin forms `مِصْرَ` and `بِمِصْرَ` at 10:87, 12:21, 12:99, and 43:51; waqf only | Same four lexical forms and scope | [Both pausal faces and preference](https://www.islamweb.org/ar/library/content/245/30/) |
| `raa_wanuthur_waqf` | `light`, `heavy`; default `light` | The six `وَنُذُرِ` endings at 54:16, 54:18, 54:21, 54:30, 54:37, and 54:39; waqf only | Same six forms; the joined yaa is fixed and drops at waqf | [The exact six Warsh yaas](https://www.islamweb.net/amp/ar/library/content/245/35/), [pausal faces](https://islamweb.net/ar/library/index.php?ID=189&bk_no=70&flag=1&page=bookcontents), [modern preference](https://quranpedia.net/book/302/1/134) |
| `raa_yasr_waqf` | `light`, `heavy`; default `light` | `يَسْرِ`, 89:4; waqf only | Same pausal choice; Warsh has a fixed joined yaa that drops at waqf | [Al-Nashr, yasr at waqf](https://www.islamweb.net/ar/library/content/70/189/) |
| `raa_asr_waqf` | `light`, `heavy`; Hafs default `light`, Warsh default `heavy` | All five `أَسْرِ` and `فَأَسْرِ` sites at 11:81, 15:65, 20:77, 26:52, and 44:23; waqf only | Only the three prefixed `فَاسْرِ` sites at 11:81, 15:65, and 44:23; the two `أَنِ ٱسْرِ` sites are fixed light | [Riwayah-specific hamza readings](https://quranpedia.net/book/436/1/292), [Al-Nashr, asr at waqf](https://www.islamweb.net/ar/library/content/70/189/) |

`بِٱلنُّذُرِ` is not part of `raa_wanuthur_waqf` and is fixed heavy at a
complete stop. `مِصْرًا` and `قِطْرًا` are also excluded because their pausal
alifs preserve the heavy outcome.

## Hafs letter and vowel choices

| ID | Options and default | Scope and examples | Effect | Source |
| --- | --- | --- | --- | --- |
| `daaf_haraka` | `fatha`, `damma`; default `fatha` | The three `ضَعْف` forms in 30:54; all states | Selects the vowel after daad. | [Both faces and preference](https://quranpedia.net/book/1279/1/106) |
| `yabsut` | `seen`, `saad`; default `seen` | `يَبْسُطُ`, 2:245; all states | Selects seen or emphatic saad. | [Hafs seen and saad positions](https://quranpedia.net/book/545/2/11) |
| `bastah` | `seen`, `saad`; default `seen` | `بَسْطَةً`, 7:69; all states | Selects seen or emphatic saad. | [Hafs seen and saad positions](https://quranpedia.net/book/545/2/11) |
| `almusaytirun` | `saad`, `seen`; default `saad` | `ٱلْمُصَيْطِرُونَ`, 52:37; all states | Selects emphatic saad or seen. | [Hafs seen and saad positions](https://tajweed.quranpedia.net/lessons/show/content/30) |
| `bimusaytir` | `saad`, `seen`; default `saad` | `بِمُصَيْطِرٍ`, 88:22; all states | Selects emphatic saad or seen across the supported Hafs paths. | [Al-Nashr, both Hafs transmissions](https://www.islamweb.net/ar/library/content/70/266/) |

## Hafs waqf and ibtidaa choices

| ID | Options and default | Scope and examples | Effect | Source |
| --- | --- | --- | --- | --- |
| `yaa_aatani_waqf` | `hadhf`, `ithbat`; default `ithbat` | `ءَاتَانِيَ`, 27:36; waqf only | Deletes or retains the final yaa at the stop. Wasl always retains it with its vowel. | [Both faces and ithbat preference](https://quran-warch.org/hafs/wasset/book/p425.htm) |
| `salasila_waqf` | `hadhf`, `ithbat`; default `hadhf` | `سَلَاسِلَا`, 76:4; waqf only | Stops without or with the final alif. Wasl has no final alif sound. | [Both faces and preference](https://www.alukah.net/sharia/0/66578/) |
| `alism_ibtidaa` | `hamza`, `lam`; default `hamza` | Beginning at `ٱلِاسْمُ` in `بِئْسَ ٱلِاسْمُ`, 49:11; ibtidaa only | Begins with hamzat al-wasl before the vowel-bearing lam, or begins directly on that lam. Ordinary wasl from `بِئْسَ` is unchanged. | [Both starts and the preferred face](https://www.islamweb.net/ar/library/content/231/79/) |

## Hafs junction and nasal choices

| ID | Options and default | Scope and examples | Effect | Source |
| --- | --- | --- | --- | --- |
| `yaseen_wasl` | `izhar`, `idgham`; default `izhar` | `يسٓ` joined to `وَٱلْقُرْءَانِ`, 36:1 - 36:2; wasl only | Keeps the final noon clear or merges it into waw with ghunnah. | [Both Hafs faces](https://quranpedia.net/book-attachment/17989/76549) |
| `irkab_maana` | `idgham`, `izhar`; default `idgham` | `ٱرْكَب مَّعَنَا`, 11:42; wasl only | Merges baa into meem or keeps both consonants clear. | [Authenticated Hafs route faces](https://quranpedia.net/book/1655/1/20) |
| `yalhath_dhalik` | `idgham`, `izhar`; default `idgham` | `يَلْهَث ذَّلِكَ`, 7:176; wasl only | Merges thaa into dhal or keeps both consonants clear. | [Authenticated Hafs route faces](https://quranpedia.net/book/1655/1/20) |

## Hafs sakt choices

| ID | Options and default | Scope and examples | Effect | Source |
| --- | --- | --- | --- | --- |
| `iwaja_qayyima` | `sakt`, `idraj`; default `sakt` | `عِوَجَا قَيِّمًا`, 18:1 -> 18:2; joined reading only | `sakt` sets `sakt_after` on `عِوَجَا`, realizes the alif substituted for tanwin, and blocks `ikhfaa`. `idraj` continues directly and applies ordinary tanwin-before-qaf `ikhfaa`. | [Authenticated faces at the four positions](https://islamweb.net/amp/ar/library/content/70/115/) |
| `man_raq` | `sakt`, `idraj`; default `sakt` | `مَنْ رَاقٍ`, 75:27; joined reading only | `sakt` sets `sakt_after` on `مَنْ`, preserves the audible noon, and blocks `idgham_bila_ghunnah`. `idraj` applies `idgham_bila_ghunnah` into raa. | [Authenticated faces at the four positions](https://islamweb.net/amp/ar/library/content/70/115/), [effect on idgham](https://www.islamweb.net/ar/library/content/231/68/) |
| `bal_ran` | `sakt`, `idraj`; default `sakt` | `بَلْ رَانَ`, 83:14; joined reading only | `sakt` sets `sakt_after` on `بَلْ`, preserves the audible lam, and blocks `idgham_mutaqaribayn`. `idraj` applies `idgham_mutaqaribayn` into raa. | [Authenticated faces at the four positions](https://islamweb.net/amp/ar/library/content/70/115/), [effect on idgham](https://www.islamweb.net/ar/library/content/231/68/) |

The three selectors are independent. `idraj` means uninterrupted continuation
through the site. A selected sakt is a breathless continuation junction, not
waqf: it sets `sakt_after`, does not mark the word as stopped, and blocks the
ordinary cross-boundary rule. If the caller explicitly stops on the first
word, the selector is inactive and both values give the same normal waqf
result.

## Warsh boundary choices

| ID | Options and default | Scope and examples | Effect | Source |
| --- | --- | --- | --- | --- |
| `kitabiyah_inni` | `tahqiq`, `naql`; default `tahqiq` | `كِتَابِيَهْ إِنِّي`, 69:19 -> 69:20; wasl only | Preserves final haa and the following qata hamza, or transfers the kasra to haa and removes the hamza onset. | [Al-Wafi, the two linked passages](https://islamweb.net/ar/library/index.php?ID=18&bk_no=245) |
| `article_ibtidaa` | `hamza`, `lam`; default `hamza` | Beginning at `ٱلِاسْمُ` or at an internal-naql article such as `ٱلْأَرْض`, `ٱلْآخِرَة`, or `ٱلْأُولَى`; ibtidaa only | At every site, begins with hamzat al-wasl before the vowel-bearing lam or directly on that lam. At the naql sites, naql remains in force and qata hamza is never restored. The internal hamza of `ٱلِاسْمُ` remains deleted under both choices. | [Al-Nashr, al-ism and article starts after naql](https://www.islamweb.net/ar/library/content/70/114/) |

`kitabiyah_inni` and the shared `maliyah_halak` selector are independent. All
four combinations are legal API selections even though transmitted route
profiles commonly correlate the two passages.

## Warsh hamza choices

### General hamza meetings

| ID | Options and default | Scope and examples | Effect | Source |
| --- | --- | --- | --- | --- |
| `hamza_dhat_fath` | `ibdal`, `tashil`; default `ibdal` | Ordinary two-hamza forms inside one word when the second hamza is open, such as `ءَأَنذَرْتَهُمْ`; all states | Replaces the second hamza with alif, or eases it. Fixed exceptions below are excluded. | [Al-Nashr, two hamzas in one word](https://www.islamweb.net/ar/library/content/70/103/) |
| `hamza_muttafiq` | `ibdal`, `tashil`; default `ibdal` | Two qata hamzas across words with matching vowels, such as `جَاءَ أَحَدٌ`, `أَوْلِيَاءُ أُولَئِكَ`, and `ٱلنِّسَاءِ إِلَّا`; wasl only | Replaces or eases the second hamza. `jaa_aal` and `hamza_kasr_yaa` own their narrower sites. | [Al-Nashr, matching hamzas across words](https://www.islamweb.net/ar/library/content/70/107/) |
| `hamza_damm_kasr` | `ibdal`, `tashil`; default `ibdal` | Two qata hamzas across words where the first is damm and the second is kasr, such as `يَا زَكَرِيَّاءُ إِنَّا`; wasl only | Replaces the second hamza with a kasra-bearing waw, or eases it toward yaa. | [Al-Wafi, differing-vowel hamzas](https://islamweb.net/ar/library/content/245/16/) |
| `jaa_aal` | `ibdal`, `tashil`; default `tashil` | `جَاءَ آلُ لُوطٍ`, 15:61, and `جَاءَ آلُ فِرْعَوْنَ`, 54:41; wasl only | Applies the matching-hamza choice at the two sites whose project-selected default differs from the general default. | [Al-Nashr, the two-site subcase](https://www.islamweb.net/amp/ar/library/content/70/109/) |

At a stop before an across-word meeting, or when beginning at its second word,
the full qata hamza is restored and the selector is inactive.

### Lexical and start-specific hamza

| ID | Options and default | Scope and examples | Effect | Source |
| --- | --- | --- | --- | --- |
| `hamza_arayta` | `ibdal`, `tashil`; default `ibdal`, the face the mushaf prints as `اَرَٰٓيْتَ` | All 34 `أَرَءَيْت` family tokens; all states | Eases or replaces the internal hamza. At a complete stop on a bare unsuffixed form, `ibdal` falls back to tashil to avoid three consecutive sukuns. | [Al-Nashr, the lexical family](https://islamweb.net/ar/library/content/70/111/), [waqf restriction](https://islamweb.net/ar/library/content/70/112/) |
| `ha_antum` | `hadhf`, `ibdal`, `ithbat`; default `ibdal`, the face the mushaf prints as `هَآنتُمْ` | The four `هَٰأَنتُمْ` forms at 3:66, 3:119, 4:109, and 47:38; all states | Omits the separator alif with an eased hamza, replaces the hamza with alif, or retains the separator alif with an eased hamza. | [Al-Nashr, all three faces](https://islamweb.net/ar/library/content/70/111/) |
| `hamza_kasr_yaa` | `ibdal`, `tashil`, `yaa`; default `ibdal` | `هَؤُلَاءِ إِن` at 2:31 and `ٱلْبِغَاءِ إِن` at 24:33; wasl only | Replaces or eases the second hamza, or realizes a consonantal yaa with kasra. The `yaa` value is not a long-vowel choice. | [Al-Wafi, the two exceptional boundaries](https://islamweb.net/ar/library/content/245/16/) |
| `hamza_aimma` | `tashil`, `ibdal`; default `tashil` | All five `أَئِمَّة` tokens; all states | Eases the second hamza toward yaa, or replaces it with a moving yaa. | [Al-Nashr, the five forms](https://islamweb.net/ar/library/content/70/105/) |
| `allai_waqf` | `tashil`, `ibdal_yaa`; default `tashil` | The four `اللائي` forms at 33:4, 58:2, and twice at 65:4; waqf only | `tashil` retains the eased kasra-bearing hamza with rawm; `ibdal_yaa` replaces it with a sakin yaa. In continuation, tashil is fixed and the deleted final yaa leaves a short kasra. The transmitted qasr/madd faces do not create additional values because duration counts are outside the sound-length model. | [Al-Wafi, continuation and three waqf faces](https://www.islamweb.net/ar/library/content/245/68/) |

The closed hamza registers are:

- `hamza_arayta`: 6:40, 6:46, 6:47, 10:50, 10:59, 11:28, 11:63,
  11:88, 17:62, 18:63, 19:77, 25:43, 26:75, 26:205, 28:71, 28:72,
  35:40, 39:38, 41:52, 45:23, 46:4, 46:10, 53:19, 53:33, 56:58,
  56:63, 56:68, 56:71, 67:28, 67:30, 96:9, 96:11, 96:13, and
  107:1. The bare-form waqf fallback applies at 18:63, 19:77, 25:43,
  26:205, 45:23, 53:33, 96:9, 96:11, 96:13, and 107:1.
- `hamza_aimma`: 9:12, 21:73, 28:5, 28:41, and 32:24.

## Warsh inclination choices

`fath` retains the ordinary open vowel. `taqlil` selects the first-class
intermediate inclination. Imala kubra is not used as an option value in these
selectors.

The `رأى` short-taqlil behavior is fixed rather than a choice. At the 16
tokens followed by a moving sound, both the raa's short vowel and the
hamza/alif long vowel are taqlil. At the six tokens followed by a
following-word sakin (Warsh public references 6:78, 6:79, 16:85, 16:86,
18:52, and 33:22), ordinary fath is realized on both nuclei in wasl and both
taqlil qualities return at waqf. `taqlil_short` affects only the short IPA
token; it does not alter this boundary law or raa tarqiq.

### General and lexical inclination

| ID | Options and default | Scope and examples | Effect | Source |
| --- | --- | --- | --- | --- |
| `dhat_yaa` | `fath`, `taqlil`; default `taqlil` | Ordinary yaa-origin final alifs, such as `هُدَى` and `ٱشْتَرَى`; all states, except scopes owned below | Selects fath or taqlil for the target vowel. | [Al-Wafi, dhat al-yaa](https://www.islamweb.net/amp/ar/library/content/245/28/) |
| `arakahum` | `fath`, `taqlil`; default `taqlil` | `أَرَاكَهُمْ`, 8:43; all states | Selects the inclined vowel in this lexical exception. | [Al-Nashr, lexical inclination](https://islamweb.net/ar/library/content/70/162/) |
| `al_jar` | `fath`, `taqlil`; default `taqlil` | Both `ٱلْجَارِ` forms in 4:36; all states | Selects the vowel before the final raa. | [Al-Nashr, al-jar](https://islamweb.net/ar/library/content/70/166/) |
| `jabbarin` | `fath`, `taqlil`; default `taqlil` | `جَبَّارِينَ`, 5:22 and 26:130; all states | Selects the vowel before raa in the two forms. | [Al-Nashr, jabbarin](https://islamweb.net/ar/library/content/70/166/) |
| `haa_verse_heads` | `fath`, `taqlil`; default `fath` | The 25 eligible verse endings on pronominal haa (`-ha`), including `بَنَاهَا`, `ضُحَاهَا`, `مُرْسَاهَا`, `وَتَقْوَاهَا`, and `وَسُقْيَاهَا`: 79:27-32, 79:42, 79:44-46, and 91:1-15; all states | Selects the ending vowel. `ذِكْرَاهَا` at 79:43 is excluded and fixed taqlil. | [Al-Nashr, pronominal-haa verse heads](https://www.islamweb.net/ar/library/content/70/164/) |

### Opening letters and coupled lam

| ID | Options and default | Scope and examples | Effect | Source |
| --- | --- | --- | --- | --- |
| `maryam_haa_yaa` | `taqlil`, `fath`; default `taqlil` | Haa and Yaa of `كهيعص`, 19:1; all states | Selects both opening letters as one transmitted pair. | [Al-Nashr, opening-letter inclination](https://www.islamweb.net/ar/library/content/70/169/) |
| `yaseen_yaa` | `fath`, `taqlil`; default `fath` | Yaa of `يس`, 36:1; all states | Selects the Yaa vowel quality. The final Seen-noon is fixed idgham in Warsh and is independent. | [Al-Nashr, opening-letter inclination](https://www.islamweb.net/ar/library/content/70/169/) |
| `lam_dhat_yaa` | `fath_tafkheem`, `taqlil_tarqiq`; default `fath_tafkheem` | Seven non-verse-head sad-lam forms, including `مُصَلًّى`, `يَصْلَاهَا`, `تَصْلَى`, and `سَيَصْلَى`: 2:125, 17:18, 84:12, 87:12, 88:4, 92:15, and 111:3 | Couples the only compatible vowel and lam outcomes. At `مُصَلًّى` and `يَصْلَى ٱلنَّارَ`, wasl masks the selection and realizes `fath_tafkheem`; the selected value manifests again at waqf. | [Al-Nashr, coupled inclination and lam](https://www.islamweb.net/ar/library/content/70/190/) |
| `lam_verse_heads` | `taqlil_tarqiq`, `fath_tafkheem`; default `taqlil_tarqiq` | `صَلَّى` verse heads at 75:31, 87:15, and 96:10; all states | Couples the target vowel with the compatible lam weight. | [Al-Nashr, coupled verse-head faces](https://www.islamweb.net/ar/library/content/70/190/), [Shatibiyya profile](https://www.islamweb.com/ar/library/content/245/31/) |

Taha has no selector. Its Haa is an imala-kubra site. Enabling the `imala`
extra phoneme renders kubra; disabling it uses the Warsh taqlil fallback while
preserving the typed imala fact and rule.

## Warsh lam choices

`tafkheem` is the shared public heavy-coloring rule. When the lam is what
gives its following fatha or alif an emphatic quality, that vowel follows the
selected lam: `tafkheem` makes both emphatic and `tarqiq` makes both plain. An
independent emphasis cause is not removed.

| ID | Options and default | Scope and examples | Effect | Source |
| --- | --- | --- | --- | --- |
| `lam_separated_by_alif` | `tafkheem`, `tarqiq`; default `tafkheem` | The five alif-separated forms `فِصَالًا`, `يُصَالِحَا`, `أَفَطَالَ`, `طَالَ`, and `فَطَالَ` at 2:233, 4:128, 20:86, 21:44, and 57:16; all states | Selects lam weight despite the separating alif. | [Al-Nashr, disputed lam scopes](https://www.islamweb.net/ar/library/content/70/190/) |
| `lam_final_waqf` | `tafkheem`, `tarqiq`; default `tafkheem` | `يُوصَلَ` at 2:27, 13:21, and 13:25; `فَصَلَ` at 2:249; `فَصَّلَ` at 6:119; `وَبَطَلَ` at 7:118; `ظَلَّ` at 16:58 and 43:17; and `وَفَصْلَ` at 38:20; waqf only | Selects the final lam at a complete stop. `طَالَ` belongs to `lam_separated_by_alif`. | [Al-Nashr, final lam at waqf](https://www.islamweb.net/ar/library/content/70/190/) |
| `lam_after_taa` | `tarqiq`, `tafkheem`; default `tafkheem` | Ordinary qualifying taa followed by open lam, such as `مَطْلَعِ`; all sounded states, with terminal waqf owned above | Selects the broader authenticated tarqiq face or the prevalent tafkheem face. Narrow lexical route splits remain within this one consumer scope. | [Al-Nashr, taa-lam routes](https://www.islamweb.net/ar/library/content/70/190/) |
| `lam_after_zhaa` | `tarqiq`, `tafkheem`; default `tafkheem` | Ordinary qualifying zhaa followed by open lam, such as `يُظْلَمُونَ`; all sounded states, with terminal waqf owned above | Selects the broader authenticated tarqiq face or the prevalent tafkheem face. Open-versus-sakin route splits remain within this one consumer scope. | [Al-Nashr, zhaa-lam routes](https://www.islamweb.net/ar/library/content/70/190/) |
| `lam_salsal` | `tarqiq`, `tafkheem`; default `tarqiq` | The first lam in all four `صَلْصَال` tokens at 15:26, 15:28, 15:33, and 55:14; all states | Selects tarqiq or tafkheem for the medial first lam. | [Al-Nashr, salsal](https://www.islamweb.net/ar/library/content/70/190/) |

Outside these scopes and the coupled inclination selectors, every qualifying
open lam after sad, taa, or zhaa follows the fixed Warsh tafkheem rule. The two
general taa and zhaa selectors expose authenticated broader al-Azraq routes;
their default remains the standard tafkheem face.

## Warsh systematic raa choices

These scopes apply after the normal structural eligibility checks for a raa
preceded by kasra or sakin yaa. Lexical selectors below take precedence.

| ID | Options and default | Scope and boundary behavior | Source |
| --- | --- | --- | --- |
| `raa_fathatan` | `light`, `heavy_wasl`, `heavy`; default `light` | Eligible raa with fathatan, such as `خَيْرًا` and `سِرًّا`. `light` is light in continuation and at stop; `heavy_wasl` is heavy while the ending sounds and light at plain waqf; `heavy` is heavy in both. The five-word set and `raa_sihra` are excluded. | [Al-Nashr, open and fathatan raa](https://www.islamweb.net/ar/library/content/70/182/) |
| `raa_damma` | `light`, `heavy`; default `light` | Eligible raa with damma or dammatan, such as `خَيْرٌ`. A medial raa keeps the selection in all states. A word-final raa uses the selection while its vowel sounds and becomes fixed light at plain waqf. | [Al-Nashr, damma raa](https://www.islamweb.net/ar/library/content/70/185/) |
| `raa_ishruna_kibr` | `light`, `heavy`; default `light` | `عِشْرُونَ`, 8:65, and `كِبْرٌ`, 40:56. The first is medial; the final raa in `كِبْرٌ` follows the ordinary pausal result. | [Al-Nashr, the grouped exception](https://www.islamweb.net/ar/library/content/70/185/) |

## Warsh lexical raa choices

| ID | Options and default | Scope and examples | Boundary behavior | Source |
| --- | --- | --- | --- | --- |
| `raa_alishraq` | `heavy`, `light`; default `heavy` | `وَٱلْإِشْرَاقِ`, 38:18 | All states | [Al-Nashr, lexical raa](https://www.islamweb.net/ar/library/content/70/183/) |
| `raa_hayran` | `heavy`, `light`; default `heavy` | `حَيْرَانَ`, 6:71 | All states | [Al-Wafi, both faces](https://islamweb.net/ar/library/index.php?ID=26&bk_no=245&idfrom=30&idto=30&page=bookcontents_ver3) |
| `raa_bisharar` | `light`, `heavy`; default `light` | `بِشَرَرٍ`, 77:32 | In continuation, controls the first raa and the second remains light. At plain waqf, both raas follow the selected face. | [Al-Nashr, bisharar](https://www.islamweb.net/ar/library/content/70/184/) |
| `raa_five_words` | `heavy`, `light`; default `heavy` | All `ذِكْرًا`, `سِتْرًا`, `إِمْرًا`, `وِزْرًا`, and `حِجْرًا` forms in the transmitted set | All states | [Al-Nashr, the five-word set](https://www.islamweb.net/ar/library/content/70/182/) |
| `raa_sihra` | `heavy`, `light`; default `heavy` | `صِهْرًا`, 25:54 | All states; separate because an authenticated route keeps the five-word set heavy but makes this raa light | [Al-Nashr, sihra split](https://www.islamweb.net/ar/library/content/70/182/) |
| `raa_iram` | `heavy`, `light`; default `heavy` | `إِرَمَ`, 89:7 | All states | [Al-Nashr, lexical raa](https://islamweb.net/ar/library/content/70/183/) |
| `raa_alif_ayn` | `light`, `heavy`; default `light` | `ذِرَاعَيْهِ`, `سِرَاعًا`, and `ذِرَاعًا` at 18:18, 50:44, 70:43, and 69:32 | All states | [Al-Nashr, lexical raa](https://islamweb.net/ar/library/content/70/183/) |
| `raa_alif_hamza` | `light`, `heavy`; default `light` | The two `ٱفْتِرَاءً` forms at 6:138 and 6:140, and `مِرَاءً` at 18:22 | All states | [Al-Nashr, raa before alif and hamza](https://islamweb.net/ar/library/content/70/183/) |
| `raa_dual_alif` | `light`, `heavy`; default `light` | `طَهِّرَا`, `لَسَاحِرَانِ`, `سَاحِرَانِ`, and `تَنتَصِرَانِ` at 2:125, 20:63, 28:48, and 55:35 | All states | [Al-Nashr, dual-alif raa](https://islamweb.net/ar/library/content/70/183/) |
| `raa_ashiratukum` | `light`, `heavy`; default `light` | Only `وَعَشِيرَتُكُمْ`, 9:24; other forms in the family are fixed light | All states | [Al-Nashr, the Tawbah exception](https://www.islamweb.net/ar/library/content/70/183/) |
| `raa_wizraka` | `light`, `heavy`; default `light` | `وِزْرَكَ`, 94:2 | All states | [Al-Nashr, lexical raa](https://www.islamweb.net/ar/library/content/70/183/) |
| `raa_dhikraka` | `light`, `heavy`; default `light` | `ذِكْرَكَ`, 94:4 | All states; independent from `raa_wizraka` | [Al-Nashr, lexical raa](https://www.islamweb.net/ar/library/content/70/183/) |
| `raa_wizra_ukhra` | `light`, `heavy`; default `light` | The five `وِزْرَ أُخْرَى` boundaries at 6:164, 17:15, 35:18, 39:7, and 53:38 | Wasl only. Stopping on `وِزْرَ` is fixed light; inclination in `أُخْرَى` is independent. | [Al-Nashr, wizra ukhra](https://www.islamweb.net/ar/library/content/70/183/) |
| `raa_ijrami` | `light`, `heavy`; default `light` | `إِجْرَامِي`, 11:35 | All states | [Al-Nashr, lexical raa](https://www.islamweb.net/ar/library/content/70/183/) |
| `raa_hidhrakum` | `light`, `heavy`; default `light` | The two `حِذْرَكُمْ` forms at 4:71 and 4:102. `حِذْرَهُمْ` is fixed light. | All states | [Al-Nashr, hidhrakum](https://www.islamweb.net/ar/library/content/70/183/) |
| `raa_ibrah_kibrahu` | `light`, `heavy`; default `light` | `عِبْرَة` and `لَعِبْرَة` at 3:13, 12:111, 16:66, 23:21, 24:44, and 79:26, plus `كِبْرَهُ` at 24:11 | All states; one consumer selector intentionally groups narrower transmitted subpatterns | [Al-Nashr, ibrah and kibrahu](https://www.islamweb.net/ar/library/content/70/183/) |
| `raa_hasirat_suduruhum` | `light`, `heavy`; default `light` | `حَصِرَتْ صُدُورُهُمْ`, 4:90 | Wasl only. Stopping on `حَصِرَتْ` is fixed light; starting at `صُدُورُهُمْ` has no target raa. | [Al-Nashr, hasirat suduruhum](https://www.islamweb.net/ar/library/content/70/183/) |

The exact `raa_five_words` register is:

- `ذِكْرًا`: 2:200, 18:70, 18:83, 20:99, 20:113, 21:48, 33:41,
  37:3, 37:168, 65:10, and 77:5;
- `سِتْرًا`: 18:90;
- `إِمْرًا`: 18:71;
- `وِزْرًا`: 20:100; and
- `حِجْرًا`: 25:22 and 25:53.

## Fixed facts that are not selectors

The following distinctions are deliberately outside the variant API:

- Madd counts, leen counts, silah counts, and count-dependent face matrices do
  not alter this phonemizer's sound-length model. [Warsh count catalogue and
  sources](warsh/research/v2/madd-counts.md)
- `imala` is an extra-phoneme rendering control. `tashil` is such a control
  only for Hafs; Warsh always renders its typed eased hamza as `ʔ̞`. Neither
  changes the typed sound feature or named rule. [Phoneme and rule
  contract](warsh/research/v2/phoneme-rule-inventory.md)
- Warsh pair assimilation is fixed, as the selected script writes it: the dal
  of `قَد` merges into dad and zaa, feminine taa into zaa, and the dhal of the
  `أخذ` family into taa (`اَ۪تَّخَذتُّمُ`, but not `فَنَبَذْتُهَا` or `عُذْتُ`).
  `يَلْهَثْ ذَٰلِكَ`, `اِ۪رْكَبْ مَعَنَا`, and `وَيُعَذِّبْ مَنْ` keep izhar,
  so the Hafs `yalhath_dhalik` and `irkab_maana` selectors have no Warsh face.
  Fixed izhar at `يَلْهَثْ ذَٰلِكَ` is the Shatibiyya path; al-Nashr also
  reports an idgham face for al-Azraq. [Pair-assimilation
  register](warsh/research/v2/pair-assimilation.md)
- Warsh Yaseen-noon is fixed idgham, the Shatibiyya path; al-Nashr gives
  al-Azraq a khulf with izhar from al-Tajrid. [Al-Wafi, opening-letter
  junctions](https://www.islamweb.net/amp/ar/library/content/245/26/),
  [Al-Nashr](https://www.islamweb.net/ar/library/content/70/149/)
- Taha is fixed imala kubra. [Al-Nashr, opening-letter
  inclination](https://www.islamweb.net/ar/library/content/70/169/)
- The triple-hamza forms `أَءَالِهَتُنَا` and `أَءَامَنتُم`, and
  `ءَأَعْجَمِيٌّ`, use fixed tashil and are excluded from
  `hamza_dhat_fath`. [Al-Nashr, the fixed
  exceptions](https://www.islamweb.net/ar/library/content/70/103/)
- Hafs `نَخْلُقكُّم` at 77:20 always uses complete qaf-to-kaf
  `idgham_mutaqaribayn` in the supported Shatibiyya and Tayyiba paths. The
  commonly taught incomplete face is a general tajwid or other-transmission
  choice, not a Hafs selector in those paths. [Hafs-chain audit and
  explanation](https://baheth.ieasybooks.com/en/media/%D8%AD%D9%83%D9%85-%D9%82%D8%B1%D8%A7%D8%A1%D8%A9-%D9%83%D9%84%D9%85%D8%A9-%D9%86%D8%AE%D9%84%D9%82%D9%83%D9%85-%D9%88%D8%A5%D8%AF%D8%BA%D8%A7%D9%85%D9%87%D8%A7-%D8%AF-%D8%A3%D9%8A%D9%85%D9%86-%D8%B3%D9%88%D9%8A%D8%AF),
  [Al-Nashr scan, p. 91](https://www.islamland.com/uploads/books/ar_AnNshr.pdf)
- Warsh isqat spellings contain no sounded hamza and emit no isqat rule.
  [Al-Wafi, single-hamza omissions](https://www.islamweb.net/ar/library/content/245/17/)
- The two leen-mahmuz exclusions `مَوْئِلًا` and `ٱلْمَوْءُودَةُ` are fixed
  classifier exceptions, not variants. [Al-Wafi and the exact selected-script
  register](warsh/research/v2/madd-leen-mahmuz.md)
- Ordinary naql is fixed structural boundary behavior unless a selector above
  explicitly names a local choice. [Al-Wafi, naql](https://islamweb.net/ar/library/index.php?ID=18&bk_no=245&flag=1&page=bookcontents), [implementation register](warsh/research/v2/naql.md)
- Mim al-jam' is fixed structural boundary behavior. [Domain and selected
  script register](warsh/research/v2/mim-al-jam.md)
- Yaa zawaid are fixed lexical and boundary facts. [Domain and selected
  script register](warsh/research/v2/yaa-zawaid.md)
- Outside the explicit `salasila_waqf` choice above, the seven alifs are fixed
  lexical and boundary facts. [Domain and selected script
  matrix](warsh/research/v2/seven-alifs.md)
- Surah-transition modes such as optional takbir or inserted basmala are
  outside the passage-boundary selector API.
- Rejected solitary reports and micro-route splits collapsed into a broader
  selector do not create extra public values.

These exclusions keep the API focused on meaningful sound and rule choices
without encoding duration matrices or historical route bundles.

## Implementation discipline for another riwayah

Before implementing Warsh selectors, reconcile the complete catalogue against
the research: IDs, option order, defaults, scopes, display names, descriptions,
and fixed exclusions. Display names should mirror the public IDs. Descriptions
should add only information the name does not already convey.

Specify each face across every layer it changes before writing rules: canonical
reading, source and cell shape, performed sounds, rule ownership, mergers, and
boundary activation. A phoneme-only implementation is valid only when the
written and canonical cell realization is proved unchanged. Otherwise the face
must explicitly insert, replace, silence, split, drop, or merge the affected
cells.

Tests follow the semantic ownership rules in `tests/README.md`. Add a variant
face to the existing rule or lexical-family case that owns it, including shared
riwayah coverage where appropriate. Do not create a selector-named test file
when the behavior belongs in an existing file, and do not duplicate the same
Quran site in multiple semantic suites. Every face must assert its boundary
masking, cell transformation, phonemes, and relevant present or absent rules.
