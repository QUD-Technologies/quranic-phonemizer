from __future__ import annotations

import pytest

from tests.support import (
    Case,
    Expect,
    R,
    Site,
    StateCase,
    assert_case,
    case_runs,
    explicit,
    isolated,
    through,
)

CASES = (
    # Hafs: وَقُل رَّبِّ
    # Warsh: وَقُل رَّبِّ
    StateCase(id="qul-rabbi", site=Site.shared("23:118", (1, 2)), states={
        "joined": Expect(read=through(), phonemes=("w a q u", "rˤrˤ aˤ bb Q"),
                         char_rules={"ل": R("idgham_mutaqaribayn"),
                                     "ر": R("idgham_mutaqaribayn")},
                         sound_rules={"rˤrˤ": R("idgham_mutaqaribayn")}),
        "ibtidaa-on-host": Expect(read=explicit(ibtidaa=1, waqf=1),
                          phonemes=("w a q u l", "rˤ aˤ bb i"),
                          absent_char_rules={"ل": R("idgham_mutaqaribayn"),
                                             "ر": R("idgham_mutaqaribayn")}),
    }),
    # Hafs: بَل رَّفَعَهُ
    # Warsh: بَل رَّفَعَهُ
    StateCase(id="bal-rafah", site=Site.shared("4:158", (1, 2)), states={
        "joined": Expect(read=through(), phonemes=("b a", "rˤrˤ aˤ f a ʕ a h"),
                         char_rules={"ل": R("idgham_mutaqaribayn"),
                                     "ر": R("idgham_mutaqaribayn")},
                         sound_rules={"rˤrˤ": R("idgham_mutaqaribayn")}),
        "ibtidaa-on-host": Expect(read=explicit(ibtidaa=1, waqf=1),
                          phonemes=("b a l", "rˤ aˤ f a ʕ a h u"),
                          absent_char_rules={"ل": R("idgham_mutaqaribayn"),
                                             "ر": R("idgham_mutaqaribayn")}),
    }),
    # Hafs: نَخْلُقكُّم
    # Warsh: نَخْلُقكُّم
    Case(id="nakhluqkum", site=Site.shared("77:20", (2,)), read=isolated(),
         phonemes="n a x l u kk u m",
         char_rules={"ق": R("idgham_mutaqaribayn"),
                     "ك": R("idgham_mutaqaribayn")},
         sound_rules={"kk": R("idgham_mutaqaribayn")},
         absent_char_rules={"ق": R(
             "tafkheem", "qalqala_sughra", "qalqala_kubra", "qalqala_akbar")}),
    # Warsh: فَقَد ضَّلَّ
    StateCase(id="qad-dad-warsh", site=Site(warsh=("2:108", (15, 16))), states={
        "joined": Expect(read=through(), phonemes=("f a q aˤ", "dˤdˤ aˤ ll"),
                         char_rules={"د": R("idgham_mutaqaribayn"),
                                     "ض": R("idgham_mutaqaribayn")},
                         sound_rules={"dˤdˤ": R("idgham_mutaqaribayn")},
                         absent_char_rules={"د": R("qalqala_sughra")}),
        "ibtidaa-on-host": Expect(read=explicit(ibtidaa=15, waqf=15),
                          phonemes=("f a q aˤ d Q", "dˤ aˤ ll a"),
                          absent_char_rules={"د": R("idgham_mutaqaribayn"),
                                             "ض": R("idgham_mutaqaribayn")}),
    }),
    # Warsh: فَقَد ظَّلَمَ
    Case(id="qad-zaa-warsh", site=Site(warsh=("65:1", (31, 32))), read=through(),
         phonemes=("f a q aˤ", "ðˤðˤ aˤ lˤ aˤ m"),
         char_rules={"د": R("idgham_mutaqaribayn"),
                     "ظ": R("idgham_mutaqaribayn")},
         sound_rules={"ðˤðˤ": R("idgham_mutaqaribayn")}),
    # Warsh: كَانَت ظَّالِمَةٗ
    Case(id="taa-zaa-warsh", site=Site(warsh=("21:11", (5, 6))), read=through(),
         phonemes=("k a: n a", "ðˤðˤ aˤ: l i m a h"),
         char_rules={"ت": R("idgham_mutaqaribayn"),
                     "ظ": R("idgham_mutaqaribayn")},
         sound_rules={"ðˤðˤ": R("idgham_mutaqaribayn")}),
    # Warsh: اَ۪تَّخَذتُّمُ
    Case(id="ittakhadhtum-warsh", site=Site(warsh=("2:51", (7,))), read=isolated(),
         phonemes="ʔ i tt a x aˤ tt u m",
         char_rules={"ذ": R("idgham_mutaqaribayn"),
                     "ت[2]": R("idgham_mutaqaribayn")},
         sound_rules={"tt[2]": R("idgham_mutaqaribayn")}),
    # Warsh: فَنَبَذْتُهَا
    Case(id="nabadhtuha-warsh", site=Site(warsh=("20:96", (12,))), read=isolated(),
         phonemes="f a n a b a ð t u h a:",
         absent_char_rules={"ذ": R("idgham_mutaqaribayn")}),
)


@pytest.mark.parametrize("run", case_runs(CASES))
def test_mutaqaribayn(run):
    assert_case(run)
