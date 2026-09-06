"""Browser tests for issue #7 - the checkbox must both select and deselect.

The regression these guard against is subtle: the checkbox used to render
purely from server state and fire no request, so it *looked* interactive
but nothing survived a reload.
"""

import os
import pathlib
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

import pytest

playwright_api = pytest.importorskip("playwright.sync_api")
sync_playwright = playwright_api.sync_playwright

REPO_ROOT = pathlib.Path(__file__).parent.parent
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "input_files"


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="module")
def server():
    """Run the real Flask app against the fixture corpus."""
    port = free_port()
    scratch = tempfile.mkdtemp(prefix="corpusfrequency-ui-")
    env = {
        **os.environ,
        "CORPUS_INPUT_FOLDER": str(FIXTURES),
        "CORPUS_OUTPUT_FILE": str(pathlib.Path(scratch) / "output.txt"),
        "CORPUS_STATE_FILE": str(pathlib.Path(scratch) / "state"),
        "FLASK_APP": "app.py",
    }
    process = subprocess.Popen(
        [sys.executable, "-m", "flask", "run", "--port", str(port)],
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    base_url = f"http://127.0.0.1:{port}"
    try:
        deadline = time.time() + 60
        while time.time() < deadline:
            if process.poll() is not None:
                raise RuntimeError(
                    "app exited before serving:\n"
                    + process.stdout.read().decode("utf-8", "replace")
                )
            try:
                urllib.request.urlopen(base_url + "/", timeout=1)
                break
            except (urllib.error.URLError, ConnectionError, socket.timeout):
                time.sleep(0.5)
        else:
            raise RuntimeError("app did not start within 60s")
        yield base_url
    finally:
        process.terminate()
        process.wait(timeout=10)


@pytest.fixture(scope="module")
def page(server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        yield page
        browser.close()


def test_ngrams_page_lists_the_merged_turkish_ngram(page, server):
    page.goto(f"{server}/ngrams/1")
    assert page.locator("text=İstanbul - 6").count() == 1


def test_checkbox_starts_unchecked(page, server):
    page.goto(f"{server}/ngrams/1")
    assert page.locator(".ngram-checkbox").first.is_checked() is False


def test_checkbox_can_select_and_the_choice_survives_reload(page, server):
    """This is the actual bug in issue #7: selecting did not persist."""
    page.goto(f"{server}/ngrams/1")
    checkbox = page.locator('.ngram-checkbox[data-ngram="İstanbul"]')
    checkbox.check()
    page.wait_for_timeout(300)

    page.reload()
    assert page.locator('.ngram-checkbox[data-ngram="İstanbul"]').is_checked() is True


def test_checkbox_can_deselect_and_that_survives_reload(page, server):
    page.goto(f"{server}/ngrams/1")
    checkbox = page.locator('.ngram-checkbox[data-ngram="İstanbul"]')
    assert checkbox.is_checked() is True

    checkbox.uncheck()
    page.wait_for_timeout(300)

    page.reload()
    assert page.locator('.ngram-checkbox[data-ngram="İstanbul"]').is_checked() is False


def test_selection_without_a_description_is_exported(page, server):
    """`selected` is independent of `chosen_text`, which issue #8 needs."""
    page.goto(f"{server}/ngrams/1")
    page.locator('.ngram-checkbox[data-ngram="İstanbul"]').check()
    page.wait_for_timeout(300)

    csv_text = urllib.request.urlopen(f"{server}/export").read().decode("utf-8")
    assert "İstanbul" in csv_text
    # selected but no example sentence chosen yet - the row still exports,
    # with an empty sentence column
    assert "İstanbul," in csv_text


def test_saving_a_sentence_implies_selection(page, server):
    page.goto(f"{server}/ngrams/1")
    page.locator('.ngram-checkbox[data-ngram="Işık"]').uncheck()
    page.wait_for_timeout(300)

    page.goto(f"{server}/sentences/Işık")
    page.locator("#textarea").fill("Işık hızı çok yüksektir.")
    page.locator("text=Save").click()
    page.wait_for_timeout(300)

    page.goto(f"{server}/ngrams/1")
    assert page.locator('.ngram-checkbox[data-ngram="Işık"]').is_checked() is True
