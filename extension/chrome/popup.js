const SERVER_URL = 'http://localhost:8080/search'
//const SERVER_URL = 'http://localhost:5000/search'

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
  { index: 0, offsets: [[2, 5], [3, 6]] },
  { index: 15, offsets: [[4, 7], [121, 124]]}
]
*/
  clearHighlights()

  if (results.length === 0) {
    return
  }

  var text_nodes = []
  var text_index = 0
  var i = 0

  walkTextNodes((node) => {
    if (i < results.length && text_index === results[i].index) {
      text_nodes.push(node)
      i++
    }

    text_index++
  })

  for (var i = 0; i < results.length; i++) {
    const node = text_nodes[i]
    const offsets = results[i].offsets

    highlight(node, offsets)
  }
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
