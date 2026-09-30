from __future__ import annotations

import pytest

from tests.support import Case, R, Site, assert_case, case_runs, pick, through

CASES = (
    # Hafs: ٱللَّهِ ٱلرَّحْمَـٰنِ
    # Warsh: اِ۬للَّهِ اِ۬لرَّحْمَٰنِ
    Case(id="lam-raa", site=Site(
             hafs=("1:1", (2, 3)), warsh=("27:30", (6, 7))), read=through(),
         phonemes=("ʔ a lˤlˤ aˤ: h i", "rˤrˤ aˤ ħ m a: n"),
         char_rules={"ل[1]": R("lam_shamsiyyah"),
                     "ل[3]": R("lam_shamsiyyah")},
         sound_rules={"lˤlˤ": R("lam_shamsiyyah"), "rˤrˤ": R("lam_shamsiyyah")}),
    # Hafs: وَٱلنَّصَـٰرَىٰ وَٱلصَّـٰبِـِٔينَ
    # Warsh: وَالنَّصَٰر۪ىٰ وَالصَّٰبِينَ
    Case(id="noon-sad", site=Site.shared("2:62", (6, 7)), read=through(),
         phonemes=pick(
             hafs=("w a ñ a sˤ aˤ: rˤ aˤ:", "w a sˤsˤ aˤ: b i ʔ i: n"),
             warsh=("w a ñ a sˤ aˤ: r ɛ:", "w a sˤsˤ aˤ: b i: n"),
         ),
         char_rules={"ل[1]": R("lam_shamsiyyah"),
                     "ل[2]": R("lam_shamsiyyah")},
         sound_rules={"ñ": R("lam_shamsiyyah"), "sˤsˤ": R("lam_shamsiyyah")}),
    # Hafs: ٱلزَّادِ ٱلتَّقْوَىٰ ۖ
    # Warsh: اَ۬لزَّادِ اِ۬لتَّقْو۪ىٰۖ
    Case(id="zay-taa", site=Site.shared("2:197", (25, 26)), read=through(),
         phonemes=pick(
             hafs=("ʔ a zz a: d i", "tt a q Q w a:"),
             warsh=("ʔ a zz a: d i", "tt a q Q w ɛ:"),
         ),
         char_rules={"ل[1]": R("lam_shamsiyyah"),
                     "ل[2]": R("lam_shamsiyyah")},
         sound_rules={"zz": R("lam_shamsiyyah"), "tt": R("lam_shamsiyyah")}),
    # Hafs: ٱلسَّرَّآءِ وَٱلضَّرَّآءِ
    # Warsh: اِ۬لسَّرَّآءِ وَالضَّرَّآءِ
    Case(id="seen-dad", site=Site.shared("3:134", (4, 5)), read=through(),
         phonemes=("ʔ a ss a rˤrˤ aˤ: ʔ i", "w a dˤdˤ aˤ rˤrˤ aˤ: ʔ"),
         char_rules={"ل[1]": R("lam_shamsiyyah"),
                     "ل[2]": R("lam_shamsiyyah")},
         sound_rules={"ss": R("lam_shamsiyyah"), "dˤdˤ": R("lam_shamsiyyah")}),
    # Hafs: وَٱلشَّجَرُ وَٱلدَّوَآبُّ
    # Warsh: وَالشَّجَرُ وَالدَّوَآبُّ
    Case(id="sheen-dal", site=Site.shared("22:18", (17, 18)), read=through(),
         phonemes=("w a ʃʃ a ʒ a rˤ u", "w a dd a w a: bb Q"),
         char_rules={"ل[1]": R("lam_shamsiyyah"),
                     "ل[2]": R("lam_shamsiyyah")},
         sound_rules={"ʃʃ": R("lam_shamsiyyah"), "dd": R("lam_shamsiyyah")}),
    # Hafs: مِنَ ٱلثَّمَرَٰتِ
    # Warsh: مِنَ اَ۬لثَّمَرَٰتِ
    Case(id="tha", site=Site.shared("2:22", (14, 15)), read=through(),
         phonemes=("m i n a", "θθ a m a rˤ aˤ: t"),
         char_rules={"ل": R("lam_shamsiyyah")},
         sound_rules={"θθ": R("lam_shamsiyyah")}),
    # Hafs: مِنَ ٱلظَّـٰلِمِينَ
    # Warsh: مِنَ اَ۬لظَّٰلِمِينَۖ
    Case(id="zhaa", site=Site.shared("2:35", (17, 18)), read=through(),
         phonemes=("m i n a", "ðˤðˤ aˤ: l i m i: n"),
         char_rules={"ل[1]": R("lam_shamsiyyah")},
         sound_rules={"ðˤðˤ": R("lam_shamsiyyah")}),
    # Hafs: عَلَيْهِمُ ٱلذِّلَّةُ
    # Warsh: عَلَيْهِمُ اُ۬لذِّلَّةُ
    Case(id="thal", site=Site.shared("2:61", (38, 39)), read=through(),
         phonemes=("ʕ a l a j h i m u", "ðð i ll a h"),
         char_rules={"ل[2]": R("lam_shamsiyyah")},
         sound_rules={"ðð": R("lam_shamsiyyah")}),
    # Hafs: فَوْقَكُمُ ٱلطُّورَ
    # Warsh: فَوْقَكُمُ اُ۬لطُّورَۖ
    Case(id="tah", site=Site.shared("2:63", (5, 6)), read=through(),
         phonemes=("f a w q aˤ k u m u", "tˤtˤ u: rˤ"),
         char_rules={"ل": R("lam_shamsiyyah")},
         sound_rules={"tˤtˤ": R("lam_shamsiyyah")}),
)


@pytest.mark.parametrize("run", case_runs(CASES))
def test_lam_shamsiyyah(run):
    assert_case(run)
