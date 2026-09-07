"""Sentence tokenisation.

nltk's tokeniser needs a data download. Doing that at import time (as the
original scripts did) means a network call on every process start, so it
is done once, lazily, on first use instead.
"""

import functools

import nltk


@functools.cache
def _ensure_punkt():
    # nltk 3.9 renamed this data from "punkt" to "punkt_tab"; asking for the
    # old name raises LookupError when the tokeniser is actually used.
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        nltk.download("punkt_tab", quiet=True)


def sentences(text):
    """Split `text` into sentences, discarding blank ones."""
    _ensure_punkt()
    found = []
    for line in text.splitlines():
        for sentence in nltk.tokenize.sent_tokenize(line):
            sentence = sentence.strip()
            if sentence:
                found.append(sentence)
    return found
