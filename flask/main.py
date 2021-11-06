from flask import Flask, jsonify, request
app = Flask(__name__)

import numpy as np
from gensim.summarization import bm25

# https://stackoverflow.com/questions/50009030/correct-way-of-using-phrases-and-preprocess-string-gensim
from gensim.parsing.preprocessing import preprocess_string, remove_stopwords, stem_text
from gensim.utils import tokenize
from gensim.corpora import Dictionary
from gensim.summarization.textcleaner import get_sentences

"When returning HTML (the default response type in Flask), " \
"any user-provided values rendered in the output must be escaped to protect from injection attacks. " \
"HTML templates rendered with Jinja, introduced later, will do this automatically."
#from markupsafe import escape


@app.route('/search', methods=['POST'])
def words():
    if request.method == 'POST':
        request_data = request.get_json()
        query = request_data['search_text']
        documents = request_data['doc_content']['text_nodes']
        #custom_filters = [remove_stopwords, stem_text]
        custom_filters = [stem_text]
        #custom_filters = []

        result = intelligent_matching(query, documents, custom_filters=custom_filters)
        print('result: ', result)

    return jsonify(result)


def intelligent_matching(query, text_nodes, custom_filters=[]):

    #print('query: ', query)

    documents = []
    map_to_text_node = []
    print('text nodes', text_nodes)
    for node_ind, text_node in enumerate(text_nodes):
        # replace new line character with space to prevent
        # get_sentences from splitting the text nodes at new line characters
        # needed for website that has \n within sentences such as
        # https://numpy.org/doc/stable/reference/generated/numpy.intersect1d.html
        text_node = text_node.replace('\n', ' ')

        # get_sentences extract sentences based on pattern set in RE_SENTENCE
        # by default,  gensim.summarization.textcleaner.RE_SENTENCE
        #  == re.compile(r'(\S.+?[.!?])(?=\s+|$)|(\S.+?)(?=[\n]|$)', re.UNICODE)
        for sentence in get_sentences(text_node):
            documents.append(sentence)
            offset = text_node.find(sentence)
            map_to_text_node.append([node_ind, offset])

    print('documents: ', documents)

    query_tokens = list(tokenize(query, lower=True))
    print(query_tokens)
    query_tokens = preprocess_string(" ".join(query_tokens), custom_filters)
    #print('query_tokens: ', query_tokens)

    doc_tokens = [list(tokenize(doc, lower=True)) for doc in documents]
    doc_tokens = [preprocess_string(" ".join(doc), custom_filters) for doc in doc_tokens]
    #print('doc_tokens: ', doc_tokens)

    dictionary = Dictionary(doc_tokens)

    doc_bow = [dictionary.doc2bow(text) for text in doc_tokens]
    query_bow = dictionary.doc2bow(query_tokens)

    #print('doc_bow: ', doc_bow)
    #print('query_bow: ', query_bow)

    bm25obj = bm25.BM25(doc_bow)
    result = []
    if len(query_bow):
        scores = bm25obj.get_scores(query_bow)
        rank_doc_inds = np.argsort(scores)
        #rank_doc_inds = np.arange(0, len(scores))[::-1]

        for ii in range(len(rank_doc_inds)-1, -1, -1):

            # json does not recognize numpy object/int
            # cast number as int
            ind = int(rank_doc_inds[ii]); # document index

            # skip document with ranking score = 0
            # breaking out of the loop assumes that the
            # scores are ordered from highest to lowest
            if scores[ind] == 0:
                continue

            #print('score = ', scores[ind])
            # for single_word_query in query_tokens:
            #     # index of first character in text node matching the query
            #     ind_char = documents[ind].lower().find(single_word_query); # find returns -1 if substring not found
            #     if ind_char == -1:
            #         continue
            #     result.append({'index': ind, 'offsets': [ind_char, ind_char+len(single_word_query)]})

            # returns the entire text node
            #result.append({'index': ind, 'offsets': [0, len(documents[ind])]})
            # return the entire sentence
            node_ind = map_to_text_node[ind][0]
            offset = map_to_text_node[ind][1]
            result.append({'index': node_ind, 'offsets': [offset, offset+len(documents[ind])]})

    return result


if __name__ == "__main__":
  app.run(debug=True, port=8080)