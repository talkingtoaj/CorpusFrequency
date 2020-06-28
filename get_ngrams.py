from sklearn.feature_extraction.text import CountVectorizer
import read
file_contents = []

with open("output.txt", "r") as file:
    file_contents = file.read().split("\n")

file_contents = [line for line in file_contents if not line.count("SOURCE-FILE") > 0]

#print(file_contents)

results = {}
for n in range(2,7):
    vectorizer = CountVectorizer(ngram_range=(n,n))
    X = vectorizer.fit_transform(file_contents)
    terms = vectorizer.get_feature_names()

    freqs = X.sum(axis=0).A1

    result = list(zip(terms, freqs))

    result.sort(key=lambda x: -x[1])

    result = result[:20]

    results[str(n)] = result