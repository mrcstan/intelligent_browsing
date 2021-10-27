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

  if (hasText && (event.key === 'Enter' || event.keyCode === 13)) {
    onSearchButtonClicked()
  }

  searchButton().disabled = !hasText

  messages().innerText = ''
}

/**
 * Gets text content from the target tab's DOM
 */
function getTargetContent() {
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
    const result = results[i]

    highlight(node.parentNode)

    // TODO: should highlight individual words, not whole parent elements.
  }
}

async function onSearchButtonClicked() {
  const searchText = searchBox().value

  // Get the active tab
  const activeTab = await chrome.tabs.query({
    active: true,
    currentWindow: true,
  })

  // Load the helper functions in the target tab context.
  await chrome.scripting.executeScript({
    target: { tabId: activeTab[0].id },
    files: ['dom.js'],
  })

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

    // Inject stylesheet
    await chrome.scripting.insertCSS({
      target: { tabId: activeTab[0].id },
      files: ['highlight.css'],
    })

    await chrome.scripting.executeScript({
      target: { tabId: activeTab[0].id },
      func: highlightResults,
      args: [jsonResponse],
    })
  } catch (e) {
    messages().innerText = 'An error occurred, please try again'
  }
}

window.onload = () => {
  searchBox().addEventListener('keyup', onSearchTextTyped)
  searchButton().addEventListener('click', onSearchButtonClicked)
}
