# Frontend - Stupid Chat Bot

React frontend for the Stupid Chat Bot application, built with Vite.

## Structure

```
frontend/
├── src/
│   ├── components/      # React components (to be added in Phase 2)
│   ├── services/        # API and WebSocket services (to be added in Phase 2)
│   ├── App.jsx          # Main App component
│   ├── App.css          # App styles
│   ├── main.jsx         # Application entry point
│   └── index.css        # Global styles
├── public/              # Static assets
├── index.html          # HTML template
├── package.json        # Node dependencies and scripts
├── vite.config.js      # Vite configuration
└── .eslintrc.cjs       # ESLint configuration
```

## Setup

1. Install dependencies:
```bash
npm install
```

2. Run the development server:
```bash
npm run dev
```

The app will be available at http://localhost:5173

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Features (Phase 1)

- Basic React application with Vite
- Backend health check integration
- Gradient background design
- Responsive layout

More features will be added in Phase 2 (Chat UI) and Phase 3 (AI integration).

## Development

### Linting
```bash
npm run lint
```

### Formatting (with Prettier)
```bash
npx prettier --write .
```
