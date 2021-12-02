from gensim.corpora import Dictionary
# https://stackoverflow.com/questions/50009030/correct-way-of-using-phrases-and-preprocess-string-gensim
from gensim.parsing.preprocessing import preprocess_string
from gensim.utils import tokenize
import numpy as np
from rankingFunctions import BM25, PLNVSM
import re
from typing import List

# regular expression for get_sentences
RE_SENTENCE = re.compile(r'(\S.+?[.!?])(?=\s+|$)|(\S.+?)(?=[\n]|$)', re.UNICODE)


class IntelligentMatch:
    def __init__(self, query: str, text_nodes: List[str], split_text_nodes: bool = False,
                 ranker: str = 'BM25', text_filters: List[object]=[],
                 word_match_filters: List[object]=[]):
        """
        :param query:
            query text
        :param text_nodes:
            list of text nodes from the webpage
        :param split_text_nodes:
            indicates if text_nodes should be split into sentences before ranking
        :param ranker:
            ranking function type
        :param text_filters:
            gensim.parsing.preprocessing filters for filtering all documents and entire query text
        :param word_match_filters:
            gensim.parsing.preprocessing filters for filtering each document word when attempting
            to match query to document word
        """
        self.query = query
        self.text_nodes = text_nodes
        self.split_text_nodes = split_text_nodes
        self.text_filters = text_filters
        self.word_match_filters = word_match_filters
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
        if self.split_text_nodes:
            self.split_text_nodes_into_sentences()
        else:
            self.text_nodes_to_documents()

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
    def get_sentences(self, text: str):
        """Sentence generator from provided text. Sentence pattern set in RE_SENTENCE

        :param text:
            Input text.
        Yields
        ------
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

            for sentence in self.get_sentences(text_node):
                self.documents.append(sentence)
                offset = text_node.find(sentence)
                self.map_to_text_node.append([node_ind, offset])

    def text_nodes_to_documents(self):
        self.documents = self.text_nodes
        self.map_to_text_node = [[node_ind, 0] for node_ind in range(len(self.text_nodes))]


    def preprocess_query(self):
        self.query_tokens = list(tokenize(self.query, lower=True))
        self.query_tokens = preprocess_string(" ".join(self.query_tokens), self.text_filters)
        #print('query_tokens: ', self.query_tokens)

    def preprocess_documents(self):
        self.doc_tokens = [list(tokenize(doc, lower=True)) for doc in self.documents]
        self.doc_tokens = [preprocess_string(" ".join(doc), self.text_filters) for doc in self.doc_tokens]
        #print('doc_tokens: ', self.doc_tokens)

    def get_query_document_bow(self):
        self.dictionary = Dictionary(self.doc_tokens)
        self.doc_bow = [self.dictionary.doc2bow(text) for text in self.doc_tokens]
        self.query_bow = self.dictionary.doc2bow(self.query_tokens)

    # Provide the offsets of matching words in a document
    def match_word_in_document(self, document: str, query_token: List[str]) -> List[List[int]]:
        """
        :param document:
            an unfiltered string of words of a document
        :param query_token:
            a list of filtered query words
        :return:
             a list of pairs of starting and ending indices where the document matches the query text
        """
        word_offsets = []
        document = document.lower()
        # split document into words, remove punctuations etc. lower=False since document has been is already lower case
        doc_words = list(tokenize(document, lower=False))

        for doc_word in doc_words:
            # get the location of the first character of the current document word
            ind_char = document.find(doc_word)
            # get the root word of the document word
            filtered_word = preprocess_string(doc_word, self.word_match_filters)[0]
            for single_word_query in query_token:
                # check if the filtered word match the single query word
                # if true, return the location of the current document word
                if filtered_word == single_word_query:
                    word_offsets.append([ind_char, ind_char + len(doc_word)])
                    break

        return word_offsets


