# Usage
Place the word documents in a folder called 'input_files'

Only reads *.docx files.

Install and activate the virtual environment

Run `python3 app.py`



Q: Do we need to run read.py to load in the new files?


# CorpusFrequency
Analysing the most frequent words and phrases in a corpus



The linguistics team is wanting to make a list of vocabulary for English learners to learn which is optimized for their future workplace.

For SE Asia, the staff will need English for emails and conversations that circle around topics common to being on Staff with our organization. So we asked the leadership of SE Asia if they could provide a corpus on materials which we can analyse to find the common words and phrases that appear in their line of work.

I have now received a large collection of word documents containing newsletters, meeting notes, emails etc. which we can analyse.

The task is to produce a frequency list of useful words and phrases in English which staff should focus on learning as part of their English development to fast-track them for their workplace.

There is a concept you may have heard of in text-based Machine Learning called n-grams. "and" is a very common 1-word English n-gram (n=number of words/tokens). "So that" would be a 2 n-gram, etc. So the larger n is, the more rarerly you will find repeating combinations, but those that do repeat are very useful to learn. "For example", "in order that" etc. Linguistics theory suggests such repeated phrases should be memorized like vocabulary rather than broken down and tried to understand according to grammar rules.  e.g. "Tabi ki", "Rica ederim", "elinize saglik" don't make much sense if you break them down by grammar, but you learn them in Turkish as a useful fixed phrase.

Scikit learn has a class called CountVectorizer that allows you to process a lot of text and extract the frequency of each ngram. You can them skim off the most frequent ngrams, and you can determine the range of n to search.  I've used it before.
https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.CountVectorizer.html

This process is one we probably will want to repeat in the future, both for English and for other languages, so we want to write a program (separate to the make GFGD project, new repository)
