const express = require('express')
const cors = require('cors')

// Basic search function that just looks for matching substrings
// returns an array like:
/*
[
  { index: 0, offsets: [[2, 5], [3, 6]] },
  { index: 15, offsets: [[4, 7], [121, 124]]}
]
*/
function search(searchText, items) {
  const matches = []

  for (var i = 0; i < items.length; i++) {
    let match = {
      index: i,
      offsets: [],
    }

    var pos = items[i].toLowerCase().indexOf(searchText.toLowerCase())
    while (pos != -1) {
      match.offsets.push([pos, pos + searchText.length - 1])
      pos = items[i].indexOf(searchText, pos + searchText.length)
    }

    if (match.offsets.length > 0) {
      matches.push(match)
    }
  }

  return matches
}

const app = express()
app.use(express.json({ limit: '50mb' }))
app.use(cors())

app.post('/search', (req, res) => {
  console.log('Got request: ', req.body)

  const result = search(req.body.search_text, req.body.doc_content.text_nodes)
  console.log('Result', result)

  res.json(result)
})

const port = process.env.PORT || 8080
app.listen(port, () => {
  console.log(`Running test server at http://localhost:${port}`)
})
