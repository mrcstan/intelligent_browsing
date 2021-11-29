# Intelligent Browsing
Intelligent Browsing is a Chrome Extension for matching sentences in a webpage to a query text.

![overview screenshot](https://github.com/mrcstan/intelligent_browsing/blob/development/docs/images/screenshot1.jpeg?raw=true)

## Overview

There are two source folders: `extension` and `flask`. 
`extension` contains frontend scripts to create the GUI of the Chrome extension, extract text nodes from a webpage 
and present results from the backend model.

`flask` contains Python scripts to create a backend server and model. 
The model takes the text nodes and query text from the frontend, split the text nodes into sentences 
and rank the sentences based on the query text.  

## Installation
The code has been tested with Python 3.7 and Google Chrome Version 96.0.
Python 3 with the following packages are required `flask`, `gensim` and `numpy`.
The Python packages can be installed in the terminal using `pip` with the command
```
pip3 install flask gensim numpy
```

Start the `flask` server by running the Python script `main.py`
```
cd flask
python3 ./main.py
```

To load the extension, go to the URL `chrome://extensions/` in the Chrome browser. 
Click "Load unpacked" and select the extension directory. 
Click the Extensions icon to the right of the URL bar and the Bookmark icon.
The Intelligent Browsing extension should be visible. 
You may pin the extension to facilitate access. 
By design, Chrome does not allow extensions to remain open when Chrome is no longer the current window.  

## How to use extension?
Three ranking methods are available: 
1. BM25 (Robertson & Walker, 1994)
2. PLNVSM (Pivoted length normalization vector space model by Singhal et al., 1996)
3. Exact match

BM25 is the default. The ranking method can be changed with the radio buttons. 
   
Type any query text (word, phrases or sentences) in the search bar and press "return".
Matching words of sentences are highlighted in yellow/cyan and presented in ranking order,
i.e, the highest rank sentence is shown first. 
As the down/up arrow is clicked, the browser scrolls to the next/previous sentence and 
the corresponding matching words in the sentence are highlighted in yellow. 
Other matching words will remain highlighted

# Optional sections
## Ratings for research purpose
One can indicate the relevance of a current result with the like or dislike button. 
The ratings will be output to a directory call `ratings` to measure performance 
in terms of average precision

## Server protocol

The server endpoint, `POST /search`. It expects the body to be a JSON object like this:

```json
{
    "search_text": "some",
    "doc_content": {
        "text_nodes": [
            "some text",
            "another text"
            "this is something some"
        ]
    }
}
```

`text_nodes` is the nodeValue of all non whitespace DOM text nodes in the document, in the order in which they appear, and `search_text` is the text the user is searching for.

The response is a JSON array containing indexes from text_nodes that match, and the offsets of matching text within those nodes. It can optionally also contain a wordOffsets array that gives the index of words within each match.

```json
[
  {
    "index": 0,
    "offsets": [0, 4]
  },
  {
    "index": 2,
    "offsets": [
      [8, 12],
      [18, 22]
    ]
  }
]
```
