"""View behaviour, with particular attention to multi-user isolation."""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from corpus.models import Corpus, Ngram
from tests.samples import ISTANBUL_TEXT

pytestmark = pytest.mark.django_db


@pytest.fixture
def their_corpus(other_user):
    return Corpus.objects.create(owner=other_user, name="Theirs", language="tr")


class TestAuthentication:
    def test_corpus_list_requires_login(self, client):
        response = client.get(reverse("corpus-list"))
        assert response.status_code == 302
        assert reverse("account_login") in response.url

    def test_logged_in_user_sees_their_list(self, client_logged_in):
        assert client_logged_in.get(reverse("corpus-list")).status_code == 200


class TestOwnershipIsolation:
    """A corpus belongs to one user; nobody else may read or change it."""

    def test_another_users_corpus_is_not_listed(self, client_logged_in, their_corpus):
        response = client_logged_in.get(reverse("corpus-list"))
        assert b"Theirs" not in response.content

    def test_another_users_corpus_detail_is_404(self, client_logged_in, their_corpus):
        response = client_logged_in.get(reverse("corpus-detail", args=[their_corpus.pk]))
        assert response.status_code == 404

    def test_another_users_ngram_cannot_be_toggled(self, client_logged_in, their_corpus):
        ngram = Ngram.objects.create(
            corpus=their_corpus, n=1, key="gizli", display="gizli", count=9
        )
        response = client_logged_in.post(
            reverse("toggle-selected", args=[ngram.pk]), {"selected": "true"}
        )
        assert response.status_code == 404
        ngram.refresh_from_db()
        assert ngram.selected is False

    def test_another_users_export_is_404(self, client_logged_in, their_corpus):
        response = client_logged_in.get(reverse("export", args=[their_corpus.pk]))
        assert response.status_code == 404

    def test_another_users_control_corpus_is_not_offered(self, client_logged_in, other_user):
        """The dropdown must not leak other people's corpus names."""
        Corpus.objects.create(owner=other_user, name="Their control", kind=Corpus.CONTROL)
        response = client_logged_in.get(reverse("corpus-list"))
        assert b"Their control" not in response.content


class TestCorpusLifecycle:
    def test_creating_a_corpus_assigns_the_logged_in_owner(self, client_logged_in, user):
        client_logged_in.post(
            reverse("corpus-list"),
            {"name": "Sport", "kind": Corpus.TARGET, "language": "en"},
        )
        assert Corpus.objects.get(name="Sport").owner == user

    def test_uploading_a_document_stores_its_text(self, client_logged_in, corpus):
        upload = SimpleUploadedFile("sample.txt", ISTANBUL_TEXT.encode("utf-8"))
        client_logged_in.post(reverse("upload-documents", args=[corpus.pk]), {"files": upload})
        assert corpus.documents.count() == 1
        assert "İstanbul" in corpus.documents.get().text

    def test_unsupported_upload_is_reported_not_crashed(self, client_logged_in, corpus):
        upload = SimpleUploadedFile("virus.exe", b"MZ...")
        response = client_logged_in.post(
            reverse("upload-documents", args=[corpus.pk]), {"files": upload}, follow=True
        )
        assert response.status_code == 200
        assert corpus.documents.count() == 0

    def test_analyse_builds_ngrams(self, client_logged_in, corpus):
        upload = SimpleUploadedFile("sample.txt", ISTANBUL_TEXT.encode("utf-8"))
        client_logged_in.post(reverse("upload-documents", args=[corpus.pk]), {"files": upload})
        client_logged_in.post(reverse("analyse", args=[corpus.pk]))
        assert corpus.ngrams.filter(n=1, key="istanbul").exists()


class TestSelection:
    """Issue #7 - the checkbox must both select and deselect, and persist."""

    def test_toggling_on_persists(self, client_logged_in, analysed_corpus):
        ngram = analysed_corpus.ngrams.get(n=1, key="istanbul")
        client_logged_in.post(reverse("toggle-selected", args=[ngram.pk]), {"selected": "true"})
        ngram.refresh_from_db()
        assert ngram.selected is True

    def test_toggling_off_persists(self, client_logged_in, analysed_corpus):
        ngram = analysed_corpus.ngrams.get(n=1, key="istanbul")
        ngram.selected = True
        ngram.save()
        client_logged_in.post(reverse("toggle-selected", args=[ngram.pk]), {"selected": "false"})
        ngram.refresh_from_db()
        assert ngram.selected is False

    def test_saving_an_example_implies_selection(self, client_logged_in, analysed_corpus):
        ngram = analysed_corpus.ngrams.get(n=1, key="istanbul")
        client_logged_in.post(
            reverse("save-text", args=[ngram.pk]), {"chosen_text": "İstanbul güzeldir."}
        )
        ngram.refresh_from_db()
        assert ngram.selected is True
        assert ngram.chosen_text == "İstanbul güzeldir."

    def test_clearing_the_example_does_not_deselect(self, client_logged_in, analysed_corpus):
        """Losing a description is not the same as dropping the n-gram."""
        ngram = analysed_corpus.ngrams.get(n=1, key="istanbul")
        ngram.selected = True
        ngram.chosen_text = "eski"
        ngram.save()
        client_logged_in.post(reverse("save-text", args=[ngram.pk]), {"chosen_text": ""})
        ngram.refresh_from_db()
        assert ngram.selected is True
        assert ngram.chosen_text == ""


