# Olho no Solo - React Frontend

Modern React dashboard for soil monitoring.

## Setup

```bash
cd web
npm install
```

## Development

```bash
npm run dev
```

Runs on `http://localhost:5173` (Vite default). Proxy configured to forward `/v1/*` to backend at `http://localhost:8000`.

## Build for Production

```bash
npm run build
```

Output goes to `dist/` folder. Can be served by FastAPI static files or deployed separately.

## Features

- ✅ Multi-select device filtering
- ✅ Depth chip selection (10-60cm)
- ✅ Time period presets (24h, 7d, 30d, 90d, YTD, Custom)
- ✅ URL state management (shareable URLs)
- ✅ Devices needing attention card
- ✅ Moisture and temperature charts
- ✅ Server-side downsampling (max 800 points)
- ✅ Responsive design

## API Endpoints Used

- `GET /v1/metrics/summary` - Summary KPIs
- `GET /v1/metrics/moisture-series` - Moisture time series
- `GET /v1/metrics/temp-series` - Temperature time series
- `GET /v1/devices/attention` - Devices needing attention
- `GET /v1/devices` - Device list
- `GET /v1/constants/thresholds` - Alert thresholds

