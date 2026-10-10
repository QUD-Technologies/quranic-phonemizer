"""The shared-rule baseline bound by Warsh through al-Azraq."""

from __future__ import annotations

from ...engine.classifier import RuleSet
from ...engine.plan import Phase
from ...model.address import KhilafId, Location, Riwayah
from ...model.canon import CanonLetter, Quality
from ...rules.annotation import CanonicalColour, CarrierTarqeeq, Inclination
from ...rules.boundary import (
    DroppedGlide,
    IwadLength,
    PausalAlif,
    TaaMarbutaAtWaqf,
    TanweenDrop,
    TanweenIwad,
    WaqfHarakaDrop,
    WaqfSilahDrop,
)
from ...rules.hamza_meetings import HamzaMeetingMadd, HamzaMeetings
from ...rules.idgham import Idgham
from ...rules.lam import LamWeight
from ...rules.lam_shamsiyyah import ArticleLam, ArticleShape
from ...rules.madd import (
    IltiqaShortening,
    MaddBadal,
    MaddClass,
    MaddLazimIbdal,
    MaddLeen,
    MaddSilah,
)
from ...rules.meem_sakinah import GhunnahMushaddadah, MeemSakinah
from ...rules.naql import CarriedNaql, Naql
from ...rules.noon_sakinah import IkhfaaWeight, NoonSakinah
from ...rules.pausal_glide import PausalGlide
from ...rules.qalqala import Qalqala
from ...rules.raa import RaaWeight
from ...rules.single_hamza import (
    AllaiFaces,
    AraytaIbdal,
    JoinedIbdal,
    JoinedIbdalMadd,
    SuppliedIbdal,
)
from ...rules.tafkheem import Emphasis, Weight
from ...rules.waqf_marks import WaqfIqlabMarkDrop
from ...rules.warsh_madd import (
    MaddLeenMahmuz,
    MaddMimAlJam,
    MaddYaaZawaid,
    StartedBadal,
)
from ...rules.wasl import (
    SoftenedHamza,
    SpelledBeforeWasl,
    TanweenBeforeWasl,
    WaslHamza,
)
from .hamza_meetings import meeting_rows, rows_by_target, selector_choices
from .lam import selector_profile as lam_selector_profile
from .raa import selector_profile as raa_selector_profile
from .resources import khilaf, lexicon, rule_tables
from .single_hamza import authored_locations

#: Warsh repairs a collision with damm when the elided word starts on an
#: original damm; the shared kasra and fatha defaults stand elsewhere.
_DAMM_START_REPAIR = {Quality.U: Quality.U}

#: The `كتابيه إني` boundary reads tahqiq by default: haa stays sakin and
#: the qata is fully realized, so the general transfer must not claim it.
_NAQL_TAHQIQ = frozenset({Location(69, 20, 1)})
#: The mushaf writes عَاداً ا۬لُّولَىٰ with the tanwin noon already assimilated
#: into the naql-voweled geminate lam, so no iltiqa repair applies there.
_NAQL_ASSIMILATED = frozenset({Location(53, 50, 4)})
#: A tanwin-separated row's boundary reads by ordinary naql, so only the
#: real meetings shield their second word from the transfer.
_HAMZA_MEETING_STARTS = frozenset(
    row.canonical
    for row in meeting_rows()
    if row.scope != "one_word" and not row.separated
)
_NAQL_IBDAL_MEETINGS = frozenset(
    row.canonical
    for row in meeting_rows()
    if row.scope == "one_word" and row.owner == "hamza_dhat_fath"
)

#: Dhal merges into taa only in the `أخذ` family, so `نَبَذْتُهَا` and
#: `عُذْتُ` keep it.
_AKHADHA_DHAL = frozenset({(CanonLetter.KHA, CanonLetter.THAL, CanonLetter.TA)})

# Canonical locations of مَوْئِلا and الْمَوْءُودَة.  Only the first waw of
# the latter can satisfy the leen predicate; its following long remains badal.
_LEEN_MAHMUZ_EXCLUDED = frozenset({
    Location(18, 58, 19),
    Location(81, 8, 2),
})


def _article(tables) -> ArticleShape:
    return ArticleShape(
        prefixes=tables.proclitics,
        is_form_eight_lam=lexicon().is_form_eight_lam,
    )


