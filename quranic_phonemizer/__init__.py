"""Quranic phonemizer. `Phonemizer(...).analyse(ref)` is the entry point."""
from .analysis.facade import (
    Phonemizer,
    Result,
    UnknownExtraPhoneme,
    UnknownRule,
    UnknownStopSign,
    available_stop_editions,
    available_stop_signs,
    available_variants,
    supported_riwayat,
    tajweed_rules,
    variant_catalogue,
)
from .model.address import (
    KhilafId,
    Option,
    Riwayah,
    Script,
    UnknownRiwayah,
    VariantSelection,
)
from .stop_editions import UnknownStopEdition

__all__: list[str] = [
    "KhilafId",
    "Option",
    "Phonemizer",
    "Result",
    "Riwayah",
    "Script",
    "UnknownExtraPhoneme",
    "UnknownRiwayah",
    "UnknownRule",
    "UnknownStopEdition",
    "UnknownStopSign",
    "VariantSelection",
    "available_stop_editions",
    "available_stop_signs",
    "available_variants",
    "variant_catalogue",
    "supported_riwayat",
    "tajweed_rules",
]
