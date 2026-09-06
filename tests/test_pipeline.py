"""End-to-end checks over the fixture corpus in tests/fixtures/input_files."""

from case_folding import convert_to_lower_case
from find_sentences import search
from get_ngrams import results


def ngram_counts(n):
    return {ngram: int(count) for ngram, count in results[str(n)]}


def test_case_variants_are_merged_into_one_ngram():
    """'İstanbul' x3 + 'istanbul' x2 + 'İSTANBUL' x1 == one n-gram of 6."""
    counts = ngram_counts(1)
    istanbul = [
        ngram for ngram in counts
        if convert_to_lower_case(ngram) == "istanbul"
    ]
    assert len(istanbul) == 1, f"case variants were not merged: {istanbul}"
    assert counts[istanbul[0]] == 6


def test_merged_ngram_survives_the_frequency_cut():
    """Each variant alone falls under MIN_FREQUENCY; merged, it clears it.

    Regression test: the cut used to be applied before merging, which threw
    away precisely the split n-grams the case folding exists to recombine.
    """
    assert "Işık" in ngram_counts(1)


def test_search_finds_every_correctly_spelled_casing():
    hits = [result["sentence"] for result in search("istanbul")]
    assert len(hits) == 6
    assert any("İstanbul" in hit for hit in hits)
    assert any("istanbul" in hit for hit in hits)
    assert any("İSTANBUL" in hit for hit in hits)


def test_search_matches_dotless_i_words():
    hits = search("ışık")
    assert len(hits) == 8


def test_search_preserves_original_casing_in_results():
    """Results are displayed, so they must not come back folded."""
    assert any("İstanbul" in result["sentence"] for result in search("istanbul"))


def test_markup_brackets_the_actual_match():
    """Offsets come from the folded string but slice the original one."""
    for result in search("istanbul"):
        highlighted = result["markup_sentence"].split("<b>")[1].split("</b>")[0]
        assert highlighted.lower().endswith("stanbul"), highlighted
