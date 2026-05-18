# mini-agent
Mini Agent Framework, for local agent learning and research.

## Local Environment
- Mac book pro M5 Pro 48GB
- LM Studio/oMLX/vMLX
- Python 3.13
- Podman
- Kind (Kubernetes in Docker) v0.31.0
- Helm 4.2.0
- Kubectl v1.36.1


## Project Plan
- Model implementation
- Simple Agent implementation
- Tool using support
- Skills support
- Memory Management
- Context Management
- Simple web UI
- Build docker and prepare helm chart
- Deploy to local kind cluster


## Project Structure
```text
mini-agent/
├── backend/                    # Python Backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI application entry point
│   │   ├── config.py         # Application configuration
│   │   ├── log.py            # Logging configuration
│   │   │
│   │   ├── core/             # Core agent functionality
│   │   │   ├── __init__.py
│   │   │   ├── model.py      # Model interface and implementations
│   │   │   ├── agent.py      # Simple agent implementation
│   │   │   ├── memory.py     # Memory management system
│   │   │   └── context.py    # Context window management
│   │   │
│   │   ├── tools/            # Tool definitions
│   │   │   ├── __init__.py
│   │   │   ├── tool.py       # Tool base class and registry
│   │   │   └── builtins/     # Built-in tools
│   │   │       ├── __init__.py
│   │   │       └── file_tool.py
│   │   │
│   │   ├── skills/           # Skills module
│   │   │   ├── __init__.py
│   │   │   └── skill.py      # Skill definition and loader
│   │   │
│   │   └── api/              # API Routes
│   │       ├── __init__.py
│   │       ├── routes.py     # API route definitions
│   │       └── schemas.py    # Pydantic schemas
│   │
│   ├── tests/                # Unit and integration tests
│   │   ├── __init__.py
│   │   ├── test_model.py
│   │   ├── test_agent.py
│   │   ├── test_memory.py
│   │   └── test_context.py
│   │
│   ├── requirements.txt      # Python dependencies
│   └── Dockerfile           # Backend container build
│
├── frontend/                 # React Frontend
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   │   └── ChatInterface.tsx
│   │   ├── hooks/           # Custom React hooks
│   │   │   └── useAgent.ts
│   │   ├── services/        # API service layer
│   │   │   └── api.ts
│   │   ├── types/           # TypeScript type definitions
│   │   │   └── index.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   │
│   ├── public/              # Static assets
│   ├── package.json
│   ├── vite.config.ts      # Vite configuration
│   └── tsconfig.json       # TypeScript configuration
│
├── deploy/                   # Kubernetes Deployment
│   ├── kind/               # Kind cluster configuration
│   │   └── cluster.yaml
│   └── helm/               # Helm chart
│       ├── templates/
│       │   ├── deployment.yaml
│       │   ├── service.yaml
│       │   └── ingress.yaml
│       └── Chart.yaml
│
├── docs/                     # Project documentation
│   └── architecture.md     # Architecture decisions
│
├── .venv/                   # Python virtual environment (gitignored)
├── .env.example            # Environment variables template
├── .gitignore
├── LICENSE
├── README.md
└──Makefile                 # Common development tasks
```

