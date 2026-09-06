from flask import Flask, render_template, request, make_response
from get_ngrams import results, MAX_N
from find_sentences import search
import pickle, csv, io, os
app = Flask(__name__)

STATE_FILE = os.environ.get("CORPUS_STATE_FILE", "state")

ngram_groups = {}
ngrams_to_n = {}


def migrate(entry):
    """Bring a state entry loaded from an older pickle up to date.

    `selected` used to be implied by `chosen_text` being non-empty, which
    meant an n-gram could not be marked as wanted before an example
    sentence had been picked for it. Existing saved work is preserved by
    reading that old implication once, on load.
    """
    if "selected" not in entry:
        entry["selected"] = entry.get("chosen_text", "") != ""
    return entry


def load():
    global ngram_groups
    global ngrams_to_n
    ngram_groups = {}
    ngrams_to_n = {}
    try:
        with open(STATE_FILE, "rb") as file:
            ngram_groups = pickle.load(file)
        for groups in ngram_groups.values():
            for entry in groups.values():
                migrate(entry)
    except FileNotFoundError:
        for n in range(1, MAX_N + 1):
            ngram_groups[str(n)] = {
                result[0]: {
                    "ngram": result[0],
                    "count": result[1],
                    "selected": False,
                    "chosen_text": "",
                } for result in results[str(n)]
            }
    for n, groups in ngram_groups.items():
        for ngram in groups:
            ngrams_to_n[ngram] = n

load()


@app.context_processor
def inject_max_n():
    """Make MAX_N available to nav.html so the tabs match what was built."""
    return {"max_n": MAX_N}


@app.route("/")
def home():
    return render_template("nav.html")

@app.route("/save-text", methods=["POST"])
def choose():
    ngram = request.form['ngram']
    n = ngrams_to_n[ngram]
    chosen_text = request.form["chosen_text"]
    ngram_groups[n][ngram]["chosen_text"] = chosen_text
    # Picking an example sentence for an n-gram necessarily means keeping it.
    # Clearing the text is not the same as dropping the n-gram, though, so
    # `selected` is never turned off here - only by the checkbox.
    if chosen_text != "":
        ngram_groups[n][ngram]["selected"] = True
    save_state()
    return ""

@app.route("/toggle-selected", methods=["POST"])
def toggle_selected():
    ngram = request.form["ngram"]
    n = ngrams_to_n[ngram]
    ngram_groups[n][ngram]["selected"] = request.form["selected"] == "true"
    save_state()
    return ""

@app.route("/ngrams/<n>")
def ngrams(n):
    return render_template("ngrams.html", list=ngram_groups[n].values())

@app.route("/sentences/<ngram>")
def sentences(ngram):
    n = ngrams_to_n[ngram]
    return render_template("sentence_view.html", results=search(ngram), ngram=ngram, chosen_text=ngram_groups[n][ngram]["chosen_text"])

@app.route("/export")
def export():
    si = io.StringIO()

    fieldnames = ['ngram', 'sentence']
    writer = csv.DictWriter(si, fieldnames=fieldnames)

    writer.writeheader()
    for group in ngram_groups.values():
        for ngram, value in group.items():
            if value['selected']:
                writer.writerow({'ngram': ngram, 'sentence': value['chosen_text']})
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
