from flask import Flask, jsonify, request

from intelligentMatch import IntelligentMatch
import os
from rating import Rating
# from typing import List
# required for production server
from waitress import serve

app = Flask(__name__)

"When returning HTML (the default response type in Flask), " \
"any user-provided values rendered in the output must be escaped to protect from injection attacks. " \
"HTML templates rendered with Jinja, introduced later, will do this automatically."
# from markupsafe import escape

TOP_K = 3

USER_RATINGS = {}


@app.route('/rate', methods=['POST'])
def rating():
    if request.method == 'POST':
        try:
            request_data = request.get_json()
            if len(request_data):
                url = request_data['url']
                query = request_data['query']
                result_index = request_data['resultIndex']
                liked = request_data['liked']
                ranking_method = request_data['ranking_method']

                if url not in USER_RATINGS:
                    USER_RATINGS[url] = {}
                if query not in USER_RATINGS[url]:
                    USER_RATINGS[url][query] = {}
                if ranking_method not in USER_RATINGS[url][query]:
                    USER_RATINGS[url][query][ranking_method] = {}
                USER_RATINGS[url][query][ranking_method][result_index] = liked
                #print('user ratings: ', USER_RATINGS)
                rating = Rating(USER_RATINGS, topK=TOP_K)
                rating.write_print_data_frame()
                rating_out_dir = '../ratings'
                os.makedirs('../ratings', exist_ok=True)
                rating.write_ratings_to_file(rating_out_dir+'/ratings.csv')
                rating.calculate_mean_avg_precisions()
                outfile = rating_out_dir+'/top-'+str(TOP_K)+'-avg-precisions.csv'
                rating.write_avg_precisions_to_file(outfile)
                outfile = rating_out_dir+'/top-'+str(TOP_K)+'-mean-avg-precisions.csv'
                rating.write_mean_avg_precisions_to_file(outfile)
                rating.print_mean_avg_precision()
                result = {'status': 'success'}
            else:
                print('Error: provided rating data is empty')
                result = {'status': 'failure'}
        except RuntimeError as e:
            print(e)
            result = {'status': 'failure'}
    else:
        result = {'status': 'failure'}

    return jsonify(result)


@app.route('/search', methods=['POST'])
def words():
    if request.method == 'POST':
        try:
            request_data = request.get_json()
            if len(request_data):
                query = request_data['search_text']
                text_nodes = request_data['doc_content']['text_nodes']
                ranker = request_data['ranking_method']
                split_text_nodes = request_data['split_text_nodes']
                add_synonyms = request_data['add_synonyms']

                intelli_match = IntelligentMatch(query, text_nodes, split_text_nodes=split_text_nodes,
                                                ranker=ranker, add_synonyms=add_synonyms)
                intelli_match.initialize()
                result = intelli_match.rank()
                if add_synonyms:
                    print('Query tokens: ', intelli_match.get_query_tokens())
                #print('result: ', result)
            else:
                print('Error: provided website data is empty')
                result = {}
        except RuntimeError as e:
            print(e)
            result = {}

    else:
        result = {}

    return jsonify(result)


if __name__ == "__main__":
    # start production server
    serve(app, host='localhost', port=8080)
    # start development server
    # app.run(debug=True, port=8080)