class TestNeedsDescription:
    """Issue #8 - find selections that still have no example sentence."""

    def test_lists_selected_ngrams_without_a_description(self, client_logged_in, analysed_corpus):
        ngram = analysed_corpus.ngrams.get(n=1, key="istanbul")
        ngram.selected = True
        ngram.save()
        response = client_logged_in.get(reverse("needs-description", args=[analysed_corpus.pk]))
        assert "İstanbul".encode() in response.content

    def test_excludes_ngrams_that_have_a_description(self, client_logged_in, analysed_corpus):
        ngram = analysed_corpus.ngrams.get(n=1, key="istanbul")
        ngram.selected = True
        ngram.chosen_text = "İstanbul güzeldir."
        ngram.save()
        response = client_logged_in.get(reverse("needs-description", args=[analysed_corpus.pk]))
        assert "İstanbul".encode() not in response.content

    def test_excludes_unselected_ngrams(self, client_logged_in, analysed_corpus):
        response = client_logged_in.get(reverse("needs-description", args=[analysed_corpus.pk]))
        assert "İstanbul".encode() not in response.content


class TestExport:
    def test_exports_selected_ngrams_only(self, client_logged_in, analysed_corpus):
        chosen = analysed_corpus.ngrams.get(n=1, key="istanbul")
        chosen.selected = True
        chosen.chosen_text = "İstanbul güzeldir."
        chosen.save()

        body = client_logged_in.get(reverse("export", args=[analysed_corpus.pk])).content.decode()
        assert "İstanbul" in body
        assert "Işık" not in body

    def test_exports_a_selection_that_has_no_description_yet(self, client_logged_in, analysed_corpus):
        """`selected` drives export, not `chosen_text` - the point of #7."""
        chosen = analysed_corpus.ngrams.get(n=1, key="ışık")
        chosen.selected = True
        chosen.save()
        body = client_logged_in.get(reverse("export", args=[analysed_corpus.pk])).content.decode()
        assert "Işık" in body


class TestScoringViews:
    """Issue #12 - the control corpus is chosen and applied through the UI."""

    def test_settings_page_of_another_users_corpus_is_404(self, client_logged_in, their_corpus):
        response = client_logged_in.get(reverse("corpus-edit", args=[their_corpus.pk]))
        assert response.status_code == 404

    def test_setting_a_control_corpus_scores_immediately(self, client_logged_in, user, analysed_corpus):
        control = Corpus.objects.create(
            owner=user, name="Control", kind=Corpus.CONTROL, language="tr"
        )
        from corpus.services.ingest import add_document

        add_document(control, "c.txt", ISTANBUL_TEXT.encode("utf-8"))

        client_logged_in.post(
            reverse("corpus-edit", args=[analysed_corpus.pk]),
            {
                "name": analysed_corpus.name,
                "kind": Corpus.TARGET,
                "language": "tr",
                "control_corpus": control.pk,
            },
        )
        analysed_corpus.refresh_from_db()
        assert analysed_corpus.control_corpus == control
        assert analysed_corpus.ngrams.exclude(importance=None).exists()

    def test_importance_ordering_hides_unscored_ngrams(self, client_logged_in, analysed_corpus):
        """Without a control corpus there is nothing to rank by."""
        response = client_logged_in.get(
            reverse("ngram-list", args=[analysed_corpus.pk, 1]), {"by": "importance"}
        )
        assert response.status_code == 200
        assert "İstanbul".encode() not in response.content


class TestUploadLimits:
    def test_oversized_upload_is_rejected(self, client_logged_in, corpus, settings):
        settings.MAX_UPLOAD_BYTES = 64
        upload = SimpleUploadedFile("big.txt", b"x" * 200)
        response = client_logged_in.post(
            reverse("upload-documents", args=[corpus.pk]), {"files": upload}, follow=True
        )
        assert response.status_code == 200
        assert corpus.documents.count() == 0
        assert b"upload limit" in response.content

    def test_upload_within_the_limit_is_accepted(self, client_logged_in, corpus, settings):
        settings.MAX_UPLOAD_BYTES = 10_000
        upload = SimpleUploadedFile("small.txt", ISTANBUL_TEXT.encode("utf-8"))
        client_logged_in.post(reverse("upload-documents", args=[corpus.pk]), {"files": upload})
        assert corpus.documents.count() == 1
