from sklearn.feature_extraction.text import CountVectorizer

file_contents = []

with open("output.txt", "r") as file:
    file_contents = file.read().split("\n")

file_contents = [line for line in file_contents if not line.count("SOURCE-FILE") > 0]

print(file_contents)

vectorizer = CountVectorizer(ngram_range=(2,2))
X = vectorizer.fit_transform(file_contents)
terms = vectorizer.get_feature_names()

freqs = X.sum(axis=0).A1

result = list(zip(terms, freqs))

print(sorted(result, key=lambda x: x[1]))