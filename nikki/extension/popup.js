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
 * Gets the dom from the target.
 *
 * TODO: Instead of returning a string, can return a json object with offsets of
 * dom elements etc.
 */
function getDOMFromTarget() {
  return document.body.innerHTML
}

async function onSearchButtonClicked() {
  const searchText = searchBox().value

  // Get the active tab
  const activeTab = await chrome.tabs.query({
    active: true,
    currentWindow: true,
  })

  // Execute the getDOMFromTarget function in the target tab context
  const result = await chrome.scripting.executeScript({
    target: { tabId: activeTab[0].id },
    func: getDOMFromTarget,
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
  } catch (e) {
    messages().innerText = 'An error occurred, please try again'
  }
}

window.onload = () => {
  searchBox().addEventListener('keyup', onSearchTextTyped)
  searchButton().addEventListener('click', onSearchButtonClicked)
}
