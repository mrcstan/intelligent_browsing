const EXCLUDE_ELEMENTS = ['script', 'style', 'iframe', 'canvas']

function walkNodes(treeWalker, nodeFunction) {
  var node
  while ((node = treeWalker.nextNode())) {
    nodeFunction(node)
  }
}

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

  var walker = document.createTreeWalker(
    document.body,
    NodeFilter.SHOW_TEXT,
    filter,
    false
  )
  walkNodes(walker, nodeFunction)
}

function clearHighlights() {
  var walker = document.createTreeWalker(
    document.body,
    NodeFilter.SHOW_ELEMENT
  )
  parentsToNormalize = new Set()
  nodesToDelete = new Set()
  walkNodes(walker, node => {
    if (node.nodeName.toLowerCase() === "span" && node.className === 'XxXIntelligentSearchHighlight') {
      nodesToDelete.add(node)
      parentsToNormalize.add(node.parentNode)
    }
  })

  for (node of nodesToDelete) {
    var textNode = document.createTextNode(node.textContent)
    node.parentNode.insertBefore(textNode, node)
    node.parentNode.removeChild(node)
  }

  for (node of parentsToNormalize) {
    node.normalize()
  }
}

// Given a text node, highlight all text at matching offsets.
function highlight(originalNode, offsets) {
  var currentNode = originalNode
  var subtracted = 0
  for (var offset of offsets) {
    var offsetWithinNode = offset[0] - subtracted

    var newNode = currentNode.splitText(offset[0] - subtracted)
    subtracted += offsetWithinNode

    currentNode = newNode
    newNode = currentNode.splitText(offset[1] - offset[0])
    subtracted += offset[1] - offset[0]

    var highlightSpan = document.createElement("span")
    highlightSpan.className = "XxXIntelligentSearchHighlight"
    highlightSpan.textContent = currentNode.textContent
    currentNode.parentNode.insertBefore(highlightSpan, currentNode)
    currentNode.parentNode.removeChild(currentNode)

    currentNode = newNode
  }

}
