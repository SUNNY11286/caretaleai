# CARETALE AI - Architecture Overview

## Project Structure

This document provides an overview of the layered architecture implementation for CARETALE AI.

### TypeScript Layers (src/)

The TypeScript codebase handles the interface and orchestration layers:

```
src/
├── patient-interaction-layer/      # Multimodal interfaces (text, voice, image)
├── multimodal-ingestion-layer/     # Input processing and normalization
├── ai-orchestration-layer/         # Task routing and pipeline coordination
├── knowledge-context-layer/        # RAG system integration
├── safety-governance-layer/        # Safety checks and audit logging
├── output-layer/                   # Patient and care team output formatting
└── shared/
    ├── types/                      # Common TypeScript interfaces
    └── utils/                      # Shared utility functions
```

### Python Components (python/src/)

The Python codebase handles AI pipelines and core processing:

```
python/src/
├── ai_pipelines/
│   ├── care_story/                 # Discharge note transformation
│   ├── understanding_verification/ # Confusion detection
│   ├── medication_clarification/   # Medication guidance
│   └── follow_up/                  # Reminders and engagement
├── rag_system/                     # Retrieval-Augmented Generation
├── safety/                         # Hallucination detection
├── models/                         # Core data models
└── utils/                          # Shared utilities
```

## Configuration Files

### TypeScript Configuration
- **package.json**: Node.js dependencies and scripts
- **tsconfig.json**: TypeScript compiler configuration
- **jest.config.js**: Jest testing framework configuration
- **.eslintrc.json**: ESLint code quality rules
- **.prettierrc**: Code formatting rules

### Python Configuration
- **pyproject.toml**: Python project metadata and tool configuration
- **requirements.txt**: Python dependencies
- **setup.py**: Package setup configuration

### Build Tools
- **Makefile**: Convenient commands for building, testing, and formatting

## Layer Responsibilities

### Patient Interaction Layer
Provides accessible, multimodal interfaces supporting text, voice, and image inputs with WCAG 2.1 AA compliance.

### Multimodal Ingestion Layer
Processes diverse input types through speech-to-text, image preprocessing, and input normalization.

### AI Orchestration Layer
Routes patient requests to appropriate specialized pipelines and coordinates multi-pipeline responses.

### AI Pipelines
Four specialized pipelines handle distinct aspects of patient care support:
- Care Story: Transforms discharge notes into patient-friendly narratives
- Understanding Verification: Detects confusion and provides clarifications
- Medication Clarification: Provides medication guidance and education
- Follow-Up: Manages reminders and engagement tracking

### Knowledge & Context Layer
Provides evidence-based medical context through RAG architecture with approved clinical guidelines.

### Safety & Governance Layer
Enforces medical scope boundaries, detects hallucinations, and maintains audit trails.

### Output Layer
Formats responses for patients and care teams with accessibility features and workflow integration.

## Development Workflow

### Initial Setup
```bash
make install    # Install all dependencies
```

### Building
```bash
make build      # Build TypeScript project
```

### Testing
```bash
make test       # Run all tests
make test-ts    # TypeScript tests only
make test-py    # Python tests only
```

### Code Quality
```bash
make lint       # Run linters
make format     # Format code
```

### Cleanup
```bash
make clean      # Remove build artifacts
```

## Next Steps

1. Implement data models and core interfaces (Task 1.3)
2. Set up testing infrastructure (Task 1.2)
3. Begin implementing individual layer components
4. Write comprehensive unit and property-based tests

## References

- Design Document: `.kiro/specs/caretale-ai/design.md`
- Requirements: `.kiro/specs/caretale-ai/requirements.md`
- Tasks: `.kiro/specs/caretale-ai/tasks.md`
