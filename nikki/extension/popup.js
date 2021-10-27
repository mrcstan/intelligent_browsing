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

function onSearchButtonClicked() {
  const searchText = searchBox().value

  // Call the server
  fetch('http://localhost:8080/search', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ search_text: searchText }),
  })
    .then((response) => response.json())
    .then((data) => console.log('Got response ', data))
    .catch((error) => {
      messages().innerText = 'An error occurred, please try again'
    })
}

window.onload = () => {
  searchBox().addEventListener('keyup', onSearchTextTyped)
  searchButton().addEventListener('click', onSearchButtonClicked)
}
