const express = require('express')
const cors = require('cors')

// Basic search function that just looks for matching substrings
// returns an array sorted in order of relevance, like this:
/*
[
  { index: 0, offsets: [2, 5]},
  { index: 15, offsets: [4, 7]},
  { index: 15, offsets: [121, 124]},
  { index: 0, offsets: [3, 6]}
]
*/
function search(searchText, items) {
  const matches = []

  for (var i = 0; i < items.length; i++) {
    var pos = items[i].toLowerCase().indexOf(searchText.toLowerCase())
    while (pos != -1) {
      matches.push({
        index: i,
        offsets: [pos, pos + searchText.length]
      })

      pos = items[i].indexOf(searchText, pos + searchText.length)
    }
  }

  // To fake ranking, we just shuffle the array
  shuffle(matches)

  return matches
}

function shuffle(array) {
  for (var i = array.length - 1; i > 0; i--) {
    var j = Math.floor(Math.random() * (i + 1));
    var temp = array[i];
    array[i] = array[j];
    array[j] = temp;
  }
}

const app = express()
app.use(express.json({ limit: '50mb' }))
app.use(cors())

app.post('/search', (req, res) => {
  console.log('Got request: ', req.body)

  const result = search(req.body.search_text, req.body.doc_content.text_nodes)

  // For inspecting the entire object
  const util = require('util')
  console.log('Result: ')
  console.log(util.inspect(result, { showHidden: false, depth: null, colors: true }))

  res.json(result)
})

const port = process.env.PORT || 8080
app.listen(port, () => {
  console.log(`Running test server at http://localhost:${port}`)
})
