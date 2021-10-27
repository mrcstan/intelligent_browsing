function getElement(id) {
  return document.querySelector('#' + id)
}

function searchButton() {
  return getElement('SearchButton')
}

function searchBox() {
  return getElement('SearchBox')
}

function onSearchTextTyped(event) {
  searchButton().disabled = event.target.value.length === 0
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
}

window.onload = () => {
  searchBox().addEventListener('keyup', onSearchTextTyped)
  searchButton().addEventListener('click', onSearchButtonClicked)
}
