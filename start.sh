#!/bin/bash
# =============================================================================
#  Insurance Fraud Detection — start / stop / status / restart helper
#  Usage:  ./start.sh [start|stop|restart|status|logs|rebuild]
#
#  Postgres, Redis, Frontend → Docker
#  Backend → LOCAL (venv with all ML packages and model artifacts)
#  Read script.txt for full explanations.
# =============================================================================

set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

CMD="${1:-start}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ok()   { echo -e "${GREEN}✓ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠ $1${NC}"; }
err()  { echo -e "${RED}✗ $1${NC}"; }

check_docker() {
  if ! docker info >/dev/null 2>&1; then
    warn "Docker daemon not running. Starting Docker Desktop..."
    open -a Docker 2>/dev/null || { err "Docker Desktop not found. Install it first."; exit 1; }
    echo -n "Waiting for Docker to be ready"
    for i in $(seq 1 30); do
      if docker info >/dev/null 2>&1; then ok "Docker is ready"; return 0; fi
      echo -n "."; sleep 2
    done
    err "Docker did not start in time. Open Docker Desktop manually."
    exit 1
  fi
}

start_backend() {
  if lsof -ti:8000 >/dev/null 2>&1; then
    ok "Backend already running on port 8000"
    return 0
  fi
  echo "Starting backend (local venv)..."
  cd "$ROOT/backend"
  ./venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
  BACKEND_PID=$!
  echo "$BACKEND_PID" > /tmp/backend.pid
  cd "$ROOT"
  echo -n "Waiting for backend"
  for i in $(seq 1 30); do
    if curl -s -o /dev/null http://localhost:8000/docs 2>/dev/null; then
      ok "Backend is up (PID $BACKEND_PID, log: /tmp/backend.log)"
      return 0
    fi
    echo -n "."; sleep 2
  done
  err "Backend failed to start. Check: tail -30 /tmp/backend.log"
  exit 1
}

stop_backend() {
  if lsof -ti:8000 >/dev/null 2>&1; then
    lsof -ti:8000 | xargs kill 2>/dev/null || true
    ok "Backend stopped"
  else
    warn "Backend was not running"
  fi
}

case "$CMD" in
  start)
    echo "=== Starting Insurance Fraud Detection System ==="
    check_docker
    echo ""

    echo "[1/4] Starting PostgreSQL + Redis (Docker)..."
    docker compose up -d postgres redis >/dev/null 2>&1
    ok "Postgres + Redis containers started"

    echo "[2/4] Waiting for Postgres to be healthy..."
    echo -n "  Waiting"
    for i in $(seq 1 20); do
      STATUS=$(docker inspect --format='{{.State.Health.Status}}' insurance-postgres-1 2>/dev/null || echo "")
      if [ "$STATUS" = "healthy" ]; then ok "Postgres is healthy"; break; fi
      echo -n "."; sleep 2
    done

    echo "[3/4] Starting Backend (local venv)..."
    start_backend

    echo "[4/4] Starting Frontend (Docker)..."
    docker compose up -d frontend >/dev/null 2>&1
    ok "Frontend container started"

    echo ""
    echo "=== All services running ==="
    echo "  Frontend : http://localhost:80"
    echo "  Backend  : http://localhost:8000/docs"
    echo "  Login    : admin / password123"
    echo ""
    echo "  Status   : ./start.sh status"
    echo "  Logs     : ./start.sh logs backend"
    echo "  Stop     : ./start.sh stop"
    echo ""
    ;;

  stop)
    echo "=== Stopping all services ==="
    stop_backend
    echo "Stopping Docker containers..."
    docker compose stop frontend postgres redis >/dev/null 2>&1
    ok "All services stopped (data preserved)"
    echo "  To wipe all data too:  docker compose down -v"
    ;;

  restart)
    $0 stop
    sleep 2
    $0 start
    ;;

  status)
    echo "=== Service Status ==="
    # Docker services
    docker compose ps 2>/dev/null | grep -v "warning" || warn "Docker not running"
    echo ""
    # Backend
    if lsof -ti:8000 >/dev/null 2>&1; then
      ok "Backend: RUNNING (port 8000)"
    else
      err "Backend: NOT RUNNING"
    fi
    # Quick HTTP checks
    curl -s -o /dev/null -w "  Frontend HTTP  : %{http_code}  (http://localhost:80)\n" http://localhost:80 2>/dev/null || echo "  Frontend HTTP  : down"
    curl -s -o /dev/null -w "  Backend HTTP   : %{http_code}  (http://localhost:8000/health)\n" http://localhost:8000/health 2>/dev/null || echo "  Backend HTTP   : down"
    ;;

  logs)
    SERVICE="${2:-backend}"
    if [ "$SERVICE" = "backend" ]; then
      tail -f /tmp/backend.log
    else
      docker compose logs -f "$SERVICE"
    fi
    ;;

  rebuild)
    SERVICE="${2:-frontend}"
    echo "Rebuilding $SERVICE (this may take a few minutes)..."
    if [ "$SERVICE" = "frontend" ]; then
      docker compose build --no-cache frontend
      docker compose up -d frontend
      ok "Frontend rebuilt and restarted"
    elif [ "$SERVICE" = "backend" ]; then
      echo "Backend runs locally. To apply code changes, just restart it:"
      echo "  ./start.sh restart"
    else
      docker compose build --no-cache "$SERVICE" && docker compose up -d "$SERVICE"
    fi
    ;;

  *)
    echo "Usage: $0 {start|stop|restart|status|logs [service]|rebuild [service]}"
    echo ""
    echo "Commands:"
    echo "  start              Start all services (postgres, redis, backend, frontend)"
    echo "  stop               Stop all services (data is preserved)"
    echo "  restart            Stop then start everything"
    echo "  status             Show running status of all services"
    echo "  logs [service]     Tail logs (default: backend; or postgres/redis/frontend)"
    echo "  rebuild [service]  Rebuild a Docker image after code changes (default: frontend)"
    echo ""
    echo "Services: frontend, postgres, redis, backend"
    echo ""
    echo "For full documentation, read script.txt"
    exit 1
    ;;
esac
