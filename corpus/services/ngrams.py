"""Build the merged n-gram list for a corpus."""

from django.db import transaction
from django.utils import timezone
from sklearn.feature_extraction.text import CountVectorizer

from corpus.models import MAX_N, MIN_FREQUENCY, Ngram, Sentence


def count_ngrams(corpus, texts, min_frequency=MIN_FREQUENCY):
    """Return {n: {key: (display, count)}} for `texts`.

    CountVectorizer runs with lowercase=False so the original casing
    survives for display; folding afterwards is what merges the case
    variants back together under one key. Folding uses `corpus`'s
    language, which is why scoring passes the *target* corpus when
    counting a control corpus - both sides have to land in one key space
    to be comparable.

    `min_frequency` is lowered to 1 by the contrastive scoring, which needs
    the true totals rather than the visible-n-gram totals.
    """
    counted = {}
    for n in range(1, MAX_N + 1):
        counted[n] = {}
        if not texts:
            continue
        vectorizer = CountVectorizer(ngram_range=(n, n), lowercase=False)
        try:
            matrix = vectorizer.fit_transform(texts)
        except ValueError:
            # Raised when the corpus yields no usable tokens at all.
            continue
        terms = vectorizer.get_feature_names_out()
        frequencies = matrix.sum(axis=0).A1

        merged = {}
        # Most frequent casing first, so that is the one kept for display:
        # a corpus writing 'İstanbul' three times and 'istanbul' twice
        # should show the correctly-spelled form.
        ordered = sorted(zip(terms, frequencies), key=lambda pair: -pair[1])
        for term, frequency in ordered:
            key = corpus.fold(term)
            if key in merged:
                display, running = merged[key]
                merged[key] = (display, running + int(frequency))
            else:
                merged[key] = (term, int(frequency))

        # The frequency cut belongs here, after merging. Applied to the raw
        # terms it would discard the case variants that together clear it.
        counted[n] = {
            key: value for key, value in merged.items() if value[1] >= min_frequency
        }
    return counted


@transaction.atomic
def rebuild(corpus):
    """Recompute `corpus`'s n-grams without discarding the user's work.

    Counts are refreshed in place, so selections and chosen example
    sentences survive documents being added later. An n-gram that has
    dropped below the frequency cut is removed only if the user never
    selected it; deleting selected work would lose exactly what this is
    meant to protect.
    """
    texts = list(
        Sentence.objects.filter(document__corpus=corpus).values_list("text", flat=True)
    )
    counted = count_ngrams(corpus, texts)

    existing = {(ngram.n, ngram.key): ngram for ngram in corpus.ngrams.all()}
    seen = set()
    to_create = []
    to_update = []

    for n, entries in counted.items():
        for key, (display, count) in entries.items():
            seen.add((n, key))
            ngram = existing.get((n, key))
            if ngram is None:
                to_create.append(
                    Ngram(corpus=corpus, n=n, key=key, display=display, count=count)
                )
            elif ngram.count != count or ngram.display != display:
                ngram.count = count
                ngram.display = display
                to_update.append(ngram)

    Ngram.objects.bulk_create(to_create, batch_size=1000)
    Ngram.objects.bulk_update(to_update, ["count", "display"], batch_size=1000)

    stale = [
        ngram.pk
        for (n, key), ngram in existing.items()
        if (n, key) not in seen and not ngram.selected and not ngram.chosen_text
    ]
    Ngram.objects.filter(pk__in=stale).delete()

    corpus.analysed_at = timezone.now()
    corpus.save(update_fields=["analysed_at"])

    return {"created": len(to_create), "updated": len(to_update), "removed": len(stale)}
