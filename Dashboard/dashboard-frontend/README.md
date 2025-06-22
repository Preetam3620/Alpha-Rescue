# Dashboard Frontend

This is the frontend for the Alpha Rescue Dashboard, built with [Create React App](https://github.com/facebook/create-react-app) and [Tailwind CSS](https://tailwindcss.com/). It provides a real-time map and information panels for emergency response coordination.

## Features

- Real-time event updates via Server-Sent Events (SSE)
- Interactive Mapbox map showing user and agent locations
- Collapsible information panels for caller, fire department, hospital, police, and paramedic
- Modern UI with Tailwind CSS and Lucide icons

## Getting Started

### Prerequisites

- Node.js (v16 or higher recommended)
- npm

### Installation

1. Install dependencies:

   ```sh
   npm install
   ```

2. Start the development server:

   ```sh
   npm start
   ```

   The app will run at [http://localhost:3000](http://localhost:3000).

### Build for Production

To build the app for production:

```sh
npm run build
```

The build output will be in the `build/` directory.

### Running Tests

To run tests:

```sh
npm test
```

## Project Structure

- `src/` - React source code
  - `components/` - UI components (MapboxMap, UserInfoCard, etc.)
  - `output.css` - Tailwind CSS output
  - `types.ts` - TypeScript types for agent and user info
- `public/` - Static assets and HTML template

## Customization

- Mapbox access token is set in [`MapboxMap.tsx`](src/components/MapboxMap.tsx).
- Tailwind CSS is configured via `index.css` and `output.css`.

## Backend Integration

This frontend expects a backend server (see `dashboard-backend`) providing:
- `/events` SSE endpoint for real-time updates
- `/api/webhook` endpoint for posting new events

## Learn More

- [Create React App Documentation](https://facebook.github.io/create-react-app/docs/getting-started)
- [React Documentation](https://reactjs.org/)
- [Tailwind CSS Documentation](https://tailwindcss.com/)
- [Mapbox GL JS Documentation](https://docs.mapbox.com/mapbox-gl-js/)

---

© 2024