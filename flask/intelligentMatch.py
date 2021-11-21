import numpy as np
from gensim.summarization import bm25
import plnVSM

# https://stackoverflow.com/questions/50009030/correct-way-of-using-phrases-and-preprocess-string-gensim
from gensim.parsing.preprocessing import preprocess_string
from gensim.utils import tokenize
from gensim.corpora import Dictionary
from gensim.summarization.textcleaner import get_sentences


class IntelligentMatch:

    def __init__(self, query, text_nodes, ranker='BM25', custom_filters=[]):
        self.query = query
        self.text_nodes = text_nodes
        self.custom_filters = custom_filters
        self.documents = []
        self.map_to_text_node = []
        self.query_tokens = []
        self.doc_tokens = []
        self.dictionary = []
        self.query_bow = []
        self.doc_bow = []
        self.scores = []
        self.rank_doc_inds = []
        self.result = []
        self.ranker = ranker

    def initialize(self):
        self.split_text_nodes_into_sentences()
        self.preprocess_query()
        self.preprocess_documents()
        self.get_query_document_bow()

    def clear_result(self):
        self.scores = []
        self.rank_doc_inds = []
        self.result = []

    def rank(self):
        if self.ranker == 'BM25':
            ranker = bm25.BM25(self.doc_bow, b=0.0)
        elif self.ranker== 'PLNVSM':
            ranker = plnVSM.PLNVSM(self.doc_bow, b=0.0)
        else:
            raise Exception('Unknown ranker')

        self.result = []
        if len(self.query_bow):
            self.scores = ranker.get_scores(self.query_bow)
            self.rank_doc_inds = np.argsort(self.scores)[::-1]

            for ii, ind in enumerate(self.rank_doc_inds):

                # jsonify does not recognize numpy object/int
                # cast number as int
                ind = int(ind)

                # skip document with ranking score = 0
                # breaking out of the loop assumes that the
                # scores are ordered from highest to lowest
                if self.scores[ind] == 0:
                    break

                # print('rank=', ii, ', ind=', ind, ', score=', scores[ind], 'ranked doc=', documents[ind])

                word_offsets = self.match_word_in_document(self.documents[ind], self.query_tokens)

                # return the entire sentence
                node_ind = self.map_to_text_node[ind][0]
                offset = self.map_to_text_node[ind][1]
                self.result.append({
                    'index': node_ind,
                    'offsets': [offset, offset + len(self.documents[ind])],
                    'wordOffsets': word_offsets
                })

        return self.result

    def split_text_nodes_into_sentences(self):
        self.documents = []
        self.map_to_text_node = []
        print('text nodes', self.text_nodes)
        for node_ind, text_node in enumerate(self.text_nodes):
            # replace new line character with space to prevent
            # get_sentences from splitting the text nodes at new line characters
            # needed for website that has \n within sentences such as
            # https://numpy.org/doc/stable/reference/generated/numpy.intersect1d.html
            text_node = text_node.replace('\n', ' ')

            # get_sentences extract sentences based on pattern set in RE_SENTENCE
            # by default,  gensim.summarization.textcleaner.RE_SENTENCE
            #  == re.compile(r'(\S.+?[.!?])(?=\s+|$)|(\S.+?)(?=[\n]|$)', re.UNICODE)
            for sentence in get_sentences(text_node):
                self.documents.append(sentence)
                offset = text_node.find(sentence)
                self.map_to_text_node.append([node_ind, offset])

    def preprocess_query(self):
        self.query_tokens = list(tokenize(self.query, lower=True))
        self.query_tokens = preprocess_string(" ".join(self.query_tokens), self.custom_filters)
        #print('query_tokens: ', self.query_tokens)

    def preprocess_documents(self):
        self.doc_tokens = [list(tokenize(doc, lower=True)) for doc in self.documents]
        self.doc_tokens = [preprocess_string(" ".join(doc), self.custom_filters) for doc in self.doc_tokens]
        # print('doc_tokens: ', doc_tokens)

    def get_query_document_bow(self):
        self.dictionary = Dictionary(self.doc_tokens)
        self.doc_bow = [self.dictionary.doc2bow(text) for text in self.doc_tokens]
        self.query_bow = self.dictionary.doc2bow(self.query_tokens)

    # Provide the offsets of matching words in a document
    def match_word_in_document(self, document, query_tokens):
        word_offsets = []

        for single_word_query in query_tokens:
            # index of first character in text node matching the query
            # find returns -1 if substring not found
            ind_char = document.lower().find(single_word_query)
            if ind_char == -1:
                continue
            word_offsets.append([ind_char, ind_char + len(single_word_query)])

        return word_offsets


