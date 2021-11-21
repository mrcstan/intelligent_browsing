from gensim.summarization import bm25
import math

PARAM_B = 0.75
EPSILON = 0.25


class PLNVSM(bm25.BM25):
    """Implementation of Pivoted Length Normalization VSM (Singhal et al. 96) by modifying bm25 class

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
        super(PLNVSM,self).__init__(corpus, b=b, epsilon=epsilon)

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