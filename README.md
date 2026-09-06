# Usage

Place the word documents in a folder called 'input_files'

Reads `*.docx`, `*.pdf`, `*.json` and plain text files.

## Requirements

* Python 3.14
* [uv](https://docs.astral.sh/uv/) for dependency management

## Starting up

* Install dependencies with `uv sync`
* Remove `output.txt` in the root directory if it exists
* Add the files you want analysed to the `input_files` folder
* Run `uv run python app.py` to begin, then open http://127.0.0.1:5000

`output.txt` is the extracted-text cache. It is only regenerated when
absent, so delete it after changing the contents of `input_files`.

`state` holds your selections and chosen example sentences. The Clear
button in the UI deletes it.

## Running the tests

```
uv sync --group dev
uv run playwright install chromium
uv run pytest
```

The browser tests run the real Flask app against the small Turkish corpus
in `tests/fixtures/input_files`, so no corpus of your own is needed.

# CorpusFrequency
Analysing the most frequent words and phrases in a corpus

Useful for making a list of the most common vocabulary from a corpus of documents in a particular domain. You can import documents that are a good representation of the content regularly used in a particular domain (e.g. transcripts of online meetings held in English by a particular company). CorpusFrequency will then identify the most common words (1-gram), combinations of 2 words that regularly appear together (2-gram), 3 word combinations (3-gram) etc... 
- Examples of the most common 1-grams: and, the, ...
- Examples of the most common 2-grams: so that, for example
- Example of the most common 3-grams: in order that ...

Linguistics theory suggests such repeated phrases should be memorized like vocabulary rather than broken down and tried to understand as individual words.

A frequency list is a useful shortcut for language learning in order to quickly become familiar and fluent with the terms being used in a particular domain.

For each n-gram identified, you are presented with samples of it appearing in context to allow you to provide an illustrative example.

# Methodology
Scikit learn has a class called CountVectorizer that allows you to process a lot of text and extract the frequency of each ngram. You can them skim off the most frequent ngrams, and you can determine the range of n to search. https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.CountVectorizer.html
