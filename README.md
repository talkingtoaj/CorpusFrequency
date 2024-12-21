# Usage
Place the word documents in a folder called 'input_files'

Only reads *.docx files.

## Starting up
* Install the pipfile dependencies by using pipenv
* Remove output.txt in root directory if it exists
* Add the files you want to be analysed in the input_files folder (remove the SAMPLE.docx file in there currently)
* run `python app.py` to being


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
