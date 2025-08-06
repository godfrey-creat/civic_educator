# 🗺️ CivicNavigator

CivicNavigator is a modern, AI-powered civic chatbot MVP that enables residents to access local service information, file incident reports, and check their status through a single, accessible conversational interface. It also provides staff tools for triaging incidents and managing a curated knowledge base (KB), ensuring transparency and responsiveness.

> 🎯 **MVP Scope**: Streamline resident access to accurate civic information and services while empowering staff with tools to maintain and update the system efficiently.

---

## ✨ Features

### 🧑‍🤝‍🧑 Resident Features
- 💬 **Chat Interface**: Ask service-related questions (e.g., "When is garbage collected in South C?") and receive concise, grounded answers with numbered citations from the curated KB.
- 📝 **Incident Reporting**: Submit structured incident reports with fields for title, description, category (e.g., waste, streetlight), location, and contact information, receiving a unique reference ID.
- 📄 **Status Lookup**: Check the current status (e.g., NEW, IN_PROGRESS, RESOLVED), last update, and history of filed incidents using the reference ID.

### 🧑‍💼 Staff Features
- 🧰 **Knowledge Base Management**: Browse and search KB documents with relevance scores.
- 🔧 **Incident Triage** (Coming Soon): View, filter, and update incident statuses and notes.
- 📚 **KB Ingestion & Reindexing** (Coming Soon): Add or update KB documents and refresh the retrieval index.

---

## 📸 Screenshots

> *Screenshots will be added upon completion of styling and layout. Planned visuals include the chat interface, incident form, status lookup, and staff tools.*

---

## ⚙️ Tech Stack

