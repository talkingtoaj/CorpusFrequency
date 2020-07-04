from flask import Flask, render_template, request, make_response
from get_ngrams import results
from find_sentences import search
import pickle, csv, io, os, time
app = Flask(__name__)

STATE_FILE = "state"

ngram_groups = {}
ngrams_to_n = {}
def load():
    global ngram_groups
    global ngrams_to_n
    ngram_groups = {}
    ngrams_to_n = {}
    try:
        with open(STATE_FILE, "rb") as file:
            ngram_groups = pickle.load(file)
    except FileNotFoundError:
        for n in range(1, 7):
            ngram_groups[str(n)] = {
                result[0]: {
                    "ngram": result[0],
                    "count": result[1],
                    "checked": False,
                    "sentences": [],
                } for result in results[str(n)]
            }
    for n, groups in ngram_groups.items():
        for ngram in groups:
            ngrams_to_n[ngram] = n

load()

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

@app.route("/toggle-sentence", methods=["POST"])
def choose():
    ngram = request.form['ngram']
    n = ngrams_to_n[ngram]
    sentence = request.form['sentence']
    sentences = ngram_groups[n][ngram]["sentences"]
    if sentence in sentences:
        sentences.remove(sentence)
    else:
        sentences.append(sentence)
    save_state()
    return ""

@app.route("/ngrams/<n>")
def ngrams(n):
    return render_template("ngrams.html", list=ngram_groups[n].values())

@app.route("/sentences/<ngram>")
def sentences(ngram):
    n = ngrams_to_n[ngram]
    return render_template("sentence_view.html", results=search(ngram), ngram=ngram, sentences=ngram_groups[n][ngram]["sentences"])

@app.route("/export")
def export():
    si = io.StringIO()

    fieldnames = ['ngram', 'sentence']
    writer = csv.DictWriter(si, fieldnames=fieldnames)

    writer.writeheader()
    for group in ngram_groups.values():
        for ngram, value in group.items():
            if value["checked"]:
                for sentence in value["sentences"]:
                    writer.writerow({'ngram': ngram, 'sentence': sentence})
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=sentences.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@app.route("/clear", methods=["POST"])
def clear():
    if os.path.isfile(STATE_FILE):
        os.remove(STATE_FILE)
    load()
    return ""



def save_state():
    with open(STATE_FILE, "wb") as file:
        pickle.dump(ngram_groups, file)


if __name__ == "__main__":
    app.run(debug=False)

