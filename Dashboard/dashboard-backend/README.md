# Dashboard Backend

This is the backend server for the Alpha Rescue Dashboard. It provides a webhook endpoint for receiving agent/user events and a Server-Sent Events (SSE) endpoint for real-time updates to the frontend.

## Features

- Webhook endpoint for receiving agent/user event data (`/api/webhook`)
- Server-Sent Events (SSE) endpoint for streaming real-time updates to clients (`/events`)
- Simple in-memory event broadcasting using Node.js EventEmitter
- CORS enabled for local development

## Getting Started

### Prerequisites

- Node.js (v16 or higher recommended)
- npm

### Installation

1. Install dependencies:

   ```sh
   npm install
   ```

2. Start the server:

   ```sh
   npm start
   ```

   The server will run on [http://localhost:3000](http://localhost:3000) by default.

## API Endpoints

### POST `/api/webhook`

Receives event data (agent/user info) as JSON in the request body and broadcasts it to all connected SSE clients.

**Example request:**

```json
{
  "type": "hospital",
  "name": "General Hospital",
  "address": "123 Main St",
  "distance": "2.3 miles",
  "contact": "555-1234",
  "lat": 37.7749,
  "lon": -122.4194
}
```

### GET `/events`

Streams real-time events to connected clients using Server-Sent Events (SSE). Used by the frontend to receive live updates.

## Project Structure

- [`server.js`](dashboard-backend/server.js): Main Express server with webhook and SSE endpoints
- [`package.json`](dashboard-backend/package.json): Project metadata and dependencies

## Customization

- Modify the `parse_webhook_payload` function in [`server.js`](dashboard-backend/server.js) to customize how webhook payloads are processed.

## License

MIT

---

© 2024 Alpha Rescue