from gensim.parsing.preprocessing import remove_stopwords, stem_text
from intelligentMatch import IntelligentMatch
from flask import Flask, jsonify, request
app = Flask(__name__)

"When returning HTML (the default response type in Flask), " \
"any user-provided values rendered in the output must be escaped to protect from injection attacks. " \
"HTML templates rendered with Jinja, introduced later, will do this automatically."
# from markupsafe import escape

USER_RATINGS = {}


@app.route('/rate', methods=['POST'])
def rating():
    if request.method == 'POST':
        request_data = request.get_json()

        url = request_data['url']
        query = request_data['query']
        result_index = request_data['resultIndex']
        liked = request_data['liked']

        if url not in USER_RATINGS:
            USER_RATINGS[url] = {}
        if query not in USER_RATINGS[url]:
            USER_RATINGS[url][query] = {}
        USER_RATINGS[url][query][result_index] = liked
        print('user ratings: ', USER_RATINGS)

    return jsonify({'status': 'success'})


@app.route('/search', methods=['POST'])
def words():
    if request.method == 'POST':
        request_data = request.get_json()
        query = request_data['search_text']
        text_nodes = request_data['doc_content']['text_nodes']
        ranker = request_data['ranking_method']
        print(ranker)

        custom_filters = [stem_text]
        # custom_filters = []
        # ranker = 'BM25' or 'PLNVSM'
        ranker = 'PLNVSM'
        intelliMatch = IntelligentMatch(query, text_nodes, ranker=ranker, custom_filters=custom_filters)
        intelliMatch.initialize()
        result = intelliMatch.rank()
        print('result: ', result)

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=8080)