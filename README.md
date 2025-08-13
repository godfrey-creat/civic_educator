# CivicNavigator

CivicNavigator is a full-stack civic engagement platform that allows residents to:
- Report community issues (e.g., road damage, waste, water supply problems)
- Chat with a knowledge-based civic assistant
- View incident status updates
- Staff can triage, manage, and update incidents

---

## 🛠 Tech Stack

### Frontend
- React 19 + Vite
- TypeScript
- Tailwind CSS
- Axios
- ESLint + Prettier

### Backend
- FastAPI
- SQLAlchemy
- SQLite (dev) / PostgreSQL (prod-ready)
- JWT Authentication (`python-jose`)
- Password hashing (`passlib`)
- Pydantic validation
- SentenceTransformers (semantic search)

---

## 📂 Project Structure

```
frontend/             # React + TypeScript frontend
backend/
  app/
    auth.py          # Authentication routes & logic
    incidents.py     # Incident CRUD
    chat.py          # Civic bot chat endpoint
    database.py      # DB session and Base
    models.py        # SQLAlchemy models
    schemas.py       # Pydantic schemas
    utils.py         # Helper functions
    main.py          # FastAPI app entry
```

---

## 🚀 Setup

### 1. Clone repository
```bash
git clone https://github.com/godfrey-creat/civic_educator.git
cd civicnavigator
```

### 2. Backend setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Environment variables (`.env` in `backend`):
```
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=sqlite:///./civic.db
```

### 3. Frontend setup
```bash
cd frontend
npm install
npm run dev
```

---

## 🔌 API Overview

### Auth
- **POST /api/auth/register** — Create user account
- **POST /api/auth/login** — Login and get token

### Incidents
- **POST /api/incidents** — Report incident (resident)
- **GET /api/staff/incidents** — List all incidents (staff)
- **PUT /api/staff/incidents/{id}** — Update incident

### Chat
- **POST /api/chat/message** — Civic bot Q&A

---

## 📝 Development Guidelines

- Follow ESLint + Prettier rules
- Keep TypeScript strict
- Validate all backend inputs with Pydantic
- Secure all staff routes with JWT and role checks

---

## 📦 Deployment

- **Frontend**: Deploy `dist/` to Vercel/Netlify
- **Backend**: Deploy FastAPI app with Uvicorn + Gunicorn (e.g., on Railway, Render, AWS)

---

## 👥 Roles

- **Resident**: Can report incidents & chat
- **Staff**: Manage incident workflow