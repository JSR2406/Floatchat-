# ORCA Deployment Guide

This guide covers deploying the ORCA Marine Intelligence Platform to production using Vercel (frontend), Railway/Render (backend API), and Supabase/Neon (PostgreSQL with PostGIS).

## Prerequisites

- GitHub account with this repository
- Vercel account
- Railway account (or Render)
- Supabase account (or Neon for PostgreSQL)
- API keys for:
  - OpenRouter (LLM)
  - Sarvam AI (STT)
  - ElevenLabs (TTS)
  - Google Cloud (Translation)

---

## 1. Database Setup (Supabase)

### Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Choose a region close to your users (e.g., `ap-south-1` for India)
3. Wait for project initialization (~2 minutes)

### Enable PostGIS Extension

1. In Supabase Dashboard, go to **SQL Editor**
2. Run the following SQL:
```sql
-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;
```
3. Click **Run**

### Get Connection String

1. Go to **Settings** → **Database**
2. Copy the **Connection string** (URI format)
3. It should look like:
   ```
   postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
   ```

---

## 2. Backend API Deployment (Railway)

### Option A: Railway (Recommended)

1. Go to [railway.app](https://railway.app) and create a new project
2. Click **Deploy from GitHub repo**
3. Select this repository
4. Set **Root Directory** to `apps/api`
5. Railway will detect the `Dockerfile` automatically

### Configure Environment Variables

In Railway project settings → **Variables**, add:

| Variable | Value | Notes |
|----------|-------|-------|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` | Link to Supabase (see below) |
| `REDIS_URL` | `${{Redis.REDIS_URL}}` | Add Redis service in Railway |
| `OPENROUTER_API_KEY` | `sk-or-v1-...` | From OpenRouter dashboard |
| `SARVAM_API_KEY` | `...` | From Sarvam AI dashboard |
| `ELEVENLABS_API_KEY` | `...` | From ElevenLabs dashboard |
| `GOOGLE_CLOUD_PROJECT` | `your-project-id` | GCP project ID |
| `GOOGLE_APPLICATION_CREDENTIALS` | `/app/gcp-credentials.json` | See GCP setup below |
| `DEMO_MODE` | `false` | Disable demo mode for production |
| `LOG_LEVEL` | `info` | |

### Connect Supabase to Railway

**Option 1: Railway Managed PostGIS (Easier)**
1. In Railway, click **New Service** → **Database** → **PostgreSQL**
2. Railway provides PostGIS-enabled PostgreSQL
3. Link `DATABASE_URL` to `${{Postgres.DATABASE_URL}}`

**Option 2: External Supabase (Recommended for production)**
1. In Railway Variables, set `DATABASE_URL` to your Supabase connection string
2. Replace `[PASSWORD]` with your actual database password
3. Ensure the URL uses `postgresql+asyncpg://` scheme for async SQLAlchemy

### Add Redis

1. In Railway, click **New Service** → **Database** → **Redis**
2. Link `REDIS_URL` to `${{Redis.REDIS_URL}}`

### Google Cloud Credentials (for Translation)

1. In GCP Console, create a Service Account with **Cloud Translation API** access
2. Download the JSON key file
3. In Railway, go to **Settings** → **Files** → **Add File**
4. Upload the JSON as `gcp-credentials.json`
4. The path `/app/gcp-credentials.json` will be available in the container

### Deploy

1. Railway will auto-deploy on push to main branch
2. Wait for build to complete (~3-5 minutes)
3. Note the generated domain: `https://orca-api.up.railway.app`

---

## 3. Frontend Deployment (Vercel)

### Deploy to Vercel

1. Go to [vercel.com](https://vercel.com) and import the repository
2. Set **Root Directory** to `apps/web`
3. Vercel will detect Next.js automatically

### Configure Environment Variables

In Vercel project settings → **Environment Variables**, add:

| Variable | Value | Environment |
|----------|-------|-------------|
| `NEXT_PUBLIC_API_URL` | `https://orca-api.up.railway.app` | Production, Preview |
| `NEXT_PUBLIC_WS_URL` | `wss://orca-api.up.railway.app` | Production, Preview |

### Deploy

1. Click **Deploy**
2. Wait for build to complete (~2-3 minutes)
3. Note the generated domain: `https://orca.vercel.app`

### Custom Domain (Optional)

1. In Vercel project settings → **Domains**
2. Add your custom domain (e.g., `orca.example.com`)
3. Follow Vercel's DNS configuration instructions

---

## 4. Alternative: Render Deployment

If you prefer Render over Railway:

### Backend on Render

1. Go to [render.com](https://render.com) and create a new **Web Service**
2. Connect GitHub repo, set root to `apps/api`
3. Render will use `render.yaml` for configuration
4. Add a **PostgreSQL** database (PostGIS enabled)
5. Add a **Redis** instance
6. Configure environment variables as in Railway section

### render.yaml is already configured

The `apps/api/render.yaml` defines:
- Web service with Docker
- PostgreSQL database with PostGIS
- Redis instance
- Environment variables linked to services

---

## 5. Running Migrations in Production

### After First Deploy

1. SSH into Railway/Render shell or use their CLI:
```bash
# Railway
railway run python -m alembic -c apps/api/alembic.ini upgrade head

# Render (in shell)
python -m alembic -c apps/api/alembic.ini upgrade head
```

### Or Use CI/CD

Add to your GitHub Actions workflow:
```yaml
- name: Run Migrations
  run: |
    railway run python -m alembic -c apps/api/alembic.ini upgrade head
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

---

## 6. Verify Deployment

### Health Checks

- API: `https://orca-api.up.railway.app/health`
- Web: `https://orca.vercel.app`

### Test Key Endpoints

```bash
# Test chat
curl -X POST https://orca-api.up.railway.app/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me temperature profiles near Mumbai"}'

# Test voice transcription
curl -X POST https://orca-api.up.railway.app/api/v1/voice/transcribe \
  -F "audio=@test.webm" \
  -F "language=ml-IN"

# Test scenarios
curl -X POST https://orca-api.up.railway.app/api/v1/scenarios/create \
  -H "Content-Type: application/json" \
  -d '{"scenario_type": "warming", "variable": "temperature", "region": {"min_lat": 5, "max_lat": 25, "min_lon": 65, "max_lon": 95}, "projection_horizon": "2050"}'
```

---

## 7. Monitoring & Observability

### Railway/Render Metrics

- CPU/Memory usage in dashboard
- Request latency and error rates
- Database connection pool

### Recommended Add-ons

- **Sentry** for error tracking (add `SENTRY_DSN` env var)
- **LogRocket** for frontend session replay
- **PostHog** for product analytics

---

## 8. Cost Optimization

### Development/Staging

- Use Railway/Render free tiers
- Supabase free tier (500MB DB, 2GB bandwidth)
- Vercel hobby tier

### Production Estimates

| Service | Monthly Cost (est.) |
|---------|---------------------|
| Railway Pro + Postgres + Redis | ~$20-50 |
| Supabase Pro | ~$25 |
| Vercel Pro | ~$20 |
| API Keys (OpenRouter, Sarvam, ElevenLabs, Google) | Variable |
| **Total** | **~$65-100+/month** |

---

## 9. Troubleshooting

### Common Issues

**Database Connection Failed**
- Check `DATABASE_URL` format: `postgresql+asyncpg://user:pass@host:5432/db`
- Verify Supabase allows connections from Railway/Render IPs
- Ensure PostGIS extension is enabled

**Voice Transcription Fails**
- Verify Sarvam API key is valid
- Check audio format (webm/opus recommended)
- Ensure file size < 25MB

**CORS Errors**
- Verify `NEXT_PUBLIC_API_URL` matches backend domain
- Check backend CORS middleware allows frontend origin

**Migration Errors**
- Run `alembic current` to check migration state
- For schema conflicts, consider manual migration or `alembic stamp head`

---

## 10. Rollback Procedure

### Railway/Render
1. Go to **Deployments** tab
2. Click **Rollback** on previous successful deployment

### Vercel
1. Go to **Deployments** tab
2. Click **...** on previous deployment → **Promote to Production**

### Database
```bash
# Rollback last migration
alembic downgrade -1
```

---

## Support

- Check logs in Railway/Render/Vercel dashboards
- Review API docs at `/docs` (Swagger UI)
- GitHub Issues for bug reports