# CorpusFrequency

Analysing the most frequent words and phrases in a corpus.

Useful for making a list of the most common vocabulary from a corpus of documents in a particular domain. You can import documents that are a good representation of the content regularly used in a particular domain (e.g. transcripts of online meetings held in English by a particular company). CorpusFrequency will then identify the most common words (1-gram), combinations of 2 words that regularly appear together (2-gram), 3 word combinations (3-gram) etc...
- Examples of the most common 1-grams: and, the, ...
- Examples of the most common 2-grams: so that, for example
- Example of the most common 3-grams: in order that ...

Linguistics theory suggests such repeated phrases should be memorized like vocabulary rather than broken down and tried to understand as individual words.

A frequency list is a useful shortcut for language learning in order to quickly become familiar and fluent with the terms being used in a particular domain.

For each n-gram identified, you are presented with samples of it appearing in context to allow you to provide an illustrative example.

# Running it

A Django application. Each user owns their own corpora; uploaded documents are parsed for text and the original files are not retained.

## Requirements

* Python 3.14
* [uv](https://docs.astral.sh/uv/) for dependency management
* PostgreSQL in deployment; SQLite is the default for local work

## Local setup

```
uv sync
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

Then open http://127.0.0.1:8000 and log in.

## Using it

1. Create a corpus, choosing its language. `tr` or `az` enable Turkish dotted/dotless i handling; anything else uses the Unicode default.
2. Upload documents (`.docx`, `.pdf`, `.json`, `.txt`, `.md`, `.csv`).
3. Analyse. This builds 1- to 6-grams, merging case variants and dropping anything appearing fewer than 4 times.
4. Work through the n-gram lists, ticking the ones worth keeping and writing an example sentence for each. The lists are paged, with a filter box that folds your query to the corpus language &mdash; searching `İSTANBUL` finds the n-gram stored as `istanbul`.
5. "Needs a description" lists everything ticked that still has no example sentence.
6. Export to CSV.

## Ranking by importance rather than frequency

The most frequent words in any corpus are `the` and `and`, which teach a
learner nothing about the domain. To find the vocabulary that is actually
characteristic of it, upload a second corpus of general language, mark it as
a **control**, and set it as the target corpus's "score against" in Settings.

Each n-gram is then scored as the log ratio of its frequency here against its
frequency in the control, weighted by the log of its count. Positive means
characteristic of the domain, near zero means general language, negative means
under-represented. The n-gram lists gain a "By importance" ordering.

Documents can be added at any point. Re-analysing refreshes the counts and keeps every selection and example sentence you have already written.

## Configuration

| Variable | Purpose | Default |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | Required in deployment | insecure dev key |
| `DJANGO_DEBUG` | `1` for local development | `1` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated | `localhost,127.0.0.1` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Comma-separated | empty |
| `DATABASE_URL` | Postgres connection string | local SQLite |
| `CORPUS_MAX_UPLOAD_BYTES` | Per-file upload cap | 20 MB |
| `DJANGO_SSL_REDIRECT` | Redirect HTTP to HTTPS when not in debug | `1` |
| `DJANGO_HSTS_SECONDS` | HSTS max-age when not in debug | 1 year |

Run `uv run python manage.py check --deploy` before going live; it should
report no issues once `DJANGO_SECRET_KEY` is set to a long random value.

## Running the tests

```
uv sync --group dev
uv run playwright install chromium
uv run pytest
```

# Methodology

Scikit learn has a class called CountVectorizer that allows you to process a lot of text and extract the frequency of each ngram. You can them skim off the most frequent ngrams, and you can determine the range of n to search. https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.CountVectorizer.html

Case variants are merged after counting rather than by lowercasing the input, because `str.lower()` is locale-independent and mangles Turkish: it expands `İ` into two codepoints and maps `I` to dotted `i` rather than dotless `ı`. See `corpus/case_folding.py`.
