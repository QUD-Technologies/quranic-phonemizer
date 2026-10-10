from __future__ import annotations

import pytest

from quranic_phonemizer.model.address import KhilafId
from tests.support import (
    Case,
    Expect,
    R,
    Site,
    StateCase,
    VariantCase,
    assert_case,
    case_runs,
    explicit,
    isolated,
    pick,
    through,
)

CASES = (
    # Hafs: قَد تَّبَيَّنَ
    # Warsh: قَد تَّبَيَّنَ
    StateCase(id="daal-taa", site=Site.shared("2:256", (5, 6)), states={
        "joined": Expect(read=through(), phonemes=("q aˤ", "tt a b a jj a n"),
                         char_rules={"د": R("idgham_mutajanisayn_kamil"),
                                     "ت": R("idgham_mutajanisayn_kamil")},
                         sound_rules={"tt": R("idgham_mutajanisayn_kamil")}),
        "ibtidaa-on-host": Expect(read=explicit(ibtidaa=5, waqf=5),
                          phonemes=("q aˤ d Q", "t a b a jj a n a"),
                          absent_char_rules={"د": R("idgham_mutajanisayn_kamil"),
                                             "ت": R("idgham_mutajanisayn_kamil")}),
    }),
    # Hafs: وَدَّت طَّآئِفَةٌ
    # Warsh: وَدَّت طَّآئِفَةٞ
    Case(id="taa-taa", site=Site.shared("3:69", (1, 2)), read=through(),
         phonemes=("w a dd a", "tˤtˤ aˤ: ʔ i f a h"),
         char_rules={"ت": R("idgham_mutajanisayn_kamil"),
                     "ط": R("idgham_mutajanisayn_kamil")},
         sound_rules={"tˤtˤ": R("idgham_mutajanisayn_kamil")}),
    # Hafs: إِذ ظَّلَمُوٓا۟
    # Warsh: إِذ ظَّلَمُوٓاْ
    Case(id="dhal-zhaa", site=Site.shared("4:64", (11, 12)), read=through(),
         phonemes=pick(
             hafs=("ʔ i", "ðˤðˤ aˤ l a m u:"),
             warsh=("ʔ i", "ðˤðˤ aˤ lˤ aˤ m u:"),
         ),
         char_rules=pick(
             hafs={"ذ": R("idgham_mutajanisayn_kamil"),
                   "ظ": R("idgham_mutajanisayn_kamil")},
             warsh={"ذ": R("idgham_mutajanisayn_kamil"),
                    "ظ": R("idgham_mutajanisayn_kamil"),
                    "ل": R("tafkheem")},
         ),
         sound_rules=pick(
             hafs={"ðˤðˤ": R("idgham_mutajanisayn_kamil")},
             warsh={"ðˤðˤ": R("idgham_mutajanisayn_kamil"),
                    "lˤ": R("tafkheem"), "aˤ[2]": R("tafkheem")},
         )),
    # Hafs: يَلْهَث ۚ ذَّٰلِكَ
    VariantCase(
         id="yalhath-dhalik", site=Site(hafs=("7:176", (20, 21))),
         selector=KhilafId.YALHATH_DHALIK,
         faces={
             "idgham": Expect(read=through(), phonemes=("j a l h a", "ðð a: l i k"),
                 char_rules={"ث": R("idgham_mutajanisayn_kamil"),
                             "ذ": R("idgham_mutajanisayn_kamil")},
                 sound_rules={"ðð": R("idgham_mutajanisayn_kamil")}),
             "izhar": Expect(read=through(), phonemes=("j a l h a θ", "ð a: l i k"),
                 absent_char_rules={"ث": R("idgham_mutajanisayn_kamil")}),
         },
         default="idgham",
         masked=Expect(read=explicit(ibtidaa=20, waqf=20),
                       phonemes=("j a l h a θ", "ð a: l i k a"),
                       absent_char_rules={"ث": R("idgham_mutajanisayn_kamil")}),
    ),
    # Warsh: يَلْهَثْۖ ذَٰلِكَ
    Case(id="thaa-dhal-warsh", site=Site(warsh=("7:176", (20, 21))), read=through(),
         phonemes=("j a l h a θ", "ð a: l i k"),
         absent_char_rules={"ث": R("idgham_mutajanisayn_kamil")}),
    # Hafs: أَثْقَلَت دَّعَوَا
    # Warsh: أَثْقَلَت دَّعَوَا
    Case(id="taa-daal", site=Site.shared("7:189", (20, 21)), read=through(),
         phonemes=("ʔ a θ q aˤ l a", "dd a ʕ a w a:"),
         char_rules={"ت": R("idgham_mutajanisayn_kamil"),
                     "د": R("idgham_mutajanisayn_kamil")},
         sound_rules={"dd": R("idgham_mutajanisayn_kamil")}),
    # Hafs: أَرَدتُّمْ
    Case(id="aradttum", site=Site(hafs=("2:233", (45,))), read=isolated(),
         phonemes="ʔ a rˤ aˤ tt u m",
         char_rules={"د": R("idgham_mutajanisayn_kamil"),
                     "ت": R("idgham_mutajanisayn_kamil")},
         sound_rules={"tt": R("idgham_mutajanisayn_kamil")}),
    # Hafs: رَٰوَدتُّهُۥ
    # Warsh: رَٰوَدتُّهُۥ
    Case(id="rawadttuhu", site=Site.shared("12:32", (7,)), read=isolated(),
         phonemes="rˤ aˤ: w a tt u h",
         char_rules={"د": R("idgham_mutajanisayn_kamil"),
                     "ت": R("idgham_mutajanisayn_kamil")},
         sound_rules={"tt": R("idgham_mutajanisayn_kamil")}),
    # Hafs: أَيَّدتُّكَ
    # Warsh: اَيَّدتُّكَ
    Case(id="ayyadttuka", site=Site.shared("5:110", (13,)), read=isolated(),
         phonemes="ʔ a jj a tt u k",
         char_rules={"د": R("idgham_mutajanisayn_kamil"),
                     "ت": R("idgham_mutajanisayn_kamil")},
         sound_rules={"tt": R("idgham_mutajanisayn_kamil")}),
    # Hafs: رَٰوَدتُّنَّ
    # Warsh: رَٰوَدتُّنَّ
    Case(id="rawadttunna", site=Site.shared("12:51", (5,)), read=isolated(),
         phonemes="rˤ aˤ: w a tt u ñ",
         char_rules={"د": R("idgham_mutajanisayn_kamil"),
                     "ت": R("idgham_mutajanisayn_kamil")},
         sound_rules={"tt": R("idgham_mutajanisayn_kamil")}),
    # Hafs: ٱرْكَب مَّعَنَا
    VariantCase(
         id="irkab-maana", site=Site(hafs=("11:42", (14, 15))),
         selector=KhilafId.IRKAB_MAANA,
         faces={
             "idgham": Expect(read=through(), phonemes=("ʔ i rˤ k a", "m̃ a ʕ a n a:"),
                 char_rules={"ب": R("idgham_mutajanisayn_kamil"),
                             "م": R("idgham_mutajanisayn_kamil")},
                 sound_rules={"m̃": R("idgham_mutajanisayn_kamil")}),
             "izhar": Expect(read=through(), phonemes=("ʔ i rˤ k a b Q", "m a ʕ a n a:"),
                 char_rules={"ب": R("qalqala_sughra")},
                 sound_rules={"Q": R("qalqala_sughra")},
                 absent_char_rules={"ب": R("idgham_mutajanisayn_kamil")}),
         },
         default="idgham",
         masked=Expect(read=explicit(ibtidaa=14, waqf=14),
                       phonemes=("ʔ i rˤ k a b Q", "m a ʕ a n a:"),
                       char_rules={"ب": R("qalqala_kubra")},
                       sound_rules={"Q": R("qalqala_kubra")},
                       absent_char_rules={"ب": R("idgham_mutajanisayn_kamil")}),
    ),
    # Warsh: اِ۪رْكَبْ مَعَنَا
    Case(id="irkab-maana-warsh", site=Site(warsh=("11:42", (14, 15))), read=through(),
         phonemes=("ʔ i rˤ k a b Q", "m a ʕ a n a:"),
         char_rules={"ب": R("qalqala_sughra")},
         sound_rules={"Q": R("qalqala_sughra")},
         absent_char_rules={"ب": R("idgham_mutajanisayn_kamil")}),
    # Warsh: وَيُعَذِّبْ مَنْ
    Case(id="yuadhdhib-man-warsh", site=Site(warsh=("2:284", (21, 22))),
         read=through(),
         phonemes=("w a j u ʕ a ðð i b Q", "m a n"),
         char_rules={"ب": R("qalqala_sughra")},
         absent_char_rules={"ب": R("idgham_mutajanisayn_kamil")}),
)


@pytest.mark.parametrize("run", case_runs(CASES))
def test_mutajanisayn_kamil(run):
    assert_case(run)
