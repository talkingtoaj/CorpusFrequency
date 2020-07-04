from sklearn.feature_extraction.text import CountVectorizer
import read
file_contents = []

with open("output.txt", "r", encoding='utf-8') as file:
    file_contents = file.read().split("\n")

file_contents = [line for line in file_contents if not line.count("SOURCE-FILE") > 0]

#print(file_contents)

results = {}
for n in range(1,7):
    vectorizer = CountVectorizer(ngram_range=(n,n))
    X = vectorizer.fit_transform(file_contents)
    terms = vectorizer.get_feature_names()

    freqs = X.sum(axis=0).A1

    results[str(n)] = sorted([pair for pair in zip(terms, freqs) if pair[1] >=4], key=lambda pair: -pair[1])