# Satellite Soil Telemetry Platform

Multi-tenant IoT platform processing satellite telemetry from Globalstar SmartOne C devices for real-time soil monitoring. Features a full-stack dashboard with time-series analytics, device management, and automated alerting.

## 🏗️ Architecture

- **Backend**: FastAPI (Python) with async request handling
- **Frontend**: React + TypeScript + Vite with real-time charts
- **Database**: PostgreSQL + PostGIS for geospatial data
- **Infrastructure**: 
  - Fly.io (São Paulo region) for compute
  - Neon PostgreSQL (AWS South America East)
  - Cloudflare (DNS, SSL, WAF)
- **Telemetry**: Globalstar SmartOne C satellite devices

## 🚀 Key Features

- **Real-time Data Ingestion**: Fast ACK → queue → decode → store pipeline
- **Multi-tenant Architecture**: Supports multiple farms/devices
- **Time-series Analytics**: Downsampled queries (max 800 points) for efficient charting
- **Device Status Monitoring**: Automated alerting (red/amber/green/blue/stale/offline)
- **Geospatial Visualization**: Interactive map with device locations
- **Automated Migrations**: Database schema updates run automatically on deployment

## 📊 Tech Stack

**Backend:**
- FastAPI, SQLAlchemy, Alembic (migrations)
- Pydantic for data validation
- Custom decoders for Globalstar hex payloads

**Frontend:**
- React 18, TypeScript
- Vite for fast development
- Tailwind CSS for styling
- Recharts for time-series visualization
- Leaflet for interactive maps
- React Query for data fetching

**Infrastructure:**
- Docker for containerization
- Terraform for IaC
- Fly.io for deployment
- Alembic for database migrations

## 🛠️ Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker Desktop (for local database)
- PostgreSQL client tools

### Backend Setup

```bash
# Install dependencies
cd api
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your DATABASE_URL

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

API will be available at `http://localhost:8000`

### Frontend Setup

```bash
cd web
npm install
npm run dev
```

Frontend will be available at `http://localhost:5173`

### Local Database (Docker)

```bash
# Start PostgreSQL + PostGIS
docker compose up -d db

# Verify it's running
docker compose ps

# Run migrations
alembic upgrade head
```

## 📦 Deployment & Updates

### Automatic Database Migrations

The platform is configured for **zero-downtime updates**:

1. **Automatic migrations on deploy**: Every `fly deploy` automatically runs `alembic upgrade head` via the `release_command` in `fly.toml`
2. **Versioned migrations**: All schema changes are tracked in `api/alembic/versions/`
3. **Rollback support**: Use `alembic downgrade -1` if needed

### Deploying Updates

```bash
# 1. Test migrations locally first (recommended)
alembic upgrade head

# 2. Deploy to Fly.io (migrations run automatically)
fly deploy

# 3. Verify deployment
fly status
fly logs
```

### Environment Variables

Set secrets in Fly.io:

```bash
fly secrets set \
  DATABASE_URL="postgresql+psycopg2://..." \
  UPLINK_TOKEN="..." \
  ALERTS_ENABLED=true \
  EXPECTED_INTERVAL_MIN=60
```

See `DEPLOYMENT_CHECKLIST.md` for detailed deployment procedures.

## 📡 API Endpoints

### Device Management
- `GET /v1/devices` - List all devices
- `GET /v1/devices/attention` - Devices needing attention (sorted by priority)

### Telemetry Ingestion
- `POST /v1/uplink/receive` - Receive satellite telemetry (Globalstar webhook)

### Metrics & Analytics
- `GET /v1/metrics/summary` - Summary KPIs (avg moisture, temp, device counts)
- `GET /v1/metrics/moisture-series` - Time-series moisture data
- `GET /v1/metrics/temp-series` - Time-series temperature data

### Readings
- `GET /v1/readings/latest` - Latest readings across devices

See `GLOBALSTAR_DELIVERY_SPEC.md` for detailed API specification.

## 🧪 Testing

```bash
# Run backend tests
pytest tests/

# Test API endpoints locally
curl http://localhost:8000/
curl http://localhost:8000/v1/devices
```

## 📚 Documentation

- [Project Structure](./docs/PROJECT_STRUCTURE.md) - Explanation of repository organization
- [Globalstar Integration Spec](./docs/GLOBALSTAR_DELIVERY_SPEC.md) - API specification for satellite device integration
- [Deployment Checklist](./docs/DEPLOYMENT_CHECKLIST.md) - Step-by-step deployment guide
- [Update Guide](./docs/UPDATE_GUIDE.md) - How to deploy updates and handle migrations
- [Frontend README](./web/README.md) - Frontend development guide

## 🔧 Database Migrations

### Creating a New Migration

```bash
# Generate migration from model changes
alembic revision --autogenerate -m "description of changes"

# Review the generated migration file
# Edit if needed, then apply:
alembic upgrade head
```

### Migration Best Practices

1. **Test locally first**: Always test migrations against a local database
2. **Use Neon branches**: Test migrations on a Neon branch before production
3. **Review generated SQL**: Check autogenerated migrations before applying
4. **Backup before major changes**: Use Neon's branching feature for safety

## 🌐 Production

- **API**: https://api.soilreadings.com
- **Web Dashboard**: https://api.soilreadings.com/static/readings.html
- **Status**: Live and processing satellite telemetry

## 📝 Project Structure

```
soilprobe-platform/
├── api/                 # FastAPI backend
│   ├── app/
│   │   ├── models/      # SQLAlchemy models
│   │   ├── routers/      # API route handlers
│   │   ├── services/    # Business logic
│   │   ├── decoders/    # Globalstar payload decoders
│   │   └── db/          # Database session management
│   ├── alembic/         # Database migrations
│   └── Dockerfile       # Production container
├── web/                 # React frontend
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── pages/       # Page components
│   │   └── api/         # API client & hooks
│   └── vite.config.ts   # Build configuration
├── infra/               # Infrastructure as Code
│   └── terraform/       # Terraform modules
├── scripts/             # Utility scripts
└── tests/               # Test suite
```

## 🔐 Security

- All API endpoints require authentication tokens
- Environment variables stored securely in Fly.io secrets
- HTTPS enforced via Cloudflare
- Database connections use SSL

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Test migrations locally
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Built with**: FastAPI, React, TypeScript, PostgreSQL, Docker, Fly.io
