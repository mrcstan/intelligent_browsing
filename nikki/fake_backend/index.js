const express = require('express')
const cors = require('cors')

const app = express()
app.use(express.json())
app.use(cors())

app.post('/search', (req, res) => {
  console.log('Got request: ', req.body)

  res.json({ message: 'hello' })
})

const port = process.env.PORT || 8080
app.listen(port, () => {
  console.log(`Running test server at http://localhost:${port}`)
})
