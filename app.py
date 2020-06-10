from flask import Flask, render_template
from get_ngrams import results
from find_phrases import search
app = Flask(__name__)

@app.route('/phrase/<n>')
def hello_world(n):
    return render_template("ngrams.html", list=results[n])

@app.route("/word/<word>")
def word(word):
    return render_template("phrase_view.html", results=search(word))

if __name__ == "__main__":
    app.run(debug=True)