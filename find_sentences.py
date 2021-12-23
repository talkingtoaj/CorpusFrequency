import nltk, read
import re
nltk.download("punkt")

file_contents = []

with open("output.txt", "r", encoding='utf-8') as file:
    file_contents = file.read().split("\n")

file_contents = [[file_contents[2*index], file_contents[2*index+1]] for index in range(int(len(file_contents)/2))]

for i in range(len(file_contents)):
    file_contents[i][1] = nltk.tokenize.sent_tokenize(file_contents[i][1])

def search(ngram):
    ngram = ngram.replace("%20", " ").upper()
    # set word boundaries (\b) and allow spaces to also represent stripped non-alphanumeric characters (\W)
    re_ngram = re.compile(r"\b" + ngram.replace(' ',r'\W') + r"\b")
    results = []
    for name, content in file_contents:
        for sentence in content:
            # find location of regex pattern re_ngram in sentence
            match = re_ngram.search(sentence.upper())
            if match is None: 
                continue
            match_start = match.start()
            match_end = match.end()
            start = max(0, match_start-60)
            end = min(len(sentence), match_end+60)

            truncated_sentence = sentence[start:end]
            match = re_ngram.search(truncated_sentence.upper())
            match_start = match.start()
            match_end = match.end()
            markup_sentence = truncated_sentence[:match_start] + "<b>" + truncated_sentence[match_start:match_end] + "</b>" + truncated_sentence[match_end:]
            results.append({
                "fileName": name, 
                "markup_sentence": markup_sentence,
                "sentence": truncated_sentence
            })
    return results
