const EXCLUDE_ELEMENTS = ['script', 'style', 'iframe', 'canvas']

function walkTextNodes(nodeFunction) {
  // Filters out nodes that only contain whitespace and nodes that
  // are children of EXCLUDE_ELEMENTS
  const filter = {
    acceptNode: function (node) {
      if (/\S/.test(node.data)) {
        if (
          !EXCLUDE_ELEMENTS.includes(node.parentNode.nodeName.toLowerCase())
        ) {
          return NodeFilter.FILTER_ACCEPT
        }
      }
    },
  }

  var node
  var walk = document.createTreeWalker(
    document.body,
    NodeFilter.SHOW_TEXT,
    filter,
    false
  )
  while ((node = walk.nextNode())) {
    nodeFunction(node)
  }
}

function highlight(node) {
  node.className += ' XxXIntelligentSearchHighlight'
}

function clearHighlights() {
  var node
  var walk = document.createTreeWalker(
    document.body,
    NodeFilter.SHOW_ELEMENT,
    null,
    false
  )
  while ((node = walk.nextNode())) {
    if (node.className && typeof node.className === 'string') {
      node.className = node.className
        .replaceAll('XxXIntelligentSearchHighlight', '')
        .trim()
    }
  }
}
