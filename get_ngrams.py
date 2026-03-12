from sklearn.feature_extraction.text import CountVectorizer
import read
import nltk, read
from alphabet_conversion import convert_to_lower_case
nltk.download("punkt")

file_contents = []

with open("output.txt", "r", encoding='utf-8') as file:
    file_contents = file.read().split("\n")

file_contents = [line for line in file_contents if not line.count("SOURCE-FILE") > 0]

sentences = []
for line in file_contents:
    sentences.extend(nltk.tokenize.sent_tokenize(line))

results = {}
stop_word_list = None
for n in range(1,7):
    vectorizer = CountVectorizer(ngram_range=(n,n), stop_words=stop_word_list, lowercase=False)
    X = vectorizer.fit_transform(sentences)
    terms = vectorizer.get_feature_names_out()

    freqs = X.sum(axis=0).A1
    result_pairs = sorted([pair for pair in zip(terms, freqs) if pair[1] >=4], key=lambda pair: -pair[1])
    # combine uppercase with lowercase
    result_dict = dict()
    for pair in result_pairs:
        title = pair[0]
        freq = pair[1]
        converted_title = convert_to_lower_case(title)
        if result_dict.get(converted_title) is None:
            # store the non-lowercase version with frequency
            result_dict[converted_title] = pair
        else:
            # add the frequency
            original_title = result_dict[converted_title][0]
            original_freq = result_dict[converted_title][1]
            result_dict[converted_title] = (original_title, original_freq + freq)

    results[str(n)] = sorted([pair for pair in result_dict.values() if pair[1] >=4], key=lambda pair: -pair[1])
    