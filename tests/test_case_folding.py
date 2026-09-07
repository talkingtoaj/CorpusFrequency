"""Regression tests for issue #15 - Turkish dotted/dotless i.

The failures these cover are all cases where Python's default, locale
independent case mappings disagree with Turkish orthography.
"""

import unicodedata

import pytest

from corpus.case_folding import convert_to_lower_case, fold_preserving_length


def test_dotted_capital_i_folds_to_a_single_codepoint():
    """`'İ'.lower()` yields 'i' + U+0307, which breaks string matching."""
    folded = convert_to_lower_case("İ")
    assert folded == "i"
    assert len(folded) == 1
    assert "̇" not in folded


def test_istanbul_variants_share_one_key():
    """The correctly-spelled variants collapse to a single n-gram key.

    This is the bug from issue #15: before the fix, 'İstanbul' folded to a
    two-codepoint sequence and never matched 'istanbul'.
    """
    variants = ["İstanbul", "istanbul", "İSTANBUL"]
    folded = {convert_to_lower_case(variant) for variant in variants}
    assert folded == {"istanbul"}, folded


def test_ascii_mangled_capital_i_is_a_known_limitation():
    """Documents a trade-off rather than asserting desired behaviour.

    In Turkish the lowercase of 'I' is dotless 'ı', so 'ISTANBUL' folds to
    'ıstanbul' and does not merge with 'istanbul'. That is orthographically
    correct - they are different letters - but text that was flattened to
    ASCII somewhere upstream (signage, foreign sources, systems that cannot
    store 'İ') will spell the city 'ISTANBUL' and land in its own n-gram.

    Fixing this would mean mapping 'I' -> 'i', which would then merge
    'ışık' with 'işik' and corrupt every genuine dotless-i word. Splitting
    the rare mangled spelling is the cheaper error, so it is left alone.
    """
    assert convert_to_lower_case("ISTANBUL") == "ıstanbul"
    assert convert_to_lower_case("ISTANBUL") != convert_to_lower_case("istanbul")


def test_default_lower_would_have_failed_to_merge_istanbul():
    """Guards the premise of the fix: this is what we are working around."""
    assert "İstanbul".lower() != "istanbul".lower()


def test_dotless_i_round_trips():
    assert convert_to_lower_case("IŞIK") == "ışık"
    assert convert_to_lower_case("ışık") == "ışık"
    assert convert_to_lower_case("Işık") == "ışık"


def test_dotless_and_dotted_i_stay_distinct():
    """They are separate letters in Turkish and must not be merged."""
    assert convert_to_lower_case("ı") != convert_to_lower_case("i")
    assert convert_to_lower_case("kırık") != convert_to_lower_case("kirik")


def test_non_turkish_text_uses_default_folding():
    assert convert_to_lower_case("Straße", lang="de") == "strasse"
    assert convert_to_lower_case("HELLO", lang="en") == "hello"


def test_english_i_is_unharmed_when_language_is_not_turkish():
    """The dotless mapping must not leak into other languages."""
    assert convert_to_lower_case("INDIA", lang="en") == "india"


def test_decomposed_input_normalises_to_composed():
    decomposed = unicodedata.normalize("NFD", "şeker")
    assert convert_to_lower_case(decomposed) == convert_to_lower_case("şeker")


@pytest.mark.parametrize(
    "text",
    ["İstanbul", "IŞIK kaynağı", "Straße", "ÇĞÖŞÜ", "plain ascii"],
)
def test_length_preserving_fold_keeps_indices_aligned(text):
    """Match offsets are used to slice the original string in `search`."""
    assert len(fold_preserving_length(text)) == len(text)


def test_length_preserving_fold_agrees_for_one_to_one_mappings():
    assert fold_preserving_length("İSTANBUL") == convert_to_lower_case("İSTANBUL")


def test_length_preserving_fold_declines_to_expand():
    """'ß' -> 'ss' would shift every later index, so it is left alone."""
    assert fold_preserving_length("Straße") == "straße"