def _boundary() -> tuple:
    return (
        Naql(
            excluded=_NAQL_TAHQIQ | _HAMZA_MEETING_STARTS,
            ibdal_meetings=_NAQL_IBDAL_MEETINGS,
            meeting_choice=khilaf().variants.get(KhilafId.HAMZA_DHAT_FATH),
            tahqiq_choices={
                location: khilaf().variants.get(KhilafId.KITABIYAH_INNI)
                for location in _NAQL_TAHQIQ
            },
        ),
        CarriedNaql(),
        HamzaMeetings(
            rows=rows_by_target(),
            choices=selector_choices(khilaf().variants),
        ),
        AraytaIbdal(
            locations=authored_locations("arayta"),
            bare=authored_locations("arayta_bare"),
            choice=khilaf().variants.get(KhilafId.HAMZA_ARAYTA),
        ),
        AllaiFaces(
            locations=authored_locations("allai"),
            choice=khilaf().variants.get(KhilafId.ALLAI_WAQF),
        ),
        SuppliedIbdal(),
        JoinedIbdal(),
        WaslHamza(
            article_choice=khilaf().variants.get(KhilafId.ARTICLE_IBTIDAA),
        ),
        SoftenedHamza(),
        PausalAlif(),
        SpelledBeforeWasl(repairs=_DAMM_START_REPAIR),
        TanweenBeforeWasl(
            repairs=_DAMM_START_REPAIR,
            assimilated=_NAQL_ASSIMILATED,
        ),
        TanweenDrop(),
        TanweenIwad(),
        WaqfIqlabMarkDrop(),
        WaqfHarakaDrop(yaa=khilaf().yaa),
        WaqfSilahDrop(),
        DroppedGlide(yaa=khilaf().yaa),
        TaaMarbutaAtWaqf(),
    )


def _build() -> RuleSet:
    tables = rule_tables()
    article = _article(tables)
    weight = Weight(always_heavy=tables.always_heavy, raa_enabled=False)
    return RuleSet(
        {
            Phase.BOUNDARY: _boundary(),
            Phase.MERGE: (
                NoonSakinah(
                    followers=tables.followers_of_noon,
                    opening_wasl=(
                        khilaf().definition(KhilafId.NOON_WASL),
                    ),
                ),
                MeemSakinah(followers=tables.followers_of_meem),
                ArticleLam(sun=tables.sun_letters, article=article),
                GhunnahMushaddadah(sun=tables.sun_letters, article=article),
                Idgham(
                    pairs=tables.pairs,
                    never_follows=tables.never_follows,
                    article=article,
                    stems=_AKHADHA_DHAL,
                ),
            ),
            Phase.LENGTH: (
                PausalGlide(),
                IltiqaShortening(),
                MaddLazimIbdal(
                    khilaf().canonical.madd.locations,
                    khilaf().canonical.madd.default,
                ),
                HamzaMeetingMadd(),
                JoinedIbdalMadd(),
                MaddClass(badal_is_effective=True),
                MaddClass(additive_arid=True),
                MaddLeen(mahmuz_is_distinct=True),
                MaddLeenMahmuz(excluded=_LEEN_MAHMUZ_EXCLUDED),
                MaddBadal(),
                StartedBadal(),
                MaddSilah(),
                MaddMimAlJam(),
                MaddYaaZawaid(),
                IwadLength(),
            ),
            Phase.COLOUR: (
                LamWeight(
                    profile=lam_selector_profile(khilaf().variants),
                    base_weight=weight,
                ),
                Emphasis(weight=weight),
                RaaWeight(profile=raa_selector_profile(khilaf().variants)),
                CarrierTarqeeq(),
                Inclination(),
                CanonicalColour(),
                IkhfaaWeight(
                    followers=tables.followers_of_noon,
                    always_heavy=tables.always_heavy,
                ),
            ),
            Phase.RELEASE: (Qalqala(letters=tables.qalqala, pairs=tables.pairs),),
        }
    )


WARSH = _build()


def rules_for(riwayah: Riwayah) -> RuleSet:
    if riwayah is not Riwayah.WARSH:
        raise ValueError(f"{__name__} assembles warsh, not {riwayah.value}")
    return WARSH


__all__ = ["WARSH", "rules_for"]
