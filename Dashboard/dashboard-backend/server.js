// Basic Express server with webhook and SSE endpoints
const express = require('express');
const EventEmitter = require('events');

const app = express();
const PORT = process.env.PORT || 3000;

// Event emitter for broadcasting data to SSE clients
const agentEmitter = new EventEmitter();

// Helper to parse webhook payload (customize as needed)
function parse_webhook_payload(envelope) {
  // Example: just return the envelope as-is
  return envelope;
}

// Broadcast data to all SSE clients
function broadcastToClients(data) {
  agentEmitter.emit('data', data);
}

// Webhook endpoint
app.post('/api/webhook', express.json(), (req, res) => {
  const envelope = req.body;
  const data = parse_webhook_payload(envelope);
  broadcastToClients(data);
  res.sendStatus(200);
});

// SSE endpoint
app.get('/events', (req, res) => {
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    'Access-Control-Allow-Origin': '*',
    Connection: 'keep-alive'
  });
  // Send a comment to keep the connection alive
  res.write(': connected\n\n');

  // Listener for new data
  const onData = d => {
    res.write(`data: ${JSON.stringify(d)}\n\n`);
  };
  agentEmitter.on('data', onData);

  // Clean up on client disconnect
  req.on('close', () => {
    agentEmitter.off('data', onData);
    res.end();
  });
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
