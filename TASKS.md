# ORCA - Remaining Implementation Tasks

This file tracks remaining work for production readiness and enhancements.

---

## 🔴 Critical (Pre-Launch)

### [ ] GitHub Actions CI/CD Pipeline
- [ ] Create `.github/workflows/ci.yml` - Run tests, lint, typecheck on PR
- [ ] Create `.github/workflows/deploy-api.yml` - Deploy to Railway on main push
- [ ] Create `.github/workflows/deploy-web.yml` - Deploy to Vercel on main push
- [ ] Add migration step to API deploy workflow
- [ ] Configure required secrets (DATABASE_URL, API keys, etc.)

### [ ] Production Environment Setup
- [ ] Create Supabase project with PostGIS enabled
- [ ] Create Railway project - link Supabase DB + Redis
- [ ] Create Vercel project - link GitHub repo
- [ ] Configure all environment variables in Railway/Vercel
- [ ] Run initial migration on production DB
- [ ] Verify health endpoints: `/health`, `/api/v1/chat`

### [ ] Security Hardening
- [ ] Add rate limiting to API (slowapi or similar)
- [ ] Configure CORS origins for production domains only
- [ ] Add API key authentication for sensitive endpoints
- [ ] Set up Sentry for error tracking (both API and Web)
- [ ] Add CSP headers
- [ ] Rotate API keys used in development

---

## 🟡 High Priority (Post-Launch)

### [ ] Monitoring & Observability
- [ ] Add structured logging (structlog) to API
- [ ] Add OpenTelemetry tracing
- [ ] Set up Grafana dashboards (Railway metrics + custom)
- [ ] Configure alerting for:
  - API error rate > 5%
  - Database connection pool exhaustion
  - High latency (>2s p95)
  - Failed voice transcriptions

### [ ] Performance Optimization
- [ ] Add Redis caching for:
  - ARGO query results (TTL: 1 hour)
  - Marine condition lookups (TTL: 15 min)
  - Scenario projections (TTL: 30 min)
- [ ] Implement connection pooling (already in SQLAlchemy)
- [ ] Add database indexes for common query patterns
- [ ] Optimize Next.js bundle size
- [ ] Enable ISR for static pages

### [ ] Voice Pipeline Enhancements
- [ ] Add VAD (Voice Activity Detection) client-side
- [ ] Implement streaming transcription for long audio
- [ ] Add TTS playback in VoiceRecorder component
- [ ] Support audio format conversion (webm → wav/mp3)
- [ ] Add language auto-detection

---

## 🟢 Medium Priority (Enhancements)

### [ ] Data Pipeline Improvements
- [ ] Automated ARGO data ingestion (cron job / GitHub Action)
- [ ] Add more data sources (CMEMS, NOAA, INCOIS)
- [ ] Implement data versioning with DVC or similar
- [ ] Add data quality monitoring/alerts

### [ ] Feature Enhancements
- [ ] WebSocket support for real-time updates
- [ ] User authentication (Clerk/Auth0/Supabase Auth)
- [ ] Saved queries / favorites
- [ ] Export to CSV/GeoJSON/NetCDF
- [ ] Mobile-responsive map improvements
- [ ] Offline mode with service worker

### [ ] Internationalization
- [ ] Add more Indian coastal languages (10 currently)
- [ ] RTL language support
- [ ] Date/number formatting per locale
- [ ] Marine terminology glossary per language

---

## 🔵 Low Priority (Nice to Have)

### [ ] Developer Experience
- [ ] Add Storybook for UI components
- [ ] Create component library documentation
- [ ] Add E2E tests with Playwright
- [ ] Set up preview deployments for PRs

### [ ] Advanced Features
- [ ] ML-based anomaly detection (beyond statistical)
- [ ] Route optimization with genetic algorithms
- [ ] Collaborative scenario planning
- [ ] Integration with AIS vessel tracking
- [ ] Weather routing API integration

### [ ] Documentation
- [ ] API reference (auto-generated from OpenAPI)
- [ ] Architecture decision records (ADRs)
- [ ] Runbook for incident response
- [ ] Contributor guide

---

## 📋 Completed (Reference)

| Task | Status | Date |
|------|--------|------|
| Fix Alembic migrations (SQLite + PG) | ✅ Done | 2026-08-29 |
| Initial schema migration | ✅ Done | 2026-08-29 |
| Dockerfile (API) | ✅ Done | 2026-08-29 |
| Dockerfile (Web) | ✅ Done | 2026-08-29 |
| docker-compose.yml | ✅ Done | 2026-08-29 |
| vercel.json | ✅ Done | 2026-08-29 |
| railway.json | ✅ Done | 2026-08-29 |
| render.yaml | ✅ Done | 2026-08-29 |
| DEPLOYMENT.md | ✅ Done | 2026-08-29 |
| VoiceRecorder.tsx backend integration | ✅ Done | 2026-08-29 |
| All 24 tests passing | ✅ Done | 2026-08-29 |
| Offline demo 10/10 queries | ✅ Done | 2026-08-29 |
| Push to GitHub | ✅ Done | 2026-08-29 |

---

## 🚀 Quick Start for Next Session

```bash
# 1. Check current status
git status

# 2. Create GitHub Actions workflows
mkdir -p .github/workflows
# ... create ci.yml, deploy-api.yml, deploy-web.yml

# 3. Set up production infrastructure
# Follow DEPLOYMENT.md

# 4. Run migrations on production
railway run python -m alembic -c apps/api/alembic.ini upgrade head

# 5. Verify deployment
curl https://orca-api.up.railway.app/health
curl https://orca.vercel.app
```