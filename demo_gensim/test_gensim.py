import numpy as np
from gensim.summarization import bm25
from gensim.utils import simple_preprocess
from gensim import corpora


# texts = [["black", "cat", "white", "cat"],
#           ["cat", "outer", "space"],
#          ["wag", "dog"]]
texts = [simple_preprocess(line, deacc=True) for line in open('./test_data/cranfield.dat', encoding='utf-8')]
print('Document 1:')
print(texts[0])

dictionary = corpora.Dictionary(texts)
corpus = [dictionary.doc2bow(text) for text in texts]
print('Corpus 1:')
print(corpus[0])
bm25obj = bm25.BM25(corpus)

#queries = dictionary.doc2bow(['black', 'space'])
query_texts = [simple_preprocess(line, deacc=True) for line in open('./test_data/cranfield-queries.txt', encoding='utf-8')]
queries = [dictionary.doc2bow(text) for text in query_texts]
print('Query 1:')
print(query_texts[0])
print(queries[0])

scores = bm25obj.get_scores(queries[0])
rank_doc_inds = np.argsort(scores)
#print(rank_doc_inds)

top_rank_doc_inds = rank_doc_inds[-1:-5:-1]
#print(top_rank_doc_inds)
for ii, ind in enumerate(top_rank_doc_inds):
    print('Rank {} document:'.format(ii+1))
    print(texts[ind])