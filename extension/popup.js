const SERVER_URL = 'http://localhost:8080';

gCurrentResult = null
gResultCount = 0
gLastSearchText = null

function getElement(id) {
  return document.querySelector('#' + id)
}


function searchBox() {
  return getElement('SearchBox')
}

function rankingMethod() {
  return document.querySelector('input[name=Ranker]:checked').value;
}

function textGranularity() {
  return document.querySelector('input[name=TextGranularity]:checked').value;
}

function synonyms() {
  return document.querySelector('input[id=synonyms]').checked;
}


function messages() {
  return getElement('Messages')
}

function likeMessage() {
  return getElement('LikeMessage')
}

function previousResultButton() {
  return getElement("previousResult")
}

function nextResultButton() {
  return getElement("nextResult");
}

function likeButton() {
  return getElement("like")
}

function dislikeButton() {
  return getElement("dislike");
}

function closeButton() {
  return getElement("close")
}

function resultCounter() {
  return getElement("resultCounter")
}

function onSearchTextTyped(event) {
  messages().innerText = ''
  likeMessage().innerText = ''
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

function updateButtons() {
  nextResultButton().disabled = gResultCount === 0
  previousResultButton().disabled = gResultCount === 0
  likeButton().disabled = gResultCount === 0
  dislikeButton().disabled = gResultCount === 0
  resultCounter().innerText = (gCurrentResult === null ? 0 : gCurrentResult + 1) + "/" + gResultCount
}

/**
 * Highlights results in the target tab's DOM.
 */
function highlightResults(results) {
  /* results looks like (wordOffsets are optional)
[
  { index: 0, offsets: [2, 5], wordOffsets: [[1, 2], [3, 4]]},
  { index: 15, offsets: [4, 7]},
  { index: 15, offsets: [121, 124]},
  { index: 0, offsets: [3, 6]}
]
  order indicates rank. For highlighting, don't care about rank, but
  will need to use it for navigating.
*/
  clearHighlights()

  if (results.length === 0) {
    return 0
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
          wordOffsets: [[...]],
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
    if (result.hasOwnProperty('wordOffsets')) {
      obj.wordOffsets = result.wordOffsets
    }

    indexedOffsets[key].push(obj)
    rankedOffsets[rank] = obj
    rank++
  }

  // Now highlight the matches and get back the spans containing
  // the highlights
  for (const [index, info] of Object.entries(indexedOffsets)) {
    // Sort info by the first offset.
    info.sort((a, b) => a.offsets[0] - b.offsets[0])

    const spans = highlight(text_nodes[index], info.map(v => v.offsets),
      info.map(v => v.hasOwnProperty('wordOffsets') ? v.wordOffsets : []))
    for (var i = 0; i < info.length; i++) {
      info[i].span = spans[i]
    }
  }

  // Now extract the spans in *ranked* order
  gResultSpans = Object.values(rankedOffsets).map(v => v.span)
  return gResultSpans.length
}

// Selects the text content of an element and scrolls it into view
function selectResultImpl(index) {
  const element = gResultSpans[index]
  // selection = window.getSelection()
  // range = document.createRange()
  // range.selectNodeContents(element)
  // selection.removeAllRanges()
  // selection.addRange(range)

  element.scrollIntoView({
    behavior: 'auto',
    block: 'center',
    inline: 'center'
  })
  element.className += " XxXIntelligentSearchCurrent"
  if (gHighlightedElement) {
    gHighlightedElement.className = gHighlightedElement.className.replaceAll("XxXIntelligentSearchCurrent", "")
  }
  gHighlightedElement = element
}

async function selectResult(index) {
  const activeTab = await chrome.tabs.query({
    active: true,
    currentWindow: true,
  })
  await chrome.scripting.executeScript({
    target: { tabId: activeTab[0].id },
    func: selectResultImpl,
    args: [index],
  })
}

function clearSearch() {
  clearHighlights()
}

async function onSearchButtonClicked() {
  messages().innerText = ''
  likeMessage().innerText = ''

  const searchText = searchBox().value

  if (searchText === gLastSearchText && gResultCount > 0) {
    // If the search text hasn't changed, then interpret this as a click on the next button.
    onNextResult()
    return
  }
  gLastSearchText = searchText

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
    gCurrentResult = null
    gResultCount = 0
    updateButtons()
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
    ranking_method: rankingMethod(),
    split_text_nodes: textGranularity() === 'Sentences',
    add_synonyms: synonyms(),
  }

  try {
    const response = await fetch(SERVER_URL + '/search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(postData),
    })
    const jsonResponse = await response.json()

    console.log('Got response from server: ', jsonResponse)

    const result = await chrome.scripting.executeScript({
      target: { tabId: activeTab[0].id },
      func: highlightResults,
      args: [jsonResponse],
    })

    const resultCount = result[0].result
    gResultCount = resultCount
    gCurrentResult = resultCount > 0 ? 0 : null

    if (resultCount > 0) {
      selectResult(0)
    }

    updateButtons()
  } catch (e) {
    console.log(e)
    messages().innerText = 'An error occurred, please try again'
  }
}

