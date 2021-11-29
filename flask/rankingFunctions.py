# Modified gensim.summarization.bm25 module
# Reasons for taking out the module and putting it in this file are
# (1) gensim.summarization is deprecated in 4.0 (latest version with the module is 3.8.3)
# (2) create a base class so that other ranking functions can be implemented by extending the base class

import logging
import math
from six import iteritems
from six.moves import range

PARAM_K1 = 1.5
PARAM_B = 0.75
EPSILON = 0.25

logger = logging.getLogger(__name__)


class Ranker():
    """Base class for ranker functions.

    Attributes
    ----------
    corpus_size : int
        Size of corpus (number of documents).
    avgdl : float
        Average length of document in `corpus`.
    doc_freqs : list of dicts of int
        Dictionary with terms frequencies for each document in `corpus`. Words used as keys and frequencies as values.
    idf : dict
        Dictionary with inversed documents frequencies for whole `corpus`. Words used as keys and frequencies as values.
    doc_len : list of int
        List of document lengths.
    """

    def __init__(self, corpus, epsilon=EPSILON):
        self.epsilon = epsilon

        self.corpus_size = 0
        self.avgdl = 0
        self.doc_freqs = []
        self.idf = {}
        self.doc_len = []
        self._initialize(corpus)

    def _initialize(self, corpus):
        """Calculates frequencies of terms in documents and in corpus. Also computes inverse document frequencies."""
        nd = {}  # word -> number of documents with word
        num_doc = 0
        for document in corpus:
            self.corpus_size += 1
            self.doc_len.append(len(document))
            num_doc += len(document)

            frequencies = {}
            for word in document:
                if word not in frequencies:
                    frequencies[word] = 0
                frequencies[word] += 1
            self.doc_freqs.append(frequencies)

            for word, freq in iteritems(frequencies):
                if word not in nd:
                    nd[word] = 0
                nd[word] += 1

        self.avgdl = float(num_doc) / self.corpus_size
        # collect idf sum to calculate an average idf for epsilon value
        idf_sum = 0
        # collect words with negative idf to set them a special epsilon value.
        # idf can be negative if word is contained in more than half of documents
        negative_idfs = []
        for word, freq in iteritems(nd):
            idf = math.log(self.corpus_size - freq + 0.5) - math.log(freq + 0.5)
            self.idf[word] = idf
            idf_sum += idf
            if idf < 0:
                negative_idfs.append(word)
        self.average_idf = float(idf_sum) / len(self.idf)

        if self.average_idf < 0:
            logger.warning(
                'Average inverse document frequency is less than zero. Your corpus of {} documents'
                ' is either too small or it does not originate from natural text. BM25 may produce'
                ' unintuitive results.'.format(self.corpus_size)
            )

        eps = self.epsilon * self.average_idf
        for word in negative_idfs:
            self.idf[word] = eps

    def get_scores(self, document):
        """Computes and returns BM25 scores of given `document` in relation to
        every item in corpus.

        Parameters
        ----------
        document : list of str
            Document to be scored.

        Returns
        -------
        list of float
            BM25 scores.

        """
        scores = [self.get_score(document, index) for index in range(self.corpus_size)]
        return scores

    def get_scores_bow(self, document):
        """Computes and returns BM25 scores of given `document` in relation to
        every item in corpus.

        Parameters
        ----------
        document : list of str
            Document to be scored.

        Returns
        -------
        list of float
            BM25 scores.

        """
        scores = []
        for index in range(self.corpus_size):
            score = self.get_score(document, index)
            if score > 0:
                scores.append((index, score))
        return scores


class BM25(Ranker):
    # Implementation of Best Matching 25 ranking function.
    def __init__(self, corpus, k1=PARAM_K1, b=PARAM_B, epsilon=EPSILON):
        """
        Parameters
        ----------
        corpus : list of list of str
            Given corpus.
        k1 : float
            Constant used for influencing the term frequency saturation. After saturation is reached, additional
            presence for the term adds a significantly less additional score. According to [1]_, experiments suggest
            that 1.2 < k1 < 2 yields reasonably good results, although the optimal value depends on factors such as
            the type of documents or queries.
        b : float
            Constant used for influencing the effects of different document lengths relative to average document length.
            When b is bigger, lengthier documents (compared to average) have more impact on its effect. According to
            [1]_, experiments suggest that 0.5 < b < 0.8 yields reasonably good results, although the optimal value
            depends on factors such as the type of documents or queries.
        epsilon : float
            Constant used as floor value for idf of a document in the corpus. When epsilon is positive, it restricts
            negative idf values. Negative idf implies that adding a very common term to a document penalize the overall
            score (with 'very common' meaning that it is present in more than half of the documents). That can be
            undesirable as it means that an identical document would score less than an almost identical one (by
            removing the referred term). Increasing epsilon above 0 raises the sense of how rare a word has to be (among
            different documents) to receive an extra score.

        """
        super().__init__(corpus, epsilon)
        self.k1 = k1
        self.b = b

    def get_score(self, document, index):
        """Computes BM25 score of given `document` in relation to item of corpus selected by `index`.

        Parameters
        ----------
        document : list of str
            Document to be scored.
        index : int
            Index of document in corpus selected to score with `document`.

        Returns
        -------
        float
            BM25 score.

        """
        score = 0.0
        doc_freqs = self.doc_freqs[index]
        numerator_constant = self.k1 + 1
        denominator_constant = self.k1 * (1 - self.b + self.b * self.doc_len[index] / self.avgdl)
        for word in document:
            if word in doc_freqs:
                df = self.doc_freqs[index][word]
                idf = self.idf[word]
                score += (idf * df * numerator_constant) / (df + denominator_constant)
        return score


class PLNVSM(Ranker):
    # Implementation of Pivoted Length Normalization VSM (Singhal et al. 96) by modifying bm25 class
    def __init__(self, corpus,  b=PARAM_B, epsilon=EPSILON):
        """
        Parameters
        ----------
        corpus : list of list of str
            Given corpus.
        b : float
            Constant used for influencing the effects of different document lengths relative to average document length.
            When b is bigger, lengthier documents (compared to average) have more impact on its effect. According to
            [1]_, experiments suggest that 0.5 < b < 0.8 yields reasonably good results, although the optimal value
            depends on factors such as the type of documents or queries.
        epsilon : float
            Constant used as floor value for idf of a document in the corpus. When epsilon is positive, it restricts
            negative idf values. Negative idf implies that adding a very common term to a document penalize the overall
            score (with 'very common' meaning that it is present in more than half of the documents). That can be
            undesirable as it means that an identical document would score less than an almost identical one (by
            removing the referred term). Increasing epsilon above 0 raises the sense of how rare a word has to be (among
            different documents) to receive an extra score.

        """
        super().__init__(corpus, epsilon)
        self.b = b

    def get_score(self, document, index):
        """Computes score of given `document` in relation to item of corpus selected by `index`.

        Parameters
        ----------
        document : list of str
            Document to be scored.
        index : int
            Index of document in corpus selected to score with `document`.

        Returns
        -------
        float
            score.

        """
        score = 0.0
        doc_freqs = self.doc_freqs[index]
        denominator_constant = 1 - self.b + self.b * self.doc_len[index] / self.avgdl
        for word in document:
            if word in doc_freqs:
                df = self.doc_freqs[index][word]
                idf = self.idf[word]
                score += idf * math.log(1 + math.log(1 + df)) / denominator_constant

        return score