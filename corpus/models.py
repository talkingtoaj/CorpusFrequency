from django.conf import settings
from django.db import models

from corpus.case_folding import convert_to_lower_case, fold_preserving_length

# Longest n we build. Kept here because both the ingest pipeline and the
# navigation need to agree on it.
MAX_N = 6

# n-grams occurring fewer times than this are noise. Applied only after
# case variants have been merged - filtering earlier throws away exactly
# the split n-grams the folding exists to recombine.
MIN_FREQUENCY = 4


class Corpus(models.Model):
    """A collection of documents analysed together.

    A control corpus is one of general language, used to work out which
    n-grams are actually characteristic of a target corpus rather than
    merely common (see the importance scoring in `services.scoring`).
    """

    TARGET = "target"
    CONTROL = "control"
    KIND_CHOICES = [
        (TARGET, "Target - the domain you want vocabulary for"),
        (CONTROL, "Control - general language to compare against"),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="corpora", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=200)
    kind = models.CharField(max_length=16, choices=KIND_CHOICES, default=TARGET)
    # Drives case folding: Turkish and Azeri need the dotted/dotless i
    # special case, every other language uses the Unicode default.
    language = models.CharField(
        max_length=8,
        default="tr",
        help_text="ISO code. 'tr' or 'az' enable Turkish dotted/dotless i handling.",
    )
    control_corpus = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="scored_targets",
        help_text="Control corpus to score this one's n-grams against.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    analysed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "corpora"
        constraints = [
            models.UniqueConstraint(fields=["owner", "name"], name="unique_corpus_name_per_owner")
        ]
        ordering = ["name"]

    def __str__(self):
        return self.name

    def fold(self, text):
        """Fold `text` using this corpus's language."""
        return convert_to_lower_case(text, self.language)

    def fold_preserving_length(self, text):
        """Fold `text` keeping offsets usable as indices into the original."""
        return fold_preserving_length(text, self.language)

    @property
    def is_stale(self):
        """True when documents have been added since the last analysis."""
        if self.analysed_at is None:
            return self.documents.exists()
        return self.documents.filter(uploaded_at__gt=self.analysed_at).exists()


class Document(models.Model):
    """One uploaded file. Only the extracted text is retained."""

    corpus = models.ForeignKey(Corpus, related_name="documents", on_delete=models.CASCADE)
    filename = models.CharField(max_length=500)
    text = models.TextField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["filename"]

    def __str__(self):
        return self.filename


class Sentence(models.Model):
    """A sentence from a document, stored twice.

    `text` keeps the original casing because it is what gets displayed;
    `folded_text` is what gets matched against, and the two are the same
    length so a match offset in one can index into the other.
    """

    document = models.ForeignKey(Document, related_name="sentences", on_delete=models.CASCADE)
    text = models.TextField()
    folded_text = models.TextField()

    class Meta:
        indexes = [models.Index(fields=["document"])]


class Ngram(models.Model):
    """A merged n-gram and the user's decisions about it.

    `selected` is deliberately independent of `chosen_text`: an n-gram can
    be marked as worth keeping before anyone has written an example
    sentence for it, which is what makes the "needs a description" view
    possible.
    """

    corpus = models.ForeignKey(Corpus, related_name="ngrams", on_delete=models.CASCADE)
    n = models.PositiveSmallIntegerField()
    # The case-folded form, used as the identity of the n-gram.
    key = models.CharField(max_length=500)
    # The first-seen original casing, used for display.
    display = models.CharField(max_length=500)
    count = models.PositiveIntegerField()
    # Contrastive score against the corpus's control, null until scored.
    importance = models.FloatField(null=True, blank=True)
    selected = models.BooleanField(default=False)
    chosen_text = models.TextField(blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["corpus", "n", "key"], name="unique_ngram_per_corpus")
        ]
        indexes = [
            models.Index(fields=["corpus", "n", "-count"]),
            models.Index(fields=["corpus", "selected"]),
        ]
        ordering = ["-count"]

    def __str__(self):
        return self.display

    @property
    def needs_description(self):
        return self.selected and not self.chosen_text
