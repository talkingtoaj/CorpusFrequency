import pytest
from django.contrib.auth import get_user_model

from corpus.models import Corpus
from corpus.services import ngrams as ngram_service
from corpus.services.ingest import add_document
from tests.samples import ISIK_TEXT, ISTANBUL_TEXT


@pytest.fixture(autouse=True)
def plain_static_storage(settings):
    """Serve static files without the hashed manifest during tests.

    Production uses whitenoise's manifest storage, which requires a
    collectstatic run; tests render templates without one.
    """
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user("ayse", password="corpus-pass-1")


@pytest.fixture
def other_user(db):
    return get_user_model().objects.create_user("mehmet", password="corpus-pass-2")


@pytest.fixture
def corpus(user):
    return Corpus.objects.create(owner=user, name="Turkish sample", language="tr")


@pytest.fixture
def analysed_corpus(corpus):
    add_document(corpus, "istanbul.txt", ISTANBUL_TEXT.encode("utf-8"))
    add_document(corpus, "isik.txt", ISIK_TEXT.encode("utf-8"))
    ngram_service.rebuild(corpus)
    return corpus


@pytest.fixture
def client_logged_in(client, user):
    client.force_login(user)
    return client
