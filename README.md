# PearlFlow - Intelligent Dental Practice AI Assistant

🦷 **PearlFlow** is an agentic AI-powered dental practice management system that automates patient intake, triage, and intelligent appointment scheduling.

## Features

- **Multi-Agent Orchestration**: Hierarchical agent architecture with a root "Receptionist" agent delegating to specialized sub-agents
- **Intelligent Triage**: IntakeSpecialist agent conducts diagnostic dialogue with 80%+ accuracy
- **Revenue Optimization**: ResourceOptimiser agent uses heuristics for appointment scheduling
- **Proactive Engagement**: Automated incentive offers for schedule optimization
- **Embeddable Chat Widget**: Production-ready React component library
- **AHPRA Compliance**: Australian Healthcare advertising compliance filters

## Technology Stack

### Frontend
- React 18+ with Vite (Library Mode)
- TypeScript (strict mode)
- Tailwind CSS with 'pf-' prefix
- Storybook 8 for component documentation
- Vitest for testing

### Backend
- Python 3.11+ with FastAPI
- deepagents library (built on LangGraph)
- PostgreSQL with JSONB for agent state
- SSE for real-time streaming

### Infrastructure
- TurboRepo monorepo
- pnpm for JavaScript packages
- uv for Python packages
- Docker for containerization

## Project Structure

```
pearlflow/
├── apps/
│   ├── api/                    # Python/FastAPI Backend
│   │   ├── src/
│   │   │   ├── agents/         # Agent definitions
│   │   │   ├── tools/          # PMS integration tools
│   │   │   ├── models/         # SQLAlchemy models
│   │   │   ├── routes/         # API endpoints
│   │   │   ├── schemas/        # Pydantic schemas
│   │   │   └── core/           # Configuration
│   │   └── tests/
│   └── demo-web/               # Next.js Demo Site
├── packages/
│   ├── chat-ui/                # React Component Library
│   │   ├── src/
│   │   │   ├── components/     # UI Components
│   │   │   ├── hooks/          # React Hooks
│   │   │   ├── context/        # React Context
│   │   │   └── types/          # TypeScript types
│   │   └── tests/
│   └── ts-client/              # Typed API Client
├── infrastructure/             # Terraform/Docker
├── turbo.json
└── package.json
```

## Quick Start

### Prerequisites

- Node.js 18+
- pnpm 9+
- Python 3.11+
- uv (Python package manager)
- PostgreSQL 15+
- Docker (optional)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd pearlflow

# Run the setup script
./init.sh

# Or step by step:
./init.sh install  # Install dependencies
./init.sh db       # Setup database
./init.sh dev      # Start development servers
```

### Development URLs

- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Frontend Demo**: http://localhost:3000
- **Storybook**: http://localhost:6006

## Usage

### Embedding the Chat Widget

```tsx
import { PearlFlowProvider, ChatWidget } from '@pearlflow/chat-ui';
import '@pearlflow/chat-ui/style.css';

function App() {
  return (
    <PearlFlowProvider
      apiKey="pf_live_..."
      theme={{ primary: '#00D4FF' }}
    >
      <ChatWidget
        position="bottom-right"
        defaultOpen={false}
      />
    </PearlFlowProvider>
  );
}
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/session` | POST | Create new chat session |
| `/session/{id}` | GET | Get session details |
| `/chat/message` | POST | Send message to agent |
| `/chat/stream/{id}` | GET | SSE stream for responses |
| `/appointments/available` | GET | Get available slots |
| `/appointments` | POST | Book appointment |
| `/patients/lookup` | GET | Lookup patient by phone |
| `/heuristics/move-score` | POST | Calculate move score |

## Agent Architecture

### Root Agent: Receptionist
Main orchestrator that classifies intent and delegates to sub-agents:
- Pain/Emergency → IntakeSpecialist
- Booking → ResourceOptimiser

### Sub-Agent: IntakeSpecialist
Triage nurse for diagnostic dialogue:
- Pain level assessment (1-10)
- Red flag screening
- Priority score calculation

### Sub-Agent: ResourceOptimiser
Scheduling optimization with tools:
- `check_availability`: Find open slots
- `heuristic_move_check`: Calculate move scores
- `book_appointment`: Create appointments
- `send_move_offer`: Generate incentive offers

## Testing

```bash
# Run all tests
./init.sh test

# Backend tests only
cd apps/api && uv run pytest

# Frontend tests only
pnpm test

# E2E tests
pnpm test:e2e
```

## Compliance

- **AHPRA**: Australian Health Practitioner Regulation Agency advertising compliance
- **APP**: Australian Privacy Principles adherence
- **Security**: Data encryption at rest and in transit

## License

MIT

## Contributing

See [CONTRIBUTING.md](./docs/CONTRIBUTING.md) for guidelines.
