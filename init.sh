#!/bin/bash
#
# PearlFlow - Intelligent Dental Practice AI Assistant
# Development Environment Setup Script
#
# Usage: ./init.sh [command]
#   init.sh          - Full setup (install deps, setup DB, start servers)
#   init.sh install  - Install dependencies only
#   init.sh db       - Setup database only
#   init.sh dev      - Start development servers only
#   init.sh test     - Run all tests
#   init.sh clean    - Clean build artifacts and node_modules
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_PORT=8000
FRONTEND_PORT=3000
POSTGRES_PORT=5432
POSTGRES_DB="pearlflow"
POSTGRES_USER="pearlflow"
POSTGRES_PASSWORD="pearlflow_dev"

# Print banner
print_banner() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║                                                                   ║"
    echo "║   🦷 PearlFlow - Intelligent Dental Practice AI Assistant 🦷     ║"
    echo "║                                                                   ║"
    echo "║   Multi-agent orchestration with deepagents + LangGraph           ║"
    echo "║   React widget + FastAPI + PostgreSQL                             ║"
    echo "║                                                                   ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Print step message
step() {
    echo -e "${GREEN}➤ $1${NC}"
}

# Print info message
info() {
    echo -e "${BLUE}  ℹ $1${NC}"
}

# Print warning message
warn() {
    echo -e "${YELLOW}  ⚠ $1${NC}"
}

# Print error message
error() {
    echo -e "${RED}  ✖ $1${NC}"
}

