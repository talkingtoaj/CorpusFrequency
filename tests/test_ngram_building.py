"""N-gram construction, case merging and rebuild behaviour."""

import pytest

from corpus.models import MIN_FREQUENCY, Corpus, Ngram
from corpus.services import ngrams as ngram_service
from corpus.services.ingest import add_document

from tests.samples import ISTANBUL_TEXT

pytestmark = pytest.mark.django_db


def unigram(corpus, key):
    return corpus.ngrams.get(n=1, key=key)


def test_case_variants_merge_into_one_ngram(analysed_corpus):
    """3x 'İstanbul' + 2x 'istanbul' + 1x 'İSTANBUL' is one n-gram of 6."""
    assert analysed_corpus.ngrams.filter(n=1, key="istanbul").count() == 1
    assert unigram(analysed_corpus, "istanbul").count == 6


def test_merged_ngram_survives_a_cut_no_variant_would(analysed_corpus):
    """Each casing alone is under MIN_FREQUENCY; merged they clear it.

    Regression test: the cut used to run before merging, discarding exactly
    the split n-grams the case folding exists to recombine.
    """
    assert MIN_FREQUENCY > 3
    assert unigram(analysed_corpus, "ışık").count == 8


def test_dotless_and_dotted_i_do_not_merge(analysed_corpus):
    keys = set(analysed_corpus.ngrams.filter(n=1).values_list("key", flat=True))
    assert "istanbul" in keys
    assert "ışık" in keys


def test_display_uses_the_most_frequent_casing(analysed_corpus):
    """'İstanbul' (3) beats 'istanbul' (2), so the correct spelling shows."""
    assert unigram(analysed_corpus, "istanbul").display == "İstanbul"
    assert unigram(analysed_corpus, "ışık").display == "Işık"


def test_rare_ngrams_are_dropped(analysed_corpus):
    for ngram in analysed_corpus.ngrams.all():
        assert ngram.count >= MIN_FREQUENCY


def test_language_setting_changes_folding(user):
    """An English corpus must not get the Turkish dotless-i mapping."""
    english = Corpus.objects.create(owner=user, name="English", language="en")
    add_document(english, "a.txt", (("INDIA is warm. india is warm. " * 3)).encode())
    ngram_service.rebuild(english)
    assert english.ngrams.filter(n=1, key="india").exists()


class TestRebuildPreservesWork:
    """Issue #9 - adding documents later must not discard progress."""

    def test_selection_and_text_survive_a_rebuild(self, analysed_corpus):
        ngram = unigram(analysed_corpus, "istanbul")
        ngram.selected = True
        ngram.chosen_text = "İstanbul çok büyük bir şehirdir."
        ngram.save()

        add_document(analysed_corpus, "more.txt", ISTANBUL_TEXT.encode("utf-8"))
        ngram_service.rebuild(analysed_corpus)

        ngram.refresh_from_db()
        assert ngram.selected is True
        assert ngram.chosen_text == "İstanbul çok büyük bir şehirdir."

    def test_counts_are_updated_by_a_rebuild(self, analysed_corpus):
        assert unigram(analysed_corpus, "istanbul").count == 6
        add_document(analysed_corpus, "more.txt", ISTANBUL_TEXT.encode("utf-8"))
        ngram_service.rebuild(analysed_corpus)
        assert unigram(analysed_corpus, "istanbul").count == 12

    def test_rebuild_does_not_duplicate_ngrams(self, analysed_corpus):
        before = analysed_corpus.ngrams.count()
        ngram_service.rebuild(analysed_corpus)
        assert analysed_corpus.ngrams.count() == before

    def test_unselected_ngrams_that_fall_away_are_removed(self, analysed_corpus):
        orphan = Ngram.objects.create(
            corpus=analysed_corpus, n=1, key="yok", display="yok", count=9
        )
        ngram_service.rebuild(analysed_corpus)
        assert not Ngram.objects.filter(pk=orphan.pk).exists()

    def test_selected_ngrams_that_fall_away_are_kept(self, analysed_corpus):
        """Deleting selected work would lose the very thing #9 protects."""
        kept = Ngram.objects.create(
            corpus=analysed_corpus, n=1, key="yok", display="yok", count=9, selected=True
        )
        ngram_service.rebuild(analysed_corpus)
        assert Ngram.objects.filter(pk=kept.pk).exists()


def test_corpus_is_stale_until_reanalysed(analysed_corpus):
    assert analysed_corpus.is_stale is False
    add_document(analysed_corpus, "more.txt", ISTANBUL_TEXT.encode("utf-8"))
    assert analysed_corpus.is_stale is True
    ngram_service.rebuild(analysed_corpus)
    assert analysed_corpus.is_stale is False
