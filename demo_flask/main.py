from flask import Flask, jsonify, request, render_template
app = Flask(__name__)

import numpy as np
from gensim.summarization import bm25
from gensim.utils import simple_preprocess
from gensim import corpora

texts = [simple_preprocess(line, deacc=True) for line in open('../test_data/cranfield.dat', encoding='utf-8')]

dictionary = corpora.Dictionary(texts)
corpus = [dictionary.doc2bow(text) for text in texts]

bm25obj = bm25.BM25(corpus)

@app.route('/', methods=['GET', 'POST'])
def index():
    result = False
    if request.method == 'POST':
        form = request.form
        result = intelligent_matching(form)
        #print('query: {0}'.format(form['query']))
    return render_template('index.html', result=result)

def intelligent_matching(form):
  query_texts = [simple_preprocess(form['query'], deacc=True)]
  #query_texts = form['query'].split(' ')
  print(query_texts)
  query_bow = [dictionary.doc2bow(text) for text in query_texts]
  print(query_bow)
  scores = bm25obj.get_scores(query_bow)
  rank_doc_inds = np.argsort(scores)

  top_rank_doc_ind = rank_doc_inds[-1]

  result = ' '.join(texts[top_rank_doc_ind])

  return result

if __name__ == "__main__":
  app.run(debug=True)