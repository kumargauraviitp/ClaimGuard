<div align="center">

# 🛡️ ClaimGuard

### AI-Powered Insurance Fraud Detection Platform

**Catch fraudulent insurance claims before a single rupee is paid out — powered by machine learning, explainable AI, and real-time risk scoring.**

</div>

---

## 📖 Table of Contents

1. [What Is This Project?](#-what-is-this-project)
2. [Why Does It Exist?](#-why-does-it-exist)
3. [How It Works (The Big Picture)](#-how-it-works-the-big-picture)
4. [What's Inside (Project Structure)](#-whats-inside-project-structure)
5. [Prerequisites](#-prerequisites)
6. [🚀 The Easy Way — Docker (Recommended)](#-the-easy-way--docker-recommended)
7. [The Hard Way — Manual Setup](#-the-hard-way--manual-setup)
   - [Step 1: PostgreSQL Database](#step-1-postgresql-database)
   - [Step 2: Redis Cache](#step-2-redis-cache)
   - [Step 3: Backend (FastAPI + ML)](#step-3-backend-fastapi--ml)
   - [Step 4: Frontend (Next.js)](#step-4-frontend-nextjs)
8. [🔑 Default Login](#-default-login)
9. [All Commands at Once](#-all-commands-at-once)
10. [Troubleshooting](#-troubleshooting)

---

## 🤔 What Is This Project?

**ClaimGuard** is a full-stack web application that insurance companies use to detect fraudulent claims automatically.

Imagine you're an insurance company. Every day, thousands of people file claims saying *"my car was in an accident, please pay me ₹2,00,000."* Some of those people are lying. How do you know which ones?

**ClaimGuard answers that question.** You upload a claim, and within seconds the AI tells you:

| What it shows | Example |
|---|---|
| 🎯 **Fraud Probability** | *"This claim is **94% likely** to be fraudulent"* |
| 🚦 **Risk Category** | *"Critical / High / Medium / Low"* |
| 🧠 **AI Explanation** | *"Red flags: policy not verified, no police report, policyholder at fault…"* |
| 📊 **SHAP Drivers** | *"The deductible amount pushed the score UP by +1.4 points"* |
| ⚠️ **Rule-Based Flags** | *"Unregistered vehicle, unverified identity"* |

It's like having a **detective that never sleeps**, looking at every claim for signs of fraud.

---

## 💡 Why Does It Exist?

Insurance fraud costs the industry **billions** every year. Those losses get passed on to honest customers as higher premiums. This platform exists to:

- ✅ **Stop fraud before payout** — catch it at the claim-filing stage, not after the money is gone
- ✅ **Explain the decision** — not a black box; every score comes with a human-readable explanation of *why*
- ✅ **Help investigators** — prioritize which claims need human review and which are safe to auto-approve
- ✅ **Scale infinitely** — a machine learning model can scan 10,000 claims in the time a human reviews 1

---

## 🧠 How It Works (The Big Picture)

```
                          ┌──────────────────────────────────────────┐
                          │           YOUR BROWSER (Port 80)          │
                          │         Next.js React Frontend            │
                          │  Dashboard · Claims · Analytics · Login   │
                          └──────────────────┬───────────────────────┘
                                             │  HTTP / API calls
                                             ▼
                          ┌──────────────────────────────────────────┐
                          │        FASTAPI BACKEND (Port 8000)        │
                          │                                          │
                          │  ┌─────────┐  ┌──────────┐  ┌────────┐  │
                          │  │ Fraud   │  │ SHAP     │  │ AI     │  │
                          │  │ Model   │  │ Explainer│  │ Agent  │  │
                          │  │(LightGBM)│  │(Why?)    │  │(LLM)   │  │
                          │  └────┬────┘  └────┬─────┘  └───┬────┘  │
                          └───────┼────────────┼─────────────┼──────┘
                                  │            │             │
                          ┌───────▼────┐  ┌────▼─────┐  ┌───▼──────┐
                          │ POSTGRES   │  │  REDIS   │  │ ML MODEL │
                          │ Database   │  │  Cache   │  │ Artifacts│
                          │ (claims,   │  │ (sessions│  │ (.pkl)   │
                          │  users…)   │  │  rate-   │  │          │
                          │            │  │  limit)  │  │          │
                          └────────────┘  └──────────┘  └──────────┘
```

**In plain English:**

1. **Frontend** (Next.js) is what you see in your browser — dashboards, forms, charts
2. **Backend** (FastAPI + Python) is the brain — it runs the ML model, scores claims, generates explanations
3. **PostgreSQL** stores all the data — claims, users, predictions, investigation reports
4. **Redis** is a super-fast cache — stores sessions and rate-limiting data
5. **ML Model** (LightGBM, serialized as `.pkl`) is the trained fraud detector

---

## 📦 What's Inside (Project Structure)

```
insurance/
├── 📁 backend/                 ← Python FastAPI server + ML engine
│   ├── 📁 app/
│   │   ├── main.py             ← Server entry point
│   │   ├── 📁 ml/              ← Machine learning (model serving, preprocessing)
│   │   ├── 📁 explainability/  ← SHAP explanations + AI narrative generator
│   │   ├── 📁 analytics/       ← Dashboard metrics & charts
│   │   ├── 📁 agent/           ← AI agents (multi-agent investigation)
│   │   └── 📁 auth/            ← Login, JWT, MFA
│   ├── 📁 artifacts/           ← Trained model files (.pkl, features.json)
│   ├── 📁 alembic/             ← Database migrations
│   ├── requirements.txt        ← Python dependencies
│   └── backend.Dockerfile      ← Docker build instructions for backend
│
├── 📁 frontend/                ← Next.js React web app
│   ├── 📁 src/
│   │   ├── 📁 app/             ← Pages (dashboard, claims, analytics, login)
│   │   ├── 📁 components/      ← UI components (charts, cards, modals)
│   │   └── 📁 lib/             ← API client, hooks, utilities
│   ├── package.json            ← Node.js dependencies
│   └── frontend.Dockerfile     ← Docker build instructions for frontend
│
├── 📁 postgres-init/           ← Database initialization scripts
├── 📄 docker-compose.yml       ← The master orchestration file
└── 📄 start.sh                 ← Quick start/stop helper script
```

---

## ✅ Prerequisites

### For Docker (Easy Way — Recommended)
| Tool | Version | How to check |
|------|---------|-------------|
| **Docker Desktop** | Latest | `docker --version` |
| **Docker Compose** | v2+ | `docker compose version` |

That's it. **Nothing else.** No Python, no Node.js, no PostgreSQL to install.

### For Manual Setup (Hard Way)
| Tool | Version | How to check |
|------|---------|-------------|
| **Python** | 3.11+ | `python3 --version` |
| **Node.js** | 20+ | `node --version` |
| **PostgreSQL** | 15+ | `psql --version` |
| **Redis** | 7+ | `redis-server --version` |

---

## 🚀 The Easy Way — Docker (Recommended)

> **Think of Docker like a shipping container.** Instead of installing and configuring 50 different things on your computer, Docker packages the entire app — database, server, frontend — into sealed containers that just work.

### Step 1: Start everything with one command

```bash
docker compose up -d
```

That's it. This single command will:

| Service | What it does | Port |
|---------|-------------|------|
| 🗄️ **PostgreSQL** | Starts the database | `5432` |
| ⚡ **Redis** | Starts the cache | `6379` |
| 🧠 **Backend** | Starts the FastAPI API + ML engine | `8000` |
| 🖥️ **Frontend** | Starts the Next.js web app | `80` |

> ⏱️ The first run takes **5-10 minutes** because it downloads and builds all images. Subsequent runs take ~10 seconds.

### Step 2: Open your browser

| Where | URL |
|-------|-----|
| **🖥️ Web App** | http://localhost |
| **📚 API Docs** | http://localhost:8000/docs |
| **❤️ Health Check** | http://localhost:8000/health |

### Step 3: Log in

```
Username: admin
Password: admin123
```

### Step 4: Stop everything when done

```bash
docker compose stop
```

### 🔨 If you changed code and need to rebuild

If you edited `requirements.txt` (backend) or `package.json` (frontend), Docker needs to rebuild the images:

```bash
# Rebuild everything from scratch
docker compose up --build -d

# Or rebuild just one service
docker compose build --no-cache backend
docker compose build --no-cache frontend
```

### 🧹 Nuke everything and start fresh (deletes all data!)

```bash
docker compose down -v
```

---

## 🔧 The Hard Way — Manual Setup

> Only do this if you can't or don't want to use Docker. Each piece runs directly on your machine.

---

### Step 1: PostgreSQL Database

> PostgreSQL is where all your claims, users, and predictions are permanently stored — like a giant, organized spreadsheet that never forgets.

**Install PostgreSQL 15+** (if not already installed):
```bash
# macOS (using Homebrew)
brew install postgresql@15
brew services start postgresql@15

# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Create the database and user:**
```bash
# Log in as the postgres superuser
sudo -u postgres psql          # macOS: psql postgres

# Run these SQL commands:
CREATE DATABASE insurance_db;
CREATE USER insurance_user WITH PASSWORD 'insurance_user';
GRANT ALL PRIVILEGES ON DATABASE insurance_db TO insurance_user;
\q
```

**Run database migrations** (creates all tables):
```bash
cd backend

# Set the database URL (adjust if your password is different)
export DATABASE_URL="postgresql+psycopg://insurance_user:insurance_user@localhost:5432/insurance_db"

# Run migrations
alembic upgrade head
```

---

### Step 2: Redis Cache

> Redis is a super-fast in-memory store. The app uses it for session management and rate-limiting (preventing brute-force login attacks).

**Install Redis 7+** (if not already installed):
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis-server
```

**Verify it's running:**
```bash
redis-cli ping
# Should return: PONG
```

---

### Step 3: Backend (FastAPI + ML)

> The backend is the brain. It's a Python server that loads the trained fraud-detection model, receives claim data, runs predictions, and explains the results.

**Create a Python virtual environment and install dependencies:**
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

**Create a `.env` file** in the project root (`insurance/.env`):
```env
DATABASE_URL=postgresql+psycopg://insurance_user:insurance_user@localhost:5432/insurance_db
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=your-secret-key-change-this
ENV=development
```

**Start the backend server:**
```bash
# From the backend/ directory, with venv activated
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

✅ You should see: `Uvicorn running on http://0.0.0.0:8000`

> 💡 The `--reload` flag means the server auto-restarts whenever you edit Python files — great for development.

---

### Step 4: Frontend (Next.js)

> The frontend is what you see in the browser — dashboards, charts, claim forms.

**Install dependencies and start the dev server:**
```bash
cd frontend

# Install Node.js dependencies
npm install --legacy-peer-deps

# Start the development server
npm run dev
```

✅ You should see: `Ready in Xs — started server on http://localhost:3000`

**But wait — the frontend needs to know where the backend is.**

In development mode (`npm run dev`), the frontend runs on port `3000`. It proxies API calls to the backend. Check `next.config.ts` — if running manually, you may need to point the rewrites to `localhost:8000` instead of `backend:8000`:

```typescript
// next.config.ts — for LOCAL (non-Docker) dev
async rewrites() {
  return [
    { source: '/api/:path*', destination: 'http://localhost:8000/api/:path*' },
    { source: '/auth/:path*', destination: 'http://localhost:8000/auth/:path*' },
    { source: '/health', destination: 'http://localhost:8000/health' },
  ];
}
```

Open: **http://localhost:3000**

---

## 🔑 Default Login

| Field | Value |
|-------|-------|
| **Username** | `admin` |
| **Password** | `admin123` |

> ⚠️ **Change this immediately** in any real deployment.

---

## 🎯 All Commands at Once

### Docker (Full Stack — Recommended)

```bash
# ──────────────────────────────────────────────
#  START EVERYTHING (first time takes 5-10 min)
# ──────────────────────────────────────────────
docker compose up -d

# ──────────────────────────────────────────────
#  CHECK IF EVERYTHING IS RUNNING
# ──────────────────────────────────────────────
docker compose ps

# ──────────────────────────────────────────────
#  VIEW LOGS (live)
# ──────────────────────────────────────────────
docker compose logs -f backend     # Backend logs
docker compose logs -f frontend    # Frontend logs
docker compose logs -f postgres    # Database logs

# ──────────────────────────────────────────────
#  STOP EVERYTHING (data is preserved)
# ──────────────────────────────────────────────
docker compose stop

# ──────────────────────────────────────────────
#  START AGAIN (fast — images already built)
# ──────────────────────────────────────────────
docker compose up -d

# ──────────────────────────────────────────────
#  REBUILD AFTER CODE CHANGES
#  (when you edited package.json or requirements.txt)
# ──────────────────────────────────────────────
docker compose up --build -d          # Rebuild everything
docker compose build --no-cache backend   # Rebuild just backend
docker compose build --no-cache frontend  # Rebuild just frontend

# ──────────────────────────────────────────────
#  DELETE EVERYTHING INCLUDING DATA
#  (⚠️ This wipes the database! Start from zero!)
# ──────────────────────────────────────────────
docker compose down -v
```

### Using the Helper Script

```bash
./start.sh start     # Start all services
./start.sh stop      # Stop all services
./start.sh restart   # Restart everything
./start.sh status    # Check what's running
./start.sh logs backend    # Tail backend logs
./start.sh rebuild frontend  # Rebuild frontend image
```

### Manual (No Docker)

```bash
# ──────────────────────────────────────────────
#  TERMINAL 1 — PostgreSQL (already running as service)
# ──────────────────────────────────────────────
# Just make sure it's running:
brew services start postgresql@15   # macOS
# sudo systemctl start postgresql   # Linux

# ──────────────────────────────────────────────
#  TERMINAL 2 — Redis (already running as service)
# ──────────────────────────────────────────────
brew services start redis           # macOS
# sudo systemctl start redis-server  # Linux

# ──────────────────────────────────────────────
#  TERMINAL 3 — Backend
# ──────────────────────────────────────────────
cd backend
source venv/bin/activate
export DATABASE_URL="postgresql+psycopg://insurance_user:insurance_user@localhost:5432/insurance_db"
export REDIS_URL="redis://localhost:6379/0"
export JWT_SECRET="your-secret-key"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# ──────────────────────────────────────────────
#  TERMINAL 4 — Frontend
# ──────────────────────────────────────────────
cd frontend
npm install --legacy-peer-deps
npm run dev
```

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| **`docker compose up` fails with network error** | Docker Desktop isn't running. Open the Docker Desktop app and wait for the whale icon to stop animating. |
| **Frontend loads but says "Connection refused"** | Backend isn't up yet. Check: `docker compose logs backend` |
| **Login says "Invalid username or password"** | The database might be empty. Run migrations: `docker compose exec backend alembic upgrade head` |
| **Port 80 / 8000 / 5432 already in use** | Something else is using that port. Stop it: `lsof -ti:80 \| xargs kill -9` |
| **`docker compose down -v` and still broken** | Remove old images: `docker compose build --no-cache` |
| **Backend says "production.pkl not found"** | ML model artifacts are missing. Check `backend/artifacts/` directory exists and contains `.pkl` files. |

---

<div align="center">

**Built with:** FastAPI · Next.js · LightGBM · PostgreSQL · Redis · SHAP · Docker

</div>
