import nltk, read
nltk.download("punkt")

file_contents = []

with open("output.txt", "r") as file:
    file_contents = file.read().split("\n")

file_contents = [[file_contents[2*index], file_contents[2*index+1]] for index in range(int(len(file_contents)/2))]

for i in range(len(file_contents)):
    file_contents[i][1] = nltk.tokenize.sent_tokenize(file_contents[i][1])

def search(ngram):
    ngram = ngram.replace("%20", " ")
    results = []
    for name, content in file_contents:
        for sentence in content:
            _sentence = list(sentence)
            location = sentence.lower().find(ngram)
            if location == -1: continue
            _sentence.insert(location, "<b>")
            _sentence.insert(location + len(ngram) + 1, "</b>")

            results.append({
                "fileName": name, 
                "markup_sentence": ''.join(_sentence),
                "sentence": sentence
            })
    return results
