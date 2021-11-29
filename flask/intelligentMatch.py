from gensim.corpora import Dictionary
# https://stackoverflow.com/questions/50009030/correct-way-of-using-phrases-and-preprocess-string-gensim
from gensim.parsing.preprocessing import preprocess_string
from rankingFunctions import BM25, PLNVSM
import re
from gensim.utils import tokenize

import numpy as np

# regular expression for get_sentences
RE_SENTENCE = re.compile(r'(\S.+?[.!?])(?=\s+|$)|(\S.+?)(?=[\n]|$)', re.UNICODE)

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
        self.result = []
        if len(self.query_bow):
            if self.ranker == 'BM25':
                ranking_func = BM25(self.doc_bow, b=0.0)
                scores = ranking_func.get_scores(self.query_bow)
                self.rank_doc_inds = np.argsort(scores)[::-1]
            elif self.ranker == 'PLNVSM':
                ranker = PLNVSM(self.doc_bow, b=0.0)
                scores = ranker.get_scores(self.query_bow)
                self.rank_doc_inds = np.argsort(scores)[::-1]
            elif self.ranker == 'Exact Match':
                clean_query = ' '.join(self.query_tokens)
                clean_documents = [' '.join(doc_token) for doc_token in self.doc_tokens]
                scores = [1 if clean_query in doc else 0 for doc in clean_documents]
                self.rank_doc_inds = np.where(scores)[0]
            else:
                raise Exception('Unknown ranker')

            for ii, ind in enumerate(self.rank_doc_inds):

                # jsonify does not recognize numpy object/int
                # cast number as int
                ind = int(ind)

                # skip document with ranking score = 0
                # breaking out of the loop assumes that the
                # scores are ordered from highest to lowest
                if scores[ind] == 0:
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

    # Copied from gensim.summarization, which has been deprecated in version 4.0
    def get_sentences(self, text):
        """Sentence generator from provided text. Sentence pattern set
        in :const:`~gensim.summarization.textcleaner.RE_SENTENCE`.

        Parameters
        ----------
        text : str
            Input text.

        Yields
        ------
        str
            Single sentence extracted from text.

        Example
        -------
        .. sourcecode:: pycon

            >>> text = "Does this text contains two sentences? Yes, it does."
            >>> for sentence in get_sentences(text):
            >>>     print(sentence)
            Does this text contains two sentences?
            Yes, it does.

        """
        for match in RE_SENTENCE.finditer(text):
            yield match.group()

    def split_text_nodes_into_sentences(self):
        self.documents = []
        self.map_to_text_node = []

        for node_ind, text_node in enumerate(self.text_nodes):
            # replace new line character with space to prevent
            # get_sentences from splitting the text nodes at new line characters
            # needed for website that has \n within sentences such as
            # https://numpy.org/doc/stable/reference/generated/numpy.intersect1d.html
            text_node = text_node.replace('\n', ' ')

            # get_sentences extract sentences based on pattern set in RE_SENTENCE
            # by default,  gensim.summarization.textcleaner.RE_SENTENCE
            #  == re.compile(r'(\S.+?[.!?])(?=\s+|$)|(\S.+?)(?=[\n]|$)', re.UNICODE)
            for sentence in self.get_sentences(text_node):
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
        #print('doc_tokens: ', self.doc_tokens)

    def get_query_document_bow(self):
        self.dictionary = Dictionary(self.doc_tokens)
        self.doc_bow = [self.dictionary.doc2bow(text) for text in self.doc_tokens]
        self.query_bow = self.dictionary.doc2bow(self.query_tokens)

    # Provide the offsets of matching words in a document
    def match_word_in_document(self, document, query_token):
        '''

        :param document:
            an unfiltered string of words
        :param query_token:
            a list of filtered query words
        :return:
        '''
        word_offsets = []
        document = document.lower()
        # split document into words, remove punctuations etc. lower=False since document has been is already lower case
        doc_words = list(tokenize(document, lower=False))
        for doc_word in doc_words:
            # get the location of the first character of the current document word
            ind_char = document.find(doc_word)
            # get the root word of the document word
            filtered_word = preprocess_string(doc_word, self.custom_filters)[0]
            for single_word_query in query_token:
                # check if the filtered word match the single query word
                # if true, return the location of the current document word
                if filtered_word == single_word_query:
                    word_offsets.append([ind_char, ind_char + len(doc_word)])
                    break

        return word_offsets


