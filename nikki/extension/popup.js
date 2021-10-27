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

  // Get the DOM from the current tab
  chrome.tabs.executeScript(
    {
      code: '(' + getDOMFromTarget + ')();',
    },
    (results) => {
      // Call the server
      const postData = {
        search_text: searchText,
        doc_content: results[0],
      }

      fetch(SERVER_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(postData),
      })
        .then((response) => response.json())
        .then((data) => console.log('Got response ', data))
        .catch((error) => {
          messages().innerText = 'An error occurred, please try again'
        })
    }
  )
}

window.onload = () => {
  searchBox().addEventListener('keyup', onSearchTextTyped)
  searchButton().addEventListener('click', onSearchButtonClicked)
}
