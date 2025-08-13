<<<<<<< HEAD
# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default tseslint.config([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      ...tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      ...tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      ...tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default tseslint.config([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```
=======
# CivicNavigator Frontend

A modern, responsive frontend for CivicNavigator, a civic engagement platform where residents can:
- Report incidents (e.g., road maintenance, waste management)
- Chat with a civic bot
- View and manage reported incidents (staff accounts)

---

## 🚀 Tech Stack

- **Framework**: React 19 + Vite
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios
- **Linting**: ESLint (`@typescript-eslint`), Prettier
- **State Management**: React Hooks

---

## 📂 Project Structure

```
src/
  components/     # UI components (forms, layout, etc.)
  pages/          # Page-level components (Home, Chat, Incidents)
  utils/          # API and auth helpers
  types/          # Shared TypeScript interfaces
  App.tsx         # Root component
  main.tsx        # Entry point
```

---

## 🔧 Setup

### 1. Install dependencies
```bash
npm install
```

### 2. Configure environment variables
Create `.env` in `frontend/`:
```
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### 3. Start development server
```bash
npm run dev
```

---

## 📝 Key Components

- **IncidentForm.tsx** — Reports new incidents with validation and category dropdown.
- **RegisterForm.tsx** — Creates new user accounts.
- **LoginForm.tsx** — Authenticates users and stores JWT tokens.
- **CivicLayout.tsx** — Global layout with navigation.
- **utils/api.ts** — Axios instance and API helper functions.
- **utils/auth.ts** — Token storage and auth helpers.

---

## ✅ Lint & Format

```bash
npm run lint
npm run format
```

---

---

## tests

```bash
npx vitest run
```

---

## 🔌 API Integration

The frontend communicates with the backend via:
- **POST /api/auth/register** — User registration
- **POST /api/auth/login** — Login
- **POST /api/incidents** — Report incident
- **GET /api/staff/incidents** — Fetch all incidents (staff only)
- **POST /api/chat/message** — Chat with civic bot

---

## 📦 Build for Production

```bash
npm run build
```
The build output will be in `dist/`.

---

## 👥 Roles

- **Resident**: Can chat with bot, report incidents, track their status.
- **Staff**: Can manage incidents, respond to reports.
>>>>>>> 6e9b7e2557e0753d1a7caeffe309a05f5f14357b