function onSearch(e) {
  // Detect escape-escape to close.
  if (e.target.value === "" && gLastSearchText === "") {
    onClose()
    return
  }

  onSearchButtonClicked()
}

function onClose() {
  // Workaround to clear the search.
  searchBox().value = ""
  onSearchButtonClicked()
  window.close()
}

function onPreviousResult() {
  likeMessage().innerText = ''
  gCurrentResult--
  if (gCurrentResult < 0) {
    gCurrentResult = gResultCount - 1
  }
  updateButtons()
  selectResult(gCurrentResult)
}

function onNextResult() {
  likeMessage().innerText = ''
  gCurrentResult++
  if (gCurrentResult === gResultCount) {
    gCurrentResult = 0
  }
  updateButtons()
  selectResult(gCurrentResult)
}

async function sendUserFeedback(resultIndex, liked) {
  try {
    const activeTab = await chrome.tabs.query({
      active: true,
      currentWindow: true,
    })
    const url = activeTab[0].url;
    const query = gLastSearchText;
    const ranking_method = rankingMethod();
    const postData = {
      url,
      query,
      resultIndex,
      ranking_method,
      liked,
    }
    const response = await fetch(SERVER_URL + '/rate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(postData),
    })
    const jsonResponse = await response.json()

    console.log('Got response from server: ', jsonResponse)
  } catch (e) {
    console.log(e)
    messages().innerText = 'Could not send user feedback to server due to an error. Please try again.'
  }
}

function onLike() {
  likeMessage().innerText = 'Liked!'
  sendUserFeedback(gCurrentResult, true);
}

function onDislike() {
  likeMessage().innerText = 'Disliked!'
  sendUserFeedback(gCurrentResult, false);
}

function addRankingMethodListeners() {
  document.querySelectorAll('input[name=Ranker]').forEach(radio => radio.addEventListener('change', () => { 
    gLastSearchText = null;
    gResultCount = 0;
    onSearchButtonClicked();
  }));
}

function addTextGranularityListeners() {
  document.querySelectorAll('input[name=TextGranularity]').forEach(radio => radio.addEventListener('change', () => { 
    gLastSearchText = null;
    gResultCount = 0;
    onSearchButtonClicked();
  }));
}

function addSynonymsListener() {
  document.querySelector('input[id=synonyms]').addEventListener('change', () => { 
    gLastSearchText = null;
    gResultCount = 0;
    onSearchButtonClicked();
  });
}

window.onload = () => {
  searchBox().addEventListener('keyup', onSearchTextTyped)
  searchBox().addEventListener('search', onSearch)
  previousResultButton().addEventListener('click', onPreviousResult)
  nextResultButton().addEventListener('click', onNextResult)
  likeButton().addEventListener('click', onLike)
  dislikeButton().addEventListener('click', onDislike)
  closeButton().addEventListener('click', onClose)
  addRankingMethodListeners()
  addTextGranularityListeners()
  addSynonymsListener()
  updateButtons()
}
