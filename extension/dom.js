const HIGHLIGHT_STYLE_SENTENCE = "sentence";
const HIGHLIGHT_STYLE_TEXT_NODE = "textnode";

// Change this to use a different highlight style
const HIGHLIGHT_STYLE = HIGHLIGHT_STYLE_SENTENCE;

const EXCLUDE_ELEMENTS = ['script', 'style', 'iframe', 'canvas']

function walkNodes(treeWalker, nodeFunction) {
  var node
  while ((node = treeWalker.nextNode())) {
    nodeFunction(node)
  }
}

function isVisible(textNode) {
  if (textNode.parentElement) {
    const rect = textNode.parentElement.getBoundingClientRect()
    return rect.width > 0 && rect.height > 0
  }
  return false
}

function walkTextNodes(nodeFunction) {
  // Filters out nodes that only contain whitespace and nodes that
  // are children of EXCLUDE_ELEMENTS, and children that are not
  // visible in the browser viewport.
  const filter = {
    acceptNode: function (node) {
      if (/\S/.test(node.data)) {
        if (
          !EXCLUDE_ELEMENTS.includes(node.parentNode.nodeName.toLowerCase())
        ) {
          if (isVisible(node)) {
            return NodeFilter.FILTER_ACCEPT
          }
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
  gResultSpans = []
  if (gHighlightedElement) {
    gHighlightedElement.className = gHighlightedElement.className.replaceAll("XxXIntelligentSearchCurrent", "")
  }
  var walker = document.createTreeWalker(
    document.body,
    NodeFilter.SHOW_ELEMENT
  )
  parentsToNormalize = new Set()
  nodesToDelete = new Set()
  walkNodes(walker, node => {
    if (node.nodeName.toLowerCase() === "span" && node.className.indexOf('XxXIntelligentSearchHighlight') >= 0) {
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
function highlight(originalNode, offsets, wordOffsets, highlightClass = "XxXIntelligentSearchHighlight") {

  var spans = []
  var currentNode = originalNode
  var subtracted = 0
  var i = 0
  for (var offset of offsets) {
    if (HIGHLIGHT_STYLE === HIGHLIGHT_STYLE_SENTENCE) {
      var offsetWithinNode = offset[0] - subtracted
      if (offsetWithinNode < 0 || offsetWithinNode >= currentNode.textContent.length) {
        // We can't continue highlighting, because all subsequent offsets
        // are corrupt.
        break
      }

      var newNode = currentNode.splitText(offsetWithinNode)
      subtracted += offsetWithinNode

      currentNode = newNode
      newNode = currentNode.splitText(offset[1] - offset[0])
      subtracted += offset[1] - offset[0]

      var highlightSpan = document.createElement("span")
      highlightSpan.className = highlightClass
      highlightSpan.textContent = currentNode.textContent
      spans.push(highlightSpan)
      currentNode.parentNode.insertBefore(highlightSpan, currentNode)
      currentNode.parentNode.removeChild(currentNode)

      if (wordOffsets) {
        if (wordOffsets[i].length > 0) {
          highlight(highlightSpan.firstChild, wordOffsets[i], undefined, "XxXIntelligentSearchWord")
        }
      }
    }

    currentNode = newNode
    i += 1
  }

  return spans
}

gResultSpans = []
gHighlightedElement = null
