"""Sentence search, including the offset alignment the highlight relies on."""

import pytest

from corpus.services.search import search

pytestmark = pytest.mark.django_db


def test_finds_every_correctly_spelled_casing(analysed_corpus):
    hits = [result["sentence"] for result in search(analysed_corpus, "İstanbul")]
    assert len(hits) == 6
    assert any("İstanbul" in hit for hit in hits)
    assert any("istanbul" in hit for hit in hits)
    assert any("İSTANBUL" in hit for hit in hits)


def test_results_keep_original_casing(analysed_corpus):
    """Results are displayed, so they must not come back folded."""
    assert any("İSTANBUL" in result["sentence"] for result in search(analysed_corpus, "İstanbul"))


def test_highlight_brackets_the_actual_match(analysed_corpus):
    """Offsets come from the folded text but slice the original."""
    for result in search(analysed_corpus, "İstanbul"):
        assert result["match"].lower().endswith("stanbul"), result["match"]


def test_dotless_i_words_are_found(analysed_corpus):
    assert len(search(analysed_corpus, "Işık")) == 8


def test_word_boundaries_are_respected(analysed_corpus):
    """'ışık' must not match inside a longer word.

    Folded with the corpus's language rather than str.lower(), which would
    turn the matched 'Işık' into 'işık' and defeat the check.
    """
    for result in search(analysed_corpus, "Işık"):
        assert analysed_corpus.fold(result["match"]) == "ışık"


def test_multi_word_ngram_matches_across_punctuation(analysed_corpus):
    """Regression: re.escape escapes spaces, which broke the \\W join."""
    results = search(analysed_corpus, "çok büyük")
    assert results
    assert all("çok büyük" in result["match"] for result in results)


def test_search_is_scoped_to_one_corpus(analysed_corpus, other_user):
    from corpus.models import Corpus
    from corpus.services.ingest import add_document

    theirs = Corpus.objects.create(owner=other_user, name="Theirs", language="tr")
    add_document(theirs, "x.txt", "İstanbul çok büyük bir şehirdir.".encode())
    assert search(theirs, "İstanbul")
    assert len(search(analysed_corpus, "İstanbul")) == 6
