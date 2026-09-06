import os

import nltk
from sklearn.feature_extraction.text import CountVectorizer

import read  # noqa: F401  - imported for its side effect of writing OUTPUT_FILE
from case_folding import convert_to_lower_case

# nltk 3.9 renamed the sentence tokeniser data from "punkt" to
# "punkt_tab"; asking for the old name raises LookupError on first use.
nltk.download("punkt_tab", quiet=True)

OUTPUT_FILE = os.environ.get("CORPUS_OUTPUT_FILE", "output.txt")

# n-grams appearing fewer times than this are treated as noise and dropped
MIN_FREQUENCY = 4

# largest n we build n-grams for; range(1, MAX_N + 1) is used throughout
MAX_N = 6

file_contents = []

with open(OUTPUT_FILE, "r", encoding='utf-8') as file:
    file_contents = file.read().split("\n")

file_contents = [line for line in file_contents if not line.count("SOURCE-FILE") > 0]

sentences = []
for line in file_contents:
    sentences.extend(nltk.tokenize.sent_tokenize(line))

results = {}
stop_word_list = None
for n in range(1, MAX_N + 1):
    vectorizer = CountVectorizer(ngram_range=(n,n), stop_words=stop_word_list, lowercase=False)
    X = vectorizer.fit_transform(sentences)
    terms = vectorizer.get_feature_names_out()

    freqs = X.sum(axis=0).A1
    # Deliberately unfiltered: the MIN_FREQUENCY cut has to happen *after*
    # the case variants below are merged. Applying it here would discard
    # 'İstanbul' (3), 'istanbul' (2) and 'İSTANBUL' (1) separately instead
    # of keeping the combined n-gram with a frequency of 6.
    result_pairs = sorted(zip(terms, freqs), key=lambda pair: -pair[1])
    # combine uppercase with lowercase
    result_dict = dict()
    for pair in result_pairs:
        title = pair[0]
        freq = pair[1]
        # CountVectorizer runs with lowercase=False so that the original
        # casing survives for display; folding here is what merges the
        # case variants back together under one key.
        folded_title = convert_to_lower_case(title)

        if result_dict.get(folded_title) is None:
            # store the non-lowercase version with frequency
            result_dict[folded_title] = pair
        else:
            # add the frequency
            original_title = result_dict[folded_title][0]
            original_freq = result_dict[folded_title][1]
            result_dict[folded_title] = (original_title, original_freq + freq)

    results[str(n)] = sorted([pair for pair in result_dict.values() if pair[1] >= MIN_FREQUENCY], key=lambda pair: -pair[1])
