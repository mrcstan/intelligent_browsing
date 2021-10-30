from flask import Flask, jsonify, request, render_template
app = Flask(__name__)

import numpy as np
from gensim.summarization import bm25
from gensim.utils import simple_preprocess
from gensim import corpora

"When returning HTML (the default response type in Flask), " \
"any user-provided values rendered in the output must be escaped to protect from injection attacks. " \
"HTML templates rendered with Jinja, introduced later, will do this automatically."
from markupsafe import escape

'''
texts = [simple_preprocess(line, deacc=True) for line in open('../test_data/cranfield.dat', encoding='utf-8')]

dictionary = corpora.Dictionary(texts)
corpus = [dictionary.doc2bow(text) for text in texts]

bm25obj = bm25.BM25(corpus)
'''


@app.route('/search', methods=['POST'])
def words():
    if request.method == 'POST':
        request_data = request.get_json()
        query = request_data['search_text']
        documents = request_data['doc_content']['text_nodes']

        print('query: ', query)
        print('documents: ', documents)
        result = intelligent_matching(query, documents)
        print('result: ', result)

    return jsonify(result)


def intelligent_matching(query, documents):
    query_texts = [simple_preprocess(query, deacc=True)]
    doc_texts = [simple_preprocess(doc, deacc=True) for doc in documents]
    dictionary = corpora.Dictionary(doc_texts)
    doc_bow = [dictionary.doc2bow(text) for text in doc_texts]
    query_bow = [dictionary.doc2bow(text) for text in query_texts]
    print('doc_bow = ', doc_bow)
    print('query_bow = ', query_bow)

    bm25obj = bm25.BM25(doc_bow)
    result = []
    if len(query_bow[0]):
        scores = bm25obj.get_scores(query_bow[0])

        rank_doc_inds = np.argsort(scores)

        for ii in range(len(rank_doc_inds)-1, -1, -1):
            ind = rank_doc_inds[ii]
            result.append({'index': ind, 'offsets': [ind, ind+len(query_bow)-1]})

    return result


if __name__ == "__main__":
  app.run(debug=True)