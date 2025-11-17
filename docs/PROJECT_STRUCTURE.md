# Project Structure

This document explains the organization of files and folders in this repository.

## Root Directory Files

These files are intentionally kept in the root directory:

### Essential Files (Must Stay in Root)
- **`README.md`** - Main project documentation (GitHub standard)
- **`LICENSE`** - MIT License (GitHub standard location)
- **`requirements.txt`** - Root-level Python dependencies (standard location)

### Configuration Files (Tools Expect in Root)
- **`alembic.ini`** - Database migration configuration (references `api/alembic`)
- **`docker-compose.yml`** - Docker Compose configuration (standard location)
- **`fly.toml`** - Fly.io deployment configuration (Fly.io requires root location)
- **`pyrightconfig.json`** - Pyright type checking configuration (applies to entire project)

## Directory Structure

```
soilprobe-platform/
├── api/                    # Backend FastAPI application
│   ├── app/                # Application code
│   │   ├── models/         # SQLAlchemy database models
│   │   ├── routers/        # API route handlers
│   │   ├── services/       # Business logic
│   │   ├── decoders/       # Globalstar payload decoders
│   │   └── db/             # Database session management
│   ├── alembic/            # Database migrations
│   └── Dockerfile          # Production container build
│
├── web/                     # Frontend React application
│   ├── src/                 # Source code
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   └── api/            # API client & hooks
│   └── package.json        # Frontend dependencies
│
├── docs/                    # Documentation
│   ├── DEPLOYMENT_CHECKLIST.md
│   ├── GLOBALSTAR_DELIVERY_SPEC.md
│   ├── UPDATE_GUIDE.md
│   └── PROJECT_STRUCTURE.md (this file)
│
├── scripts/                 # Utility scripts
│   ├── seed_test_data.py   # Generate test data
│   ├── verify_status.py    # Production verification
│   └── *.ps1               # PowerShell scripts
│
├── tests/                   # Test suite
│   ├── api/                # API tests
│   ├── decoders/           # Decoder tests
│   └── e2e/                # End-to-end tests
│
├── infra/                   # Infrastructure as Code
│   └── terraform/          # Terraform modules
│
├── data/                    # Test data and fixtures
│   └── fixtures/           # XML test files
│
└── ops/                     # Operations scripts
    └── scripts/            # Operational utilities
```

## Why These Files Stay in Root

### `alembic.ini`
- References `api/alembic` for migration scripts
- Alembic expects this file in the project root
- Path: `script_location = api/alembic`

### `docker-compose.yml`
- Standard location for Docker Compose files
- References paths relative to root (e.g., `api/Dockerfile`)
- Used for local development setup

### `fly.toml`
- Fly.io deployment tool requires this in root
- Contains deployment configuration
- References `api/Dockerfile` for builds

### `pyrightconfig.json`
- Type checking configuration for entire project
- Applies to both `api/` and `scripts/` directories
- Could be moved but root is standard location

### `requirements.txt`
- Root-level Python dependencies
- Standard location for project-wide dependencies
- API-specific deps are in `api/requirements.txt`

## File Organization Principles

1. **Tool Requirements**: Files stay in root if tools require it (Fly.io, Alembic, Docker)
2. **Standards**: Follow GitHub/Python/Node.js conventions (README, LICENSE in root)
3. **Logical Grouping**: Related files grouped in folders (docs/, scripts/, tests/)
4. **Clear Structure**: Each major component has its own directory (api/, web/)

## Adding New Files

- **Configuration files**: Add to root if tool requires it, otherwise consider `config/` folder
- **Documentation**: Add to `docs/` folder
- **Scripts**: Add to `scripts/` folder
- **Tests**: Add to `tests/` with appropriate subfolder

