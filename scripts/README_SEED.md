# Seed Test Data

This script generates realistic test data for development and demos.

## What it creates:
- **3 devices** (Field A North, Field A South, Field B Center)
- **30 days** of historical data
- **6 readings per day** (every 4 hours)
- **4 depths per reading** (10cm, 30cm, 60cm, 90cm)
- **Total: ~2,160 readings** across all devices

Data includes realistic:
- Moisture variations by depth and time of day
- Temperature cycles (daily and by depth)
- Natural variation and noise

## Run locally:

```powershell
cd C:\Users\kelly\Charlie_APP\Olho_no_solo\soilprobe-platform
python scripts/seed_test_data.py
```

Make sure your `.env` or `.env.compose` has the correct `DATABASE_URL` pointing to your Neon database.

## Run on Fly.io (production):

```powershell
cd C:\Users\kelly\Charlie_APP\Olho_no_solo\soilprobe-platform
fly ssh console -a soilprobe-api-floral-sound-9539
# Then inside the container:
python /app/scripts/seed_test_data.py
```

## After seeding:

1. Visit: `https://api.soilreadings.com/static/readings.html`
2. You should see:
   - Charts with 30 days of data
   - Multiple devices and depths
   - Time-series trends
   - Depth and device comparisons

## Notes:

- The script is **idempotent** - devices won't be duplicated if you run it multiple times
- Each run adds new readings (based on current date)
- To reset, you'd need to manually clear the database tables

