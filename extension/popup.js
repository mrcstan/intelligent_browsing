const SERVER_URL = 'http://localhost:8080/search'

function getElement(id) {
  return document.querySelector('#' + id)
}

function searchButton() {
  return getElement('SearchButton')
}

function searchBox() {
  return getElement('SearchBox')
}

function messages() {
  return getElement('Messages')
}

function onSearchTextTyped(event) {
  const hasText = event.target.value.length > 0
  searchButton().disabled = !hasText
  messages().innerText = ''
}

/**
 * Gets text content from the target tab's DOM
 */
function getTargetContent() {
  clearHighlights()

  // Get all the text nodes in the document body.
  // TODO: this needs to filter out things like <script> / <style> elements
  var text_nodes = []
  walkTextNodes((node) => {
    text_nodes.push(node.nodeValue)
  })

  return {
    text_nodes,
  }
}

/**
 * Highlights results in the target tab's DOM.
 */
function highlightResults(results) {
  /* results looks like:
[
  { index: 0, offsets: [2, 5]},
  { index: 15, offsets: [4, 7]},
  { index: 15, offsets: [121, 124]},
  { index: 0, offsets: [3, 6]}
]
  order indicates rank. For highlighting, don't care about rank, but
  will need to use it for navigating.
*/
  clearHighlights()
  IS_GLOBAL_STATE.rankedSpans = []

  if (results.length === 0) {
    return
  }

  // Collect the text nodes in the order of the index
  var text_nodes = []
  walkTextNodes((node) => {
    text_nodes.push(node)
  })


  // We have to highlight all indexes within a text node at
  // the same time, otherwise the offsets get disturbed, but
  // need to keep track of the rank. So group the offsets by
  // the index. This maps the above into a structure like this:
  /*
    indexedOffsets = {
      0: [
        {
          offsets: [2, 5],
        },
        {
          offsets: [3, 6],
        }
      ],
      15: [
        {
          offsets: [4, 7],
        },
        {
          offsets: [121, 124],
        }
      ]
    }
  */
  var indexedOffsets = {}
  var rankedOffsets = {}
  var rank = 0
  for (var result of results) {
    const key = result.index
    if (!(key in indexedOffsets)) {
      indexedOffsets[key] = []
    }

    const obj = { offsets: result.offsets }
    indexedOffsets[key].push(obj)
    rankedOffsets[rank] = obj
    rank++
  }

  // Now highlight the matches and get back the spans containing
  // the highlights
  for (const [index, info] of Object.entries(indexedOffsets)) {
    // Sort info by the first offset.
    info.sort((a, b) => a.offsets[0] - b.offsets[0])
    const spans = highlight(text_nodes[index], info.map(v => v.offsets))
    for (var i = 0; i < info.length; i++) {
      info[i].span = spans[i]
    }
  }

  // Now extract the spans in *ranked* order
  IS_GLOBAL_STATE.rankedSpans = Object.values(rankedOffsets).map(v => v.span)
}

function clearSearch() {
  clearHighlights()
}

async function onSearchButtonClicked() {
  const searchText = searchBox().value

  // Get the active tab
  const activeTab = await chrome.tabs.query({
    active: true,
    currentWindow: true,
  })

  if (searchText.trim().length === 0) {
    await chrome.scripting.executeScript({
      target: { tabId: activeTab[0].id },
      func: clearSearch,
    })
    return
  }

  // Execute the getDOMFromTarget function in the target tab context
  const result = await chrome.scripting.executeScript({
    target: { tabId: activeTab[0].id },
    func: getTargetContent,
  })
  // Unpack the result frame
  const resultValue = result[0].result

  // Make a POST request to the server
  const postData = {
    search_text: searchText,
    doc_content: resultValue,
  }

  try {
    const response = await fetch(SERVER_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(postData),
    })
    const jsonResponse = await response.json()

    console.log('Got response from server: ', jsonResponse)

    await chrome.scripting.executeScript({
      target: { tabId: activeTab[0].id },
      func: highlightResults,
      args: [jsonResponse],
    })
  } catch (e) {
    messages().innerText = 'An error occurred, please try again'
  }
}

function onSearch(e) {
  onSearchButtonClicked()
}

window.onload = () => {
  searchBox().addEventListener('keyup', onSearchTextTyped)
  searchBox().addEventListener('search', onSearch)
  searchButton().addEventListener('click', onSearchButtonClicked)
}
