"""Issue #12 - rank n-grams by how characteristic they are, not how frequent."""

import pytest

from corpus.models import Corpus
from corpus.services import ngrams as ngram_service
from corpus.services import scoring
from corpus.services.ingest import add_document
from tests.samples_scoring import FOOTBALL, GENERAL

pytestmark = pytest.mark.django_db


@pytest.fixture
def scored(user):
    control = Corpus.objects.create(
        owner=user, name="General English", kind=Corpus.CONTROL, language="en"
    )
    add_document(control, "general.txt", GENERAL.encode())
    ngram_service.rebuild(control)

    target = Corpus.objects.create(
        owner=user, name="Football", language="en", control_corpus=control
    )
    add_document(target, "football.txt", FOOTBALL.encode())
    ngram_service.rebuild(target)
    scoring.rescore(target)
    return target


def importance(corpus, key):
    return corpus.ngrams.get(n=1, key=key).importance


def test_domain_words_score_above_general_words(scored):
    assert importance(scored, "referee") > importance(scored, "the")


def test_general_words_are_not_characteristic(scored):
    """'the' is frequent in both corpora, so it must not rank."""
    assert importance(scored, "the") < 0


def test_every_ngram_gets_a_score(scored):
    assert not scored.ngrams.filter(importance=None).exists()


def test_ranking_by_importance_differs_from_ranking_by_count(scored):
    by_count = list(scored.ngrams.filter(n=1).order_by("-count").values_list("key", flat=True))
    by_importance = list(
        scored.ngrams.filter(n=1).order_by("-importance").values_list("key", flat=True)
    )
    assert by_count != by_importance
    assert by_count[0] == "the"
    assert by_importance[0] != "the"


def test_frequency_still_breaks_ties_between_distinctive_words(scored):
    """A distinctive word that is common beats one that is barely there."""
    common = scored.ngrams.get(n=1, key="referee")
    rarer = scored.ngrams.get(n=1, key="offside")
    assert common.count > rarer.count
    assert common.importance > rarer.importance


def test_removing_the_control_clears_the_scores(scored):
    """A stale ranking must not be left looking authoritative."""
    scored.control_corpus = None
    scored.save()
    result = scoring.rescore(scored)
    assert result["cleared"] > 0
    assert not scored.ngrams.exclude(importance=None).exists()


def test_scoring_without_a_control_is_a_no_op(analysed_corpus):
    assert scoring.rescore(analysed_corpus) == {"scored": 0, "cleared": 0}


def test_control_totals_include_the_long_tail(user):
    """Denominators must count every occurrence, not just visible n-grams."""
    control = Corpus.objects.create(owner=user, name="C", kind=Corpus.CONTROL, language="en")
    add_document(control, "c.txt", GENERAL.encode())
    target = Corpus.objects.create(owner=user, name="T", language="en", control_corpus=control)

    counted = scoring.control_counts(target, control)
    rare = [key for key, (_, count) in counted[1].items() if count < 4]
    assert rare, "expected some below-threshold words in the control counts"
