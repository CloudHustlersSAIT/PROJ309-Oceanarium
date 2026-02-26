# Oceanarium Frontend

Vue 3 frontend for the Oceanarium Tour Scheduling system. Provides an interactive interface for administrators and guides to manage tours, bookings, schedules, resources, and view dashboard metrics.

## Tech Stack

| Category         | Technology              |
| ---------------- | ----------------------- |
| Framework        | Vue 3 (Composition API) |
| Build Tool       | Vite 7                  |
| Styling          | Tailwind CSS 4          |
| State Management | Pinia 3                 |
| Routing          | Vue Router 4            |
| HTTP Client      | Axios                   |
| Authentication   | Firebase Auth           |
| Code Formatting  | Prettier                |

## Prerequisites

- Node.js `^20.19.0` or `>=22.12.0`
- Backend API running (see [backend/README.md](../backend/README.md))

## Getting Started

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The app runs on http://localhost:5173 and connects to the backend API at `http://localhost:8000` by default.

## Available Scripts

| Script            | Description                           |
| ----------------- | ------------------------------------- |
| `npm run dev`     | Start Vite dev server with hot reload |
| `npm run build`   | Build for production                  |
| `npm run preview` | Preview production build locally      |
| `npm run format`  | Format all source files with Prettier |

## Environment Variables

Create a `.env` file in the `frontend/` directory. Firebase variables are optional for local development — the app runs in unauthenticated mode when they are missing.

| Variable                            | Description                  | Required                                 |
| ----------------------------------- | ---------------------------- | ---------------------------------------- |
| `VITE_API_BASE_URL`                 | Backend API URL              | No (defaults to `http://localhost:8000`) |
| `VITE_FIREBASE_API_KEY`             | Firebase API key             | No                                       |
| `VITE_FIREBASE_AUTH_DOMAIN`         | Firebase auth domain         | No                                       |
| `VITE_FIREBASE_PROJECT_ID`          | Firebase project ID          | No                                       |
| `VITE_FIREBASE_STORAGE_BUCKET`      | Firebase storage bucket      | No                                       |
| `VITE_FIREBASE_MESSAGING_SENDER_ID` | Firebase messaging sender ID | No                                       |
| `VITE_FIREBASE_APP_ID`              | Firebase app ID              | No                                       |

## Project Structure

```
frontend/
├── public/                  # Static files served as-is
├── src/
│   ├── assets/              # Icons, images, videos, CSS
│   ├── components/          # Reusable Vue components
│   │   ├── OceanError.vue       # Error display
│   │   ├── Sidebar.vue          # Navigation sidebar
│   │   └── SidebarButton.vue    # Sidebar button
│   ├── contexts/            # Composables
│   │   └── authContext.js       # Authentication state & methods
│   ├── router/              # Vue Router configuration
│   │   └── index.js             # Route definitions & guards
│   ├── services/            # API service layer
│   │   └── api.js               # Backend API calls (Axios)
│   ├── stores/              # Pinia state stores
│   ├── utils/               # Utilities
│   │   └── firebase.js          # Firebase initialization
│   ├── views/               # Page-level components
│   │   ├── AssetsView.vue
│   │   ├── BookingsView.vue
│   │   ├── CalendarView.vue
│   │   ├── DashboardView.vue
│   │   ├── ForgotPasswordView.vue
│   │   ├── HomeView.vue
│   │   ├── LoginView.vue
│   │   ├── NotificationsView.vue
│   │   └── SettingsView.vue
│   ├── App.vue              # Root component
│   └── main.js              # Application entry point
├── .prettierrc.json         # Prettier config (no semis, single quotes, 100 chars)
├── jsconfig.json            # Path aliases (@ → ./src/)
├── package.json
└── vite.config.js           # Vite + Vue + Tailwind + DevTools config
```

## Authentication

Firebase Auth is used for user authentication. Route guards in `router/index.js` protect all routes except `/login` and `/forgot-password`.

When Firebase environment variables are not configured, the app runs in development mode with authentication checks disabled, allowing local development without a Firebase project.

## Deployment

The frontend is deployed to Vercel automatically via GitHub Actions when changes are pushed to the `main` branch in the `frontend/` directory. See the [frontend-deploy workflow](../.github/workflows/frontend-deploy.yaml) for details.

## Recommended IDE Setup

- [VS Code](https://code.visualstudio.com/) + [Vue (Official)](https://marketplace.visualstudio.com/items?itemName=Vue.volar)

### Browser DevTools

- **Chromium-based:** [Vue.js devtools](https://chromewebstore.google.com/detail/vuejs-devtools/nhdogjmejiglipccpnnnanhbledajbpd)
- **Firefox:** [Vue.js devtools](https://addons.mozilla.org/en-US/firefox/addon/vue-js-devtools/)
