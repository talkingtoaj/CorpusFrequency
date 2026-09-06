"""Find the sentences an n-gram appears in, with the match highlighted."""

import re

from corpus.models import Sentence

# How much of the surrounding sentence to show either side of a match.
CONTEXT_CHARACTERS = 60


def pattern_for(corpus, phrase):
    """Build the match pattern for `phrase` within `corpus`.

    Word boundaries keep 'ali' from matching inside 'kalabalik', and each
    space is allowed to stand for any non-word character so that the
    n-gram still matches across the punctuation the tokeniser stripped.
    """
    folded = corpus.fold_preserving_length(phrase)
    # Escape each word separately and join with \W. Escaping the whole
    # phrase first does not work: re.escape backslash-escapes spaces, so
    # replacing " " afterwards would leave that backslash stranded.
    words = [re.escape(word) for word in folded.split(" ") if word]
    return re.compile(r"\b" + r"\W".join(words) + r"\b")


def search(corpus, phrase, limit=200):
    """Return matches for `phrase`, newest document first.

    Matching happens against `folded_text`, which is the same length as
    `text`, so the offsets a match yields can slice the original sentence
    and preserve its casing for display.
    """
    expression = pattern_for(corpus, phrase)
    candidates = Sentence.objects.filter(
        document__corpus=corpus, folded_text__regex=expression.pattern
    ).select_related("document")[:limit]

    results = []
    for candidate in candidates:
        match = expression.search(candidate.folded_text)
        if match is None:
            # The database's regex dialect is close to Python's but not
            # identical; Python's answer is the one that counts.
            continue
        start = max(0, match.start() - CONTEXT_CHARACTERS)
        end = min(len(candidate.text), match.end() + CONTEXT_CHARACTERS)
        results.append(
            {
                "filename": candidate.document.filename,
                "sentence": candidate.text[start:end],
                "before": candidate.text[start:match.start()],
                "match": candidate.text[match.start():match.end()],
                "after": candidate.text[match.end():end],
            }
        )
    return results
