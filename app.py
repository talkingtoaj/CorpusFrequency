from flask import Flask, render_template, request
from get_ngrams import results
from find_phrases import search
import pickle
app = Flask(__name__)

state = {}
try:
    with open("state", "rb") as file:
        state = pickle.load(file)
except FileNotFoundError:
    for n in range(2, 7):
        state[str(n)] = {
            result[0]: {
                "ngram": result[0],
                "count": result[1],
                "checked": "checked",
            } for result in results[str(n)]
        }

@app.route("/toggle", methods=["POST"])
def toggle():
    ngram = request.form['ngram']
    n = request.form['n']
    state[n][ngram]["checked"] = "" if state[n][ngram]["checked"] == "checked" else "checked"
    save_state()
    return ""

@app.route("/phrase/<n>")
def hello_world(n):
    return render_template("ngrams.html", list=state[n].values(), n=n)

@app.route("/word/<word>")
def word(word):
    return render_template("phrase_view.html", results=search(word))

def save_state():
    with open("state", "wb") as file:
        pickle.dump(state, file)

if __name__ == "__main__":
    app.run(debug=False)

