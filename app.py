from flask import Flask, render_template, request
from get_ngrams import results
from find_phrases import search
import pickle, csv
app = Flask(__name__)

ngram_groups = {}
try:
    with open("ngram_groups", "rb") as file:
        ngram_groups = pickle.load(file)
except FileNotFoundError:
    for n in range(2, 7):
        ngram_groups[str(n)] = {
            result[0]: {
                "ngram": result[0],
                "count": result[1],
                "checked": True,
                "phrases": [],
            } for result in results[str(n)]
        }
ngrams_to_n = {}
for n, groups in ngram_groups.items():
    for ngram in groups:
        ngrams_to_n[ngram] = n

@app.route("/")
def home():
    return render_template("nav.html")

@app.route("/toggle-ngram", methods=["POST"])
def toggle():
    ngram = request.form['ngram']
    n = ngrams_to_n[ngram]
    ngram_groups[n][ngram]["checked"] = not ngram_groups[n][ngram]["checked"]
    save_state()
    return ""

@app.route("/toggle-phrase", methods=["POST"])
def choose():
    ngram = request.form['ngram']
    n = ngrams_to_n[ngram]
    phrase = request.form['phrase']
    phrases = ngram_groups[n][ngram]["phrases"]
    if phrase in phrases:
        phrases.remove(phrase)
    else:
        phrases.append(phrase)
    save_state()
    return ""

@app.route("/ngrams/<n>")
def ngrams(n):
    return render_template("ngrams.html", list=ngram_groups[n].values())

@app.route("/phrase/<ngram>")
def phrase(ngram):
    n = ngrams_to_n[ngram]
    return render_template("phrase_view.html", results=search(ngram), ngram=ngram, phrases=ngram_groups[n][ngram]["phrases"])

@app.route("/export", methods=["POST"])
def export():
    with open('phrases.csv', mode='w') as csv_file:
        fieldnames = ['ngram', 'phrase']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        writer.writeheader()
        for group in ngram_groups.values():
            for ngram, value in group.items():
                for phrase in value["phrases"]:
                    writer.writerow({'ngram': ngram, 'phrase': phrase})
    return ""

def save_state():
    with open("ngram_groups", "wb") as file:
        pickle.dump(ngram_groups, file)

if __name__ == "__main__":
    app.run(debug=False)

