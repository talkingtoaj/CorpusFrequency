"""Paging and filtering the n-gram lists.

Without paging a real corpus renders every n-gram into one document: 12,000
of them came to 2.6 MB of HTML, with a checkbox listener attached to each.
"""

import pytest
from django.urls import reverse

from corpus.models import PAGE_SIZE, Corpus, Ngram

pytestmark = pytest.mark.django_db


@pytest.fixture
def many_ngrams(user):
    corpus = Corpus.objects.create(owner=user, name="Big", language="tr")
    Ngram.objects.bulk_create(
        [
            Ngram(corpus=corpus, n=1, key=f"kelime{i:04d}", display=f"kelime{i:04d}", count=5000 - i)
            for i in range(250)
        ]
    )
    return corpus


def page_of(response):
    return response.context["page_obj"]


class TestPaging:
    def test_first_page_is_capped_at_the_page_size(self, client_logged_in, many_ngrams):
        response = client_logged_in.get(reverse("ngram-list", args=[many_ngrams.pk, 1]))
        assert len(page_of(response).object_list) == PAGE_SIZE

    def test_total_reports_the_whole_result_set(self, client_logged_in, many_ngrams):
        response = client_logged_in.get(reverse("ngram-list", args=[many_ngrams.pk, 1]))
        assert response.context["total"] == 250

    def test_later_pages_continue_the_ordering(self, client_logged_in, many_ngrams):
        first = client_logged_in.get(reverse("ngram-list", args=[many_ngrams.pk, 1]))
        second = client_logged_in.get(
            reverse("ngram-list", args=[many_ngrams.pk, 1]), {"page": 2}
        )
        assert page_of(first).object_list[0].count > page_of(second).object_list[0].count

    def test_last_page_holds_the_remainder(self, client_logged_in, many_ngrams):
        response = client_logged_in.get(
            reverse("ngram-list", args=[many_ngrams.pk, 1]), {"page": 3}
        )
        assert len(page_of(response).object_list) == 50

    def test_out_of_range_page_clamps_rather_than_404s(self, client_logged_in, many_ngrams):
        response = client_logged_in.get(
            reverse("ngram-list", args=[many_ngrams.pk, 1]), {"page": 9999}
        )
        assert response.status_code == 200
        assert page_of(response).number == page_of(response).paginator.num_pages

    def test_a_nonsense_page_does_not_error(self, client_logged_in, many_ngrams):
        response = client_logged_in.get(
            reverse("ngram-list", args=[many_ngrams.pk, 1]), {"page": "abc"}
        )
        assert response.status_code == 200

    def test_page_stays_small(self, client_logged_in, many_ngrams):
        response = client_logged_in.get(reverse("ngram-list", args=[many_ngrams.pk, 1]))
        assert len(response.content) < 100_000


class TestFiltering:
    def test_filter_narrows_the_result_set(self, client_logged_in, many_ngrams):
        response = client_logged_in.get(
            reverse("ngram-list", args=[many_ngrams.pk, 1]), {"q": "kelime001"}
        )
        assert response.context["total"] == 10

    def test_filter_folds_the_query_to_the_corpus_language(self, client_logged_in, analysed_corpus):
        """'İSTANBUL' must find the n-gram keyed 'istanbul'."""
        response = client_logged_in.get(
            reverse("ngram-list", args=[analysed_corpus.pk, 1]), {"q": "İSTANBUL"}
        )
        assert [ngram.key for ngram in page_of(response).object_list] == ["istanbul"]

    def test_a_plain_lowercase_query_also_matches(self, client_logged_in, analysed_corpus):
        response = client_logged_in.get(
            reverse("ngram-list", args=[analysed_corpus.pk, 1]), {"q": "istanbul"}
        )
        assert response.context["total"] == 1

    def test_ascii_i_is_folded_to_dotless_and_finds_nothing(self, client_logged_in, analysed_corpus):
        """Turkish 'I' lowercases to 'ı', so this is the documented miss."""
        response = client_logged_in.get(
            reverse("ngram-list", args=[analysed_corpus.pk, 1]), {"q": "ISTANBUL"}
        )
        assert response.context["total"] == 0

    def test_filter_is_scoped_to_the_requested_n(self, client_logged_in, analysed_corpus):
        response = client_logged_in.get(
            reverse("ngram-list", args=[analysed_corpus.pk, 2]), {"q": "istanbul"}
        )
        assert all(ngram.n == 2 for ngram in page_of(response).object_list)

    def test_filter_survives_the_importance_ordering(self, client_logged_in, many_ngrams):
        response = client_logged_in.get(
            reverse("ngram-list", args=[many_ngrams.pk, 1]), {"q": "kelime", "by": "importance"}
        )
        assert response.context["ordering"] == "-importance"
        assert response.context["query"] == "kelime"

    def test_needs_description_can_be_filtered(self, client_logged_in, analysed_corpus):
        analysed_corpus.ngrams.filter(n=1).update(selected=True)
        response = client_logged_in.get(
            reverse("needs-description", args=[analysed_corpus.pk]), {"q": "istanbul"}
        )
        assert [ngram.key for ngram in page_of(response).object_list] == ["istanbul"]