### Frontend
- **[React 19](https://react.dev/)**: Component-based UI for a responsive, accessible single-page application.
- **[Vite](https://vitejs.dev/)**: Fast build tool for development and production.
- **[TypeScript](https://www.typescriptlang.org/)**: Static typing for robust frontend code.
- **[Tailwind CSS](https://tailwindcss.com/)**: Utility-first CSS for accessible, high-contrast styling.
- **[ESLint](https://eslint.org/) + [Prettier](https://prettier.io/)**: Code linting and formatting for consistency.

### Backend
- **[FastAPI](https://fastapi.tiangolo.com/)**: High-performance Python framework for RESTful APIs.
- **[SQLite](https://www.sqlite.org/)**: Lightweight, serverless database for incidents and KB storage.
- **[SentenceTransformers](https://www.sbert.net/)**: `all-MiniLM-L6-v2` model for retrieval-augmented generation (RAG) and intent classification.
- **[Uvicorn](https://www.uvicorn.org/)**: ASGI server for running FastAPI.

### Development Tools
- **GitHub**: Version control, issues, PRs, and project board for collaboration.
- **Pytest**: Unit and integration testing for backend.
- **Cypress** (Planned): End-to-end testing for frontend (optional for MVP).

---

## ✅ Prerequisites

To run CivicNavigator locally, ensure you have:
- **Node.js 18+**: For frontend development and Vite.
- **Python 3.9+**: For FastAPI backend and AI components.
- **pip**: Python package manager for installing dependencies.
- **SQLite**: Included in Python standard library.
- **Git**: For cloning the repository.
- **Browser**: Modern browser (e.g., Chrome, Firefox) for testing.

---

## 📦 Installation

Follow these steps to set up CivicNavigator locally:

### 🔹 1. Clone the Repository
```bash
git clone https://github.com/your-username/civicnavigator.git
cd civicnavigator
```

### 🔹 2. Frontend Setup (`/civicnavigator-frontend`)
```bash
cd civicnavigator-frontend
npm install
```
- Create a `.env` file by copying the example:
  ```bash
  cp .env.example .env
  ```
- Update `.env` with the backend URL:
  ```ini
  VITE_API_BASE_URL=http://localhost:9756
  ```

### 🔹 3. Backend Setup (`/backend`)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```
- Ensure `requirements.txt` includes:
  ```txt
  fastapi==0.115.0
  uvicorn==0.30.6
  sentence-transformers==3.1.1
  numpy==2.1.1
  ```
- Create a `.env` file by copying `.env.example`:
  ```bash
  cp .env.example .env
  ```
- Update `.env` with:
  ```ini
  API_BASE_URL=http://localhost:9756
  LOG_LEVEL=INFO
  DB_PATH=civicnavigator.db
  ```

### 🔹 4. Seed Data
- Initialize SQLite database with sample KB (2 documents) and incidents:
  ```bash
  python backend/init_db.py
  ```
  > *Note*: `init_db.py` will be provided to create tables and load sample data (e.g., garbage collection and streetlight documents).

---

## 🧪 Running Locally

### 🔹 Backend
```bash
cd backend
uvicorn main:app --reload --port 9756
```
- The backend will be available at `http://localhost:9756`.
- Check health: `curl http://localhost:9756/health`

### 🔹 Frontend
```bash
cd civicnavigator-frontend
npm run dev
```
- Open your browser at `http://localhost:5173`.

### 🔹 Smoke Tests
1. **Chat**: Ask "When is garbage collected in South C?" and verify cited response.
2. **Incident**: Submit an incident (e.g., title: "Broken Streetlight", category: "Streetlight") and note the reference ID.
3. **Status**: Enter the reference ID to check status (e.g., "NEW").
4. **Staff**: Toggle to staff role, search KB, and verify document list.

### 🔹 Shutdown
- Backend: Press `Ctrl+C` in the terminal running Uvicorn.
- Frontend: Press `Ctrl+C` in the terminal running Vite.

---

## 🚀 Deployment

### Local Deployment
- Follow the "Running Locally" steps above.
- Ensure `.env` files are configured correctly.
- SQLite database (`civicnavigator.db`) is created automatically on first run.

### Hosted Deployment (Preview)
For a production-like setup (optional for MVP):
#### Frontend
- Deploy `/civicnavigator-frontend` to **Vercel** or **Netlify**:
  - Push to a GitHub repository.
  - Connect to Vercel/Netlify, set `VITE_API_BASE_URL` to the deployed backend URL.
  - Build command: `npm run build`.
  - Output directory: `dist`.

#### Backend
- Deploy `/backend` to **Render**, **Railway**, or **Fly.io**:
  - Push to a GitHub repository.
  - Configure the platform to install `requirements.txt` and run `uvicorn main:app --host 0.0.0.0 --port $PORT`.
  - Ensure SQLite DB (`civicnavigator.db`) is writable and persisted (e.g., use a volume).
  - Set environment variables in the platform’s dashboard (e.g., `API_BASE_URL`, `DB_PATH`).

#### Notes
- Update `VITE_API_BASE_URL` in the frontend `.env` to match the backend’s deployed URL.
- Verify health endpoint (`/health`) post-deployment.
- Monitor logs via the hosting platform’s dashboard.

---

## 👥 Contributing

We welcome contributions to CivicNavigator! To contribute:
1. **Fork the Repository**:
   ```bash
   git clone https://github.com/godfrey-creat/civic_educator.git
   ```
2. **Create a Feature Branch**:
   ```bash
   git checkout -b feature/your-feature
   ```
3. **Commit Changes**:
   ```bash
   git commit -m "Add your feature description"
   ```
4. **Push to Your Branch**:
   ```bash
   git push origin feature/your-feature
   ```
5. **Open a Pull Request**:
   - Link to relevant GitHub issue.
   - Include a clear description of changes.
   - Ensure tests pass (run `npm test` for frontend, `pytest` for backend).

### Contribution Guidelines
- Follow ESLint/Prettier rules for code style.
- Write tests for new features (unit tests in `/backend/tests`, frontend tests in `/civicnavigator-frontend/src/tests`).
- Ensure accessibility (keyboard navigation, ARIA labels).
- Document API changes in `/docs/api.md`.
- Reference issues in PRs (e.g., "Fixes #123").

---

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

## 🙌 Acknowledgments

Made with civic spirit and a lot of code 💙 by the Team 4. Special thanks to:
- The open-source community for tools like React, FastAPI, and SentenceTransformers.
- Contributors and testers who help make civic services more accessible.

---

## 📋 Project Structure

```
civicnavigator/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── init_db.py           # SQLite schema and seed data
│   ├── requirements.txt     # Python dependencies
│   ├── tests/               # Pytest unit and integration tests
│   ├── logs/                # Application logs
│   └── .env.example         # Backend environment variables
├── civicnavigator-frontend/
│   ├── src/                 # React components and TypeScript code
│   ├── public/              # Static assets
│   ├── tests/               # Frontend tests
│   ├── vite.config.ts       # Vite configuration
│   ├── .env.example         # Frontend environment variables
│   └── package.json         # Node.js dependencies
├── docs/
│   ├── api.md               # API documentation
│   ├── eval/                # AI evaluation logs and metrics
│   ├── tests/               # Test reports
│   └── model_card.md        # AI model card
├── data/
│   ├── intents.json         # Synthetic dataset for intent classification
│   └── kb.json              # Sample KB documents
├── .gitignore
├── LICENSE
└── README.md
```

---

## 🔍 Observability

- **Logs**: View structured logs with request IDs in `/backend/logs/app.log`.
- **Metrics**: Basic counters (request volume, latency, errors) logged in `/backend/logs/metrics.log`.
- **Health Check**: Access `/health` endpoint to verify backend and AI model status.

---

## 🧪 Testing

### Frontend
- Run tests: `cd civicnavigator-frontend && npm test`
- Includes unit tests for components and integration tests for API calls.

### Backend
- Run tests: `cd backend && pytest tests/`
- Includes unit tests for API endpoints and integration tests for database and AI.

### Accessibility
- Manual tests for keyboard navigation and ARIA labels.
- Report in `/docs/tests/a11y.md`.

### Performance
- Chat response latency: P50 ≤ 1.5s, P95 ≤ 3.5s (measured locally).
- Report in `/docs/tests/performance.md`.

---

## 🤖 AI Component

- **Model**: `all-MiniLM-L6-v2` (SentenceTransformers) for RAG and intent classification.
- **Dataset**: Synthetic dataset with 200 examples (`/data/intents.json`).
- **Evaluation**: ≥70% correctness on 50-query set, F1=0.85, MRR=0.90, NDCG=0.88.
- **Model Card**: See `/docs/model_card.md` for details on intended use, metrics, limitations, and risks.

---

## 📬 Contact

For questions or feedback, create an issue on GitHub or contact the CivicNavigator team at [your-email@example.com](mailto:esaakadevsolutions.com).
