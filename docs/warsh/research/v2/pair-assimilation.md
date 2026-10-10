# Pair assimilation

This document owns the adjacent-consonant pairs where Warsh through al-Azraq
differs from Hafs in idgham mutajanisayn and mutaqaribayn: the dal of `قد`,
feminine taa, the dhal of `إذ`, the dhal of the `أخذ` family, and the three
sakin-letter junctions that Hafs merges by default or by selector. It does not
own noon and tanwin, plural mim, lam al-tarif, or the agreed idgham that the
two readings share.

None of these Warsh results is a public choice. The Hafs selectors
`yalhath_dhalik` and `irkab_maana` remain Hafs-only; their values and defaults
are in [`docs/variants.md`](../../../variants.md).

## Sources

The Shatibiyya route is taken from al-Wafi, chapters 21 to 26 on islamweb
([W21 dhal of idh](https://www.islamweb.net/ar/library/content/245/21/),
[W22 dal of qad](https://www.islamweb.net/ar/library/content/245/22/),
[W23 feminine taa](https://www.islamweb.net/ar/library/content/245/23/),
[W24 lam of hal and bal](https://www.islamweb.net/ar/library/content/245/24/),
[W25 agreed idgham](https://www.islamweb.net/ar/library/content/245/25/),
[W26 close-articulation letters](https://www.islamweb.net/ar/library/content/245/26/)).
The Tayyiba cross-check is al-Nashr, islamweb book 70, pages 131 to 152
(cited as N followed by the page, for example
[N132](https://www.islamweb.net/ar/library/content/70/132/)).

The selected King Fahd Warsh script writes exactly the faces below at every
site: a merged pair has a bare first letter and a shadda on the second, and an
izhar pair keeps the sukun on the first.

## Differences from Hafs

| Family | Hafs | Warsh | Evidence |
| --- | --- | --- | --- |
| Dal of `قد` before dad and zaa | Izhar | Idgham, fixed | W22 `وأدغم ورش ضر ظمآن وامتلا`; [N132](https://www.islamweb.net/ar/library/content/70/132/) `وأدغمها ورش في الضاد والظاء` |
| Dal of `قد` before jim, sad, sin, dhal, shin, zay | Izhar | Izhar | W22; N132 |
| Feminine taa before zaa | Izhar | Idgham, fixed | W23 `وأدغم ورش ظافرا ومخولا`; [N133](https://www.islamweb.net/ar/library/content/70/133/) `وأدغمها الأزرق عن ورش في الظاء فقط` |
| Dhal of `إذ` before taa, dal, zay, sin, sad, jim | Izhar | Izhar | W21; [N131](https://www.islamweb.net/ar/library/content/70/131/) |
| Dhal of the `أخذ` family before taa | Izhar | Idgham, fixed | W26 `وقرأ حفص وابن كثير بإظهار الذال عند التاء`; [N143](https://www.islamweb.net/ar/library/content/70/143/) |
| `نبذتها`, `عذت` | Izhar | Izhar | W26; [N144](https://www.islamweb.net/ar/library/content/70/144/), [N145](https://www.islamweb.net/ar/library/content/70/145/) |
| `يلهث ذلك`, 7:176 | Selector, default idgham | Izhar, fixed on the Shatibiyya path | W26 `وابن كثير وورشا أظهروا الثاء عند الذال`; [N142](https://www.islamweb.net/ar/library/content/70/142/) |
| `اركب معنا`, 11:42 | Selector, default idgham | Izhar, fixed | W26 `وقرأ ابن عامر وخلف وورش بالإظهار قولا واحدا`; [N137](https://www.islamweb.net/ar/library/content/70/137/) |
| `ويعذب من`, 2:284 | No meeting: Hafs reads damm | Izhar, fixed | W26 `وورش بلا خلف`; [N136](https://www.islamweb.net/ar/library/content/70/136/) `بالإظهار وجها واحدا وهو ورش وحده` |

Nafi' reads `ويعذب` with jazm, so the baa-meem meeting exists only in Warsh.
At 11:42 the lone idgham report in al-Nashr is through al-Asbahani, not
al-Azraq, so no Tayyiba face reaches this route.

The following agree with Hafs and need no Warsh data: `لبثت` and `لبثتم`,
`أورثتموها`, `يرد ثواب`, the opening-letter junction `كهيعص ذكر`, the
`طسم` idgham, jazm baa into faa, raa into lam, `نخسف بهم`, `يفعل ذلك`, the lam
of `هل` and `بل` (W24), the agreed idgham (W25), and complete idgham in
`نخلقكم` ([N152](https://www.islamweb.net/ar/library/content/70/152/)).
`بل ران` and `من راق` carry the Hafs-only sakt; Warsh merges them. `ماليه
هلك` keeps two faces for every reader.

## Shatibiyya and Tayyiba

Two Warsh results here are Shatibiyya choices where al-Nashr records a khulf
for al-Azraq:

- `يلهث ذلك`: al-Nashr reports izhar from the majority and an idgham report
  through al-Khuzai via al-Azraq (N142). Fixed izhar is the Shatibiyya path.
- `يس والقرآن`: the Shatibiyya gives Warsh fixed idgham; al-Nashr gives
  al-Azraq both faces, with izhar from al-Tajrid
  ([N149](https://www.islamweb.net/ar/library/content/70/149/)).

`ن والقلم` is a khulf for Warsh in both books and stays the existing
`noon_wasl` selector ([N150](https://www.islamweb.net/ar/library/content/70/150/)).

## Selected-script register

Counts are over the selected King Fahd Warsh corpus. Source refs use its
numbering; canonical refs are the cross-script identity.

| Family | Result | Count |
| --- | --- | ---: |
| Dal of `قد` before dad | Idgham | 14 |
| Dal of `قد` before zaa | Idgham | 3 |
| Dal of `قد` before the other six | Izhar | 82: jim 57, sad 11, sin 11, dhal 1, shin 1, zay 1 |
| Feminine taa before zaa | Idgham | 3 |
| Dhal of `إذ` before the six | Izhar | 42: jim 17, taa 16, dal 4, zay 2, sin 2, sad 1 |
| `أخذ` family dhal before taa | Idgham | 18 |
| `نبذتها`, `عذت` | Izhar | 3 |
| `يلهث ذلك`, `اركب معنا`, `ويعذب من` | Izhar | 3 |

The 38 merged sites are:

| Family | Selected source refs | Canonical refs |
| --- | --- | --- |
| `قد` + dad | 2:107:15-16; 4:115:17-18; 4:135:25-26; 4:166:8-9; 5:13:42-43; 5:79:14-15; 6:57:15-16; 6:141:16-17; 7:149:7-8; 30:57:1-2; 33:36:21-22; 37:71:1-2; 39:26:1-2; 60:1:45-46 | 2:108:15-16; 4:116:17-18; 4:136:25-26; 4:167:8-9; 5:12:42-43; 5:77:14-15; 6:56:15-16; 6:140:16-17; 7:149:7-8; 30:58:1-2; 33:36:21-22; 37:71:1-2; 39:27:1-2; 60:1:45-46 |
| `قد` + zaa | 2:229:18-19; 38:23:2-3; 65:1:31-32 | 2:231:18-19; 38:24:2-3; 65:1:31-32 |
| Taa + zaa | 6:139:13-14; 6:147:16-17; 21:11:5-6 | 6:138:13-14; 6:146:16-17; 21:11:5-6 |
| `أخذ` dhal + taa | 2:50:7; 2:79:9; 2:91:6; 3:80:22; 8:69:8; 11:92:8; 13:17:9; 13:33:10; 18:76:22; 22:42:8; 22:46:9; 23:111:1; 25:27:8; 26:28:3; 29:24:3; 35:26:2; 40:4:18; 45:34:3 | 2:51:7; 2:80:9; 2:92:6; 3:81:22; 8:68:8; 11:92:8; 13:16:9; 13:32:10; 18:77:22; 22:44:8; 22:48:9; 23:110:1; 25:27:8; 26:29:3; 29:25:3; 35:26:2; 40:5:18; 45:35:3 |

The izhar exceptions are `فَنَبَذْتُهَا` (source 20:94:12, canonical
20:96:12), `عُذْتُ` (source 40:27:4 and 44:19:2, canonical 40:27:4 and
44:20:2), `يَلْهَثْ ذَٰلِكَ` (7:176:20-21 in both), `اِ۪رْكَبْ مَعَنَا`
(11:42:14-15 in both), and `وَيُعَذِّبْ مَنْ` (source 2:283:21-22, canonical
2:284:21-22).

Representative joined results:

| Site | Selected source and refs | Canonical refs | Joined result span |
| --- | --- | --- | --- |
| `قد` + dad | `فَقَد ضَّلَّ`, 2:107:15-16 | 2:108:15-16 | `f a q a dˤdˤ a ll a` |
| `قد` + zaa | `فَقَد ظَّلَمَ`, 2:229:18-19 | 2:231:18-19 | `f a q a ðˤðˤ a lˤ a m a` |
| Taa + zaa | `كَانَت ظَّالِمَةٗ`, 21:11:5-6 | 21:11:5-6 | `k a: n a ðˤðˤ aˤ: l i m a t a` |
| `أخذ` dhal + taa | `اَ۪تَّخَذتُّمُ`, 2:50:7 | 2:51:7 | `tt a x a tt u m u` |
| Izhar | `يَلْهَثْ ذَٰلِكَ`, 7:176:20-21 | 7:176:20-21 | `j a l h a θ ð a: l i k a` |

## Implementation contract

- The Warsh pair table overrides the shared table as a whole. It adds dal into
  dad, dal into zaa, taa into zaa, and dhal into taa as
  `idgham_mutaqaribayn`, and omits baa into meem and thaa into dhal.
- Dhal into taa is stem-scoped: it fires only after kha in the same word, so
  `أخذ` and `اتخذ` merge while `نبذ` and `عاذ` keep izhar. `إذ` before taa is a
  word boundary and never matches.
- The cross-word pairs merge only in joined speech. A stop on `قد` restores
  the dal with qalqala, and a start on the second word begins with its own
  consonant.
- Hafs output is unchanged.
