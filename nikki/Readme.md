# Intelligent Browsing

This has two folders: `extension` and `fake_backend`. The `extension` folder is a Chrome extension to add search functionality, and the `fake_backend` is a temporary node backend to test making `POST` calls from the extension.

## Running the server

First, install node - see [instructions](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm)

Then you can start the server by:

```
cd fake_backend
npm start
```

The server right now just has one API endpoint, `POST /search`. It expects the body to be a JSON object like this:

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

The response is a JSON array containing indexes from text_nodes that match, and the offsets of matching text within those nodes.

```json
[
  {
    "index": 0,
    "offsets": [[0, 4]]
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

## Running the extension

In Chrome, load the extension unpacked from the `extension` folder. Then click on the extension toolbar button to load it. Type a search term, and press return.
