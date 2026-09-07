"""Browser tests driving the real application.

These cover the behaviour that unit tests cannot see: that the checkbox
actually writes to the server, and that its state survives a reload. That
is the substance of issue #7 - the old checkbox rendered from server state
but fired no request, so it looked interactive while persisting nothing.
"""

import pathlib
import tempfile
from importlib import import_module

import pytest
from django.conf import settings
from django.contrib.auth import (
    BACKEND_SESSION_KEY,
    HASH_SESSION_KEY,
    SESSION_KEY,
    get_user_model,
)

from corpus.models import Corpus
from tests.samples import ISIK_TEXT, ISTANBUL_TEXT

playwright_api = pytest.importorskip("playwright.sync_api")


@pytest.fixture
def browser_user(transactional_db, django_user_model):
    return django_user_model.objects.create_user("ayse")


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


def login(page, live_server, user=None):
    """Sign a user in without a round trip to Google.

    Sign-in is Google-only, so there is no password form to drive and no
    way to authenticate in-process against the real provider. Building the
    session directly is what the app itself ends up with after a successful
    OAuth callback, so everything downstream is exercised as normal.
    """
    if user is None:
        user = get_user_model().objects.get(username="ayse")
    engine = import_module(settings.SESSION_ENGINE)
    session = engine.SessionStore()
    session[SESSION_KEY] = str(user.pk)
    session[BACKEND_SESSION_KEY] = "django.contrib.auth.backends.ModelBackend"
    session[HASH_SESSION_KEY] = user.get_session_auth_hash()
    session.save()
    page.context.add_cookies(
        [
            {
                "name": settings.SESSION_COOKIE_NAME,
                "value": session.session_key,
                "url": live_server.url,
            }
        ]
    )


def test_login_lands_on_the_corpus_list(page, live_server, browser_user):
    login(page, live_server)
    page.goto(live_server.url)
    assert page.locator("h1", has_text="Your corpora").count() == 1


def test_signed_out_visitors_are_sent_to_the_sign_in_page(page, live_server, transactional_db):
    page.goto(live_server.url)
    assert page.locator("h1", has_text="Sign in").count() == 1


def test_sign_in_page_offers_google_and_no_password_form(page, live_server, transactional_db):
    """Sign-in is Google-only: there is no password for us to store."""
    page.goto(f"{live_server.url}/accounts/login/")
    assert page.locator('a:has-text("Sign in with Google")').count() == 1
    assert page.locator('input[type="password"]').count() == 0


def test_ngram_list_shows_the_merged_turkish_ngram(page, live_server, browser_corpus):
    login(page, live_server)
    page.goto(f"{live_server.url}/corpus/{browser_corpus.pk}/ngrams/1/")
    assert page.locator(".ngram-row", has_text="İstanbul").count() == 1
    assert page.locator(".ngram-row", has_text="İstanbul").inner_text().find("6") != -1


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
    assert page.locator(".ngrams tbody tr", has_text="İstanbul").count() == 1

    page.click('.ngrams a:has-text("İstanbul")')
    page.fill("#chosen_text", "İstanbul çok büyük bir şehirdir.")
    page.click("button[type=submit]")

    page.goto(f"{live_server.url}/corpus/{browser_corpus.pk}/needs-description/")
    assert page.locator(".ngrams tbody tr", has_text="İstanbul").count() == 0


def test_sentences_are_listed_with_the_match_highlighted(page, live_server, browser_corpus):
    login(page, live_server)
    ngram = browser_corpus.ngrams.get(n=1, key="istanbul")
    page.goto(f"{live_server.url}/ngram/{ngram.pk}/")
    assert page.locator(".results li").count() == 6
    assert page.locator(".results mark").first.inner_text().lower().endswith("stanbul")


def test_uploading_a_document_and_analysing_produces_ngrams(page, live_server, browser_user):
    """Issue #13 - documents arrive through the browser, not a folder."""
    login(page, live_server)
    page.goto(live_server.url)
    page.fill("#id_name", "Uploaded")
    page.fill("#id_language", "tr")
    page.click('button:has-text("Create")')

    with tempfile.TemporaryDirectory() as directory:
        sample = pathlib.Path(directory) / "istanbul.txt"
        sample.write_text(ISTANBUL_TEXT, encoding="utf-8")
        page.set_input_files("#id_files", str(sample))
        page.click('button:has-text("Upload")')

    page.click('button:has-text("Analyse")')
    page.click('a:has-text("1-gram")')
    assert page.locator(".ngram-row", has_text="İstanbul").count() == 1


def test_another_users_corpus_is_not_reachable(page, live_server, browser_corpus, django_user_model):
    """Multi-user isolation, exercised through the browser."""
    intruder = django_user_model.objects.create_user("mehmet")
    login(page, live_server, intruder)
    response = page.goto(f"{live_server.url}/corpus/{browser_corpus.pk}/")
    assert response.status == 404


def test_filter_box_narrows_the_list(page, live_server, browser_corpus):
    """Filtering folds the query, so an all-caps Turkish search still hits."""
    login(page, live_server)
    page.goto(f"{live_server.url}/corpus/{browser_corpus.pk}/ngrams/1/")
    assert page.locator(".ngram-row").count() > 1

    page.fill('input[name="q"]', "İSTANBUL")
    page.click('button:has-text("Filter")')

    assert page.locator(".ngram-row").count() == 1
    assert page.locator(".ngram-row").first.inner_text().find("İstanbul") != -1


def test_keyboard_triage_selects_without_the_mouse(page, live_server, browser_corpus):
    """Triaging thousands of n-grams by mouse is hours of avoidable work.

    j/k move the active row and space keeps it, so the whole list can be
    worked through from the home row.
    """
    login(page, live_server)
    page.goto(f"{live_server.url}/corpus/{browser_corpus.pk}/ngrams/1/")
    first = page.locator(".ngram-row").first

    page.keyboard.press("j")
    assert "is-active" in first.get_attribute("class")

    page.keyboard.press(" ")
    page.wait_for_timeout(400)
    page.reload()
    assert page.locator(".ngram-row").first.locator(".ngram-checkbox").is_checked() is True


def test_slash_focuses_the_filter_box(page, live_server, browser_corpus):
    login(page, live_server)
    page.goto(f"{live_server.url}/corpus/{browser_corpus.pk}/ngrams/1/")
    page.keyboard.press("/")
    assert page.evaluate("document.activeElement.id") == "filter-input"


def test_a_frequent_ngram_does_not_render_every_sentence(page, live_server, browser_corpus):
    """A common n-gram matches far more sentences than fit on one page."""
    from corpus.models import RESULT_PAGE_SIZE

    ngram = browser_corpus.ngrams.filter(n=1).order_by("-count").first()
    login(page, live_server)
    page.goto(f"{live_server.url}/ngram/{ngram.pk}/")
    assert page.locator(".results li").count() <= RESULT_PAGE_SIZE