# Print success message
success() {
    echo -e "${GREEN}  ✔ $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    step "Checking prerequisites..."

    local missing=()

    # Check Node.js
    if command_exists node; then
        local node_version=$(node --version)
        success "Node.js: $node_version"
    else
        missing+=("Node.js (v18+)")
    fi

    # Check pnpm
    if command_exists pnpm; then
        local pnpm_version=$(pnpm --version)
        success "pnpm: $pnpm_version"
    else
        missing+=("pnpm (npm install -g pnpm)")
    fi

    # Check Python
    if command_exists python3; then
        local python_version=$(python3 --version)
        success "Python: $python_version"
    else
        missing+=("Python 3.11+")
    fi

    # Check uv (Python package manager)
    if command_exists uv; then
        local uv_version=$(uv --version)
        success "uv: $uv_version"
    else
        missing+=("uv (curl -LsSf https://astral.sh/uv/install.sh | sh)")
    fi

    # Check Docker (optional but recommended)
    if command_exists docker; then
        local docker_version=$(docker --version)
        success "Docker: $docker_version (optional)"
    else
        warn "Docker not found (optional, needed for production)"
    fi

    # Check PostgreSQL
    if command_exists psql; then
        local pg_version=$(psql --version)
        success "PostgreSQL: $pg_version"
    else
        warn "PostgreSQL client not found (install postgresql)"
    fi

    # Exit if missing required tools
    if [ ${#missing[@]} -ne 0 ]; then
        echo ""
        error "Missing required tools:"
        for tool in "${missing[@]}"; do
            error "  - $tool"
        done
        echo ""
        info "Please install the missing tools and run this script again."
        exit 1
    fi

    echo ""
}

# Install JavaScript dependencies
install_js_deps() {
    step "Installing JavaScript dependencies with pnpm..."

    cd "$PROJECT_ROOT"

    if [ -f "pnpm-lock.yaml" ]; then
        pnpm install --frozen-lockfile
    else
        pnpm install
    fi

    success "JavaScript dependencies installed"
}

# Install Python dependencies
install_python_deps() {
    step "Installing Python dependencies with uv..."

    cd "$PROJECT_ROOT/apps/api"

    # Create virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
        uv venv
    fi

    # Install dependencies
    uv sync

    success "Python dependencies installed"
}

# Install all dependencies
install_deps() {
    install_js_deps
    install_python_deps
}

# Setup PostgreSQL database
setup_database() {
    step "Setting up PostgreSQL database..."

    # Check if PostgreSQL is running
    if ! pg_isready -q 2>/dev/null; then
        warn "PostgreSQL is not running. Attempting to start with Docker..."

        if command_exists docker; then
            # Start PostgreSQL with Docker
            docker run -d \
                --name pearlflow-postgres \
                -e POSTGRES_USER="$POSTGRES_USER" \
                -e POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
                -e POSTGRES_DB="$POSTGRES_DB" \
                -p "$POSTGRES_PORT:5432" \
                -v pearlflow-pgdata:/var/lib/postgresql/data \
                postgres:15-alpine

            # Wait for PostgreSQL to be ready
            info "Waiting for PostgreSQL to start..."
            sleep 5

            success "PostgreSQL started with Docker"
        else
            error "PostgreSQL is not running and Docker is not available"
            info "Please start PostgreSQL manually or install Docker"
            exit 1
        fi
    else
        success "PostgreSQL is running"
    fi

    # Run database migrations
    cd "$PROJECT_ROOT/apps/api"

    if [ -f "src/core/database.py" ]; then
        info "Running database migrations..."
        uv run python -c "from src.core.database import init_db; init_db()" 2>/dev/null || true
        success "Database initialized"
    else
        warn "Database initialization script not found (will be created later)"
    fi
}

# Start development servers
start_dev_servers() {
    step "Starting development servers..."

    # Start backend
    info "Starting FastAPI backend on port $BACKEND_PORT..."
    cd "$PROJECT_ROOT/apps/api"
    uv run uvicorn src.main:app --reload --port "$BACKEND_PORT" &
    BACKEND_PID=$!

    # Wait for backend to start
    sleep 2

    # Start frontend
    info "Starting React frontend on port $FRONTEND_PORT..."
    cd "$PROJECT_ROOT"
    pnpm --filter demo-web dev &
    FRONTEND_PID=$!

    # Start Storybook (optional)
    # info "Starting Storybook on port 6006..."
    # pnpm --filter @pearlflow/chat-ui storybook &
    # STORYBOOK_PID=$!

    success "Development servers started"
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════════${NC}"
    echo ""
    info "🚀 PearlFlow is running!"
    echo ""
    info "  API:       http://localhost:$BACKEND_PORT"
    info "  Swagger:   http://localhost:$BACKEND_PORT/docs"
    info "  ReDoc:     http://localhost:$BACKEND_PORT/redoc"
    info "  Frontend:  http://localhost:$FRONTEND_PORT"
    # info "  Storybook: http://localhost:6006"
    echo ""
    info "Press Ctrl+C to stop all servers"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════════${NC}"
    echo ""

    # Wait for interrupt
    trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM
    wait
}

# Run tests
run_tests() {
    step "Running tests..."

    echo ""
    info "Running Python backend tests..."
    cd "$PROJECT_ROOT/apps/api"
    uv run pytest tests/ -v --cov=src --cov-report=term-missing

    echo ""
    info "Running JavaScript frontend tests..."
    cd "$PROJECT_ROOT"
    pnpm test

    echo ""
    info "Running Playwright E2E tests..."
    pnpm --filter @pearlflow/chat-ui test:e2e

    success "All tests completed"
}

# Clean build artifacts
clean() {
    step "Cleaning build artifacts..."

    cd "$PROJECT_ROOT"

    # Remove node_modules
    find . -name "node_modules" -type d -prune -exec rm -rf {} \; 2>/dev/null || true

    # Remove Python caches
    find . -name "__pycache__" -type d -prune -exec rm -rf {} \; 2>/dev/null || true
    find . -name ".pytest_cache" -type d -prune -exec rm -rf {} \; 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true

    # Remove build directories
    find . -name "dist" -type d -prune -exec rm -rf {} \; 2>/dev/null || true
    find . -name ".next" -type d -prune -exec rm -rf {} \; 2>/dev/null || true
    find . -name ".turbo" -type d -prune -exec rm -rf {} \; 2>/dev/null || true

    # Remove lock files (optional - uncomment if needed)
    # rm -f pnpm-lock.yaml
    # rm -f apps/api/uv.lock

    success "Clean complete"
}

# Full setup
full_setup() {
    print_banner
    check_prerequisites
    install_deps
    setup_database
    start_dev_servers
}

# Main
case "${1:-}" in
    install)
        print_banner
        check_prerequisites
        install_deps
        ;;
    db)
        print_banner
        setup_database
        ;;
    dev)
        print_banner
        start_dev_servers
        ;;
    test)
        print_banner
        run_tests
        ;;
    clean)
        print_banner
        clean
        ;;
    help|--help|-h)
        print_banner
        echo "Usage: ./init.sh [command]"
        echo ""
        echo "Commands:"
        echo "  (none)   - Full setup (install deps, setup DB, start servers)"
        echo "  install  - Install dependencies only"
        echo "  db       - Setup database only"
        echo "  dev      - Start development servers only"
        echo "  test     - Run all tests"
        echo "  clean    - Clean build artifacts and node_modules"
        echo "  help     - Show this help message"
        echo ""
        ;;
    *)
        full_setup
        ;;
esac
