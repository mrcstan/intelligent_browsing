console.log('popup!')

window.onload = () => {
  document.querySelector('#SearchBox').addEventListener('keyup', (event) => {
    const button = document.querySelector('#SearchButton')
    console.log('Value is ' + event.target.value)
    button.disabled = event.target.value.length === 0

    console.log('Text changed!')
  })
}
