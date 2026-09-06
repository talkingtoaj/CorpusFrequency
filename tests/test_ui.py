"""Browser tests driving the real application.

These cover the behaviour that unit tests cannot see: that the checkbox
actually writes to the server, and that its state survives a reload. That
is the substance of issue #7 - the old checkbox rendered from server state
but fired no request, so it looked interactive while persisting nothing.
"""

import pathlib
import tempfile

import pytest

from corpus.models import Corpus
from tests.samples import ISIK_TEXT, ISTANBUL_TEXT

playwright_api = pytest.importorskip("playwright.sync_api")

PASSWORD = "corpus-browser-pass"


@pytest.fixture
def browser_user(transactional_db, django_user_model):
    return django_user_model.objects.create_user("ayse", password=PASSWORD)


@pytest.fixture
def browser_corpus(browser_user):
    """A corpus with documents already ingested and analysed."""
    from corpus.services import ngrams as ngram_service
    from corpus.services.ingest import add_document

    corpus = Corpus.objects.create(owner=browser_user, name="Turkish sample", language="tr")
    add_document(corpus, "istanbul.txt", ISTANBUL_TEXT.encode("utf-8"))
    add_document(corpus, "isik.txt", ISIK_TEXT.encode("utf-8"))
    ngram_service.rebuild(corpus)
    return corpus


@pytest.fixture
def page(live_server):
    with playwright_api.sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        yield page
        browser.close()


def login(page, live_server):
    page.goto(f"{live_server.url}/accounts/login/")
    page.fill("#id_username", "ayse")
    page.fill("#id_password", PASSWORD)
    page.click("button[type=submit]")


def test_login_lands_on_the_corpus_list(page, live_server, browser_user):
    login(page, live_server)
    assert page.locator("h1", has_text="Your corpora").count() == 1


def test_ngram_list_shows_the_merged_turkish_ngram(page, live_server, browser_corpus):
    login(page, live_server)
    page.goto(f"{live_server.url}/corpus/{browser_corpus.pk}/ngrams/1/")
    assert page.locator('.ngrams li', has_text="İstanbul").count() == 1
    assert page.locator('.ngrams li', has_text="İstanbul").inner_text().find("6") != -1


def test_checkbox_can_select_and_it_survives_a_reload(page, live_server, browser_corpus):
    login(page, live_server)
    page.goto(f"{live_server.url}/corpus/{browser_corpus.pk}/ngrams/1/")

    checkbox = page.locator('.ngram-checkbox[data-ngram="İstanbul"]')
    assert checkbox.is_checked() is False
    checkbox.check()
    page.wait_for_timeout(400)

    page.reload()
    assert page.locator('.ngram-checkbox[data-ngram="İstanbul"]').is_checked() is True


def test_checkbox_can_deselect_and_it_survives_a_reload(page, live_server, browser_corpus):
    browser_corpus.ngrams.filter(key="istanbul").update(selected=True)
    login(page, live_server)
    page.goto(f"{live_server.url}/corpus/{browser_corpus.pk}/ngrams/1/")

    checkbox = page.locator('.ngram-checkbox[data-ngram="İstanbul"]')
    assert checkbox.is_checked() is True
    checkbox.uncheck()
    page.wait_for_timeout(400)

    page.reload()
    assert page.locator('.ngram-checkbox[data-ngram="İstanbul"]').is_checked() is False


def test_selecting_then_writing_an_example_clears_the_todo_list(page, live_server, browser_corpus):
    """Issue #8 - selections without a description are findable until written."""
    login(page, live_server)
    page.goto(f"{live_server.url}/corpus/{browser_corpus.pk}/ngrams/1/")
    page.locator('.ngram-checkbox[data-ngram="İstanbul"]').check()
    page.wait_for_timeout(400)

    page.goto(f"{live_server.url}/corpus/{browser_corpus.pk}/needs-description/")
    assert page.locator(".ngrams li", has_text="İstanbul").count() == 1

    page.click('.ngrams a:has-text("İstanbul")')
    page.fill("#chosen_text", "İstanbul çok büyük bir şehirdir.")
    page.click("button[type=submit]")

    page.goto(f"{live_server.url}/corpus/{browser_corpus.pk}/needs-description/")
    assert page.locator(".ngrams li", has_text="İstanbul").count() == 0


def test_sentences_are_listed_with_the_match_highlighted(page, live_server, browser_corpus):
    login(page, live_server)
    ngram = browser_corpus.ngrams.get(n=1, key="istanbul")
    page.goto(f"{live_server.url}/ngram/{ngram.pk}/")
    assert page.locator(".results li").count() == 6
    assert page.locator(".results b").first.inner_text().lower().endswith("stanbul")


def test_uploading_a_document_and_analysing_produces_ngrams(page, live_server, browser_user):
    """Issue #13 - documents arrive through the browser, not a folder."""
    login(page, live_server)
    page.fill("#id_name", "Uploaded")
    page.fill("#id_language", "tr")
    page.click('button:has-text("Create")')

    with tempfile.TemporaryDirectory() as directory:
        sample = pathlib.Path(directory) / "istanbul.txt"
        sample.write_text(ISTANBUL_TEXT, encoding="utf-8")
        page.set_input_files("#id_files", str(sample))
        page.click('button:has-text("Upload")')

    page.click('button:has-text("Analyse")')
    page.click('a:has-text("#1")')
    assert page.locator(".ngrams li", has_text="İstanbul").count() == 1


def test_another_users_corpus_is_not_reachable(page, live_server, browser_corpus, django_user_model):
    """Multi-user isolation, exercised through the browser."""
    django_user_model.objects.create_user("mehmet", password=PASSWORD)
    page.goto(f"{live_server.url}/accounts/login/")
    page.fill("#id_username", "mehmet")
    page.fill("#id_password", PASSWORD)
    page.click("button[type=submit]")

    response = page.goto(f"{live_server.url}/corpus/{browser_corpus.pk}/")
    assert response.status == 404


def test_filter_box_narrows_the_list(page, live_server, browser_corpus):
    """Filtering folds the query, so an all-caps Turkish search still hits."""
    login(page, live_server)
    page.goto(f"{live_server.url}/corpus/{browser_corpus.pk}/ngrams/1/")
    assert page.locator(".ngrams li").count() > 1

    page.fill('input[name="q"]', "İSTANBUL")
    page.click('button:has-text("Filter")')

    assert page.locator(".ngrams li").count() == 1
    assert page.locator(".ngrams li").first.inner_text().find("İstanbul") != -1
