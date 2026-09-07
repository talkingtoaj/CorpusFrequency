"""Contrastive scoring: which n-grams are characteristic of a corpus.

Raw frequency answers the wrong question. The most frequent words in a
corpus of sport writing are 'the' and 'and', which tell a learner nothing
about sport. What matters is how much *more* often an n-gram appears here
than in general language, tempered by how common it is - a word appearing
once in one article is noise, however distinctive it looks.

So each n-gram is scored as the log ratio of its frequency in this corpus
against its frequency in a control corpus of general language, multiplied
by the log of its count. Positive means characteristic of this domain,
near zero means general language, negative means under-represented.
"""

import math

from django.db import transaction

from corpus.models import Ngram, Sentence
from corpus.services.ngrams import count_ngrams

# Add-alpha smoothing. Stops a divide-by-zero for n-grams absent from the
# control corpus, and stops those n-grams scoring arbitrarily high.
ALPHA = 1.0


def full_counts(corpus, source):
    """Count every n-gram of `source`, in `corpus`'s key space.

    Counts the whole distribution rather than only n-grams clearing
    MIN_FREQUENCY, because these totals are the denominator of a frequency
    ratio. Both sides must be counted the same way: totalling only the
    visible n-grams on one side and the whole distribution on the other
    understates that side's denominator and biases every score.
    """
    texts = list(
        Sentence.objects.filter(document__corpus=source).values_list("text", flat=True)
    )
    return count_ngrams(corpus, texts, min_frequency=1)


def control_counts(corpus, control):
    """Count `control`'s n-grams in `corpus`'s key space."""
    return full_counts(corpus, control)


@transaction.atomic
def rescore(corpus):
    """Recompute `corpus.importance` for every n-gram.

    Clears the scores when no control corpus is set, so a stale ranking is
    never left behind looking authoritative.
    """
    control = corpus.control_corpus
    if control is None:
        cleared = corpus.ngrams.exclude(importance=None).update(importance=None)
        return {"scored": 0, "cleared": cleared}

    counted = full_counts(corpus, control)
    target_counted = full_counts(corpus, corpus)

    scored = []
    for n in sorted(counted):
        ngrams = list(corpus.ngrams.filter(n=n))
        if not ngrams:
            continue

        control_for_n = counted.get(n, {})
        # Totals over the full distribution on both sides - see full_counts.
        target_total = sum(count for _, count in target_counted.get(n, {}).values())
        control_total = sum(count for _, count in control_for_n.values())
        if not target_total or not control_total:
            continue

        for ngram in ngrams:
            control_count = control_for_n.get(ngram.key, (None, 0))[1]
            target_frequency = (ngram.count + ALPHA) / (target_total + ALPHA)
            control_frequency = (control_count + ALPHA) / (control_total + ALPHA)
            distinctiveness = math.log(target_frequency / control_frequency)
            # Weighted by count so that a distinctive-but-rare n-gram does
            # not outrank one that is distinctive and actually common.
            ngram.importance = distinctiveness * math.log(1 + ngram.count)
            scored.append(ngram)

    Ngram.objects.bulk_update(scored, ["importance"], batch_size=1000)
    return {"scored": len(scored), "cleared": 0}
