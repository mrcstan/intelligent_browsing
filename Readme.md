# Intelligent Browsing
Intelligent Browsing is a Chrome Extension for matching sentences in a webpage to a query text.

![overview screenshot](https://github.com/mrcstan/intelligent_browsing/blob/development/docs/images/screenshot1.jpeg?raw=true)

## Overview

There are two source folders: `extension` and `flask`. 

The `extension` folder contains the frontend scripts to create the GUI of the Chrome extension, extract text nodes from a web page,
and present results from the backend model.

The `flask` folder contains Python scripts to create a backend server and model and handle user feedback. The model takes the text nodes and query text from the frontend, splits the text nodes into sentences, and ranks the sentences based on the query text.  

## Implementation Details

### Frontend

The structure of the `extension` folder follows a standard format adopted for most Chrome extensions. Within this folder, the `manifest.json` is a required configuration for an extension that specifies various properties, including the name and version of the extension, as well as information about where Chrome can find the icons of the extension as well as the files related to the popup user interface of the extension (pictured above). 

The popup UI is handled by the `popup.html`, `popup.css`, and `popup.js`. The HTML file contains the markup of the UI elements in the popup, and the CSS file adds styling to each of the elements and the overall popup. The core logic of the extension lives in `popup.js`. Within this file, event handlers are set up to listen for user interactions with the search box, search button, navigation arrows, and like/dislike buttons in the popup.

Upon receiving a user interaction to search for text, the handler for the search button, `onSearch`, will execute a script on the currently displayed page to gather up all the text nodes within the document, and will execute an asynchronous HTTP (AJAX) request to the backend server to obtain the rankings of the text nodes. Subsequently, the handler will execute another script on the currently displayed page to highlight the relevant text nodes accordingly. 

Similarly, the handlers for the like/dislike buttons, `onLike` and `onDislike`, will send AJAX requests to the backend to store a record of each result the user liked or disliked.

### Backend

#### Server protocol

##### Search

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

##### Rating

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

## How to use the extension?
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
Other matching words will remain highlighted in cyan.

# Optional sections
## Ratings for research purpose
One can indicate the relevance of a current result with the like or dislike button. 
The ratings will be output to a directory called `ratings` to measure performance 
in terms of average precision. 
