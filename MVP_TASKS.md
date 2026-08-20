# FloatChat MVP Tasks

## Phase 0: Audit & Planning ✅
- [x] Repository reuse audit (`docs/reuse-audit.md`)
- [x] Architecture diagram (`docs/architecture.md`)
- [x] API contracts (`docs/api-contract.md`)
- [x] Data dictionary (`docs/data-dictionary.md`)
- [x] Safety policy (`docs/safety.md`)
- [x] Monorepo structure created

## Phase 1: Data Foundation
- [ ] Regional ARGO sample data download script
- [ ] Normalization pipeline (NetCDF → xarray → Parquet)
- [ ] QC filtering implementation
- [ ] Parquet cache generation
- [ ] Dataset validation report
- [ ] Supabase migrations
- [ ] Seed database with sample data

## Phase 2: Deterministic Query Engine
- [ ] `search_profiles` tool
- [ ] `aggregate_timeseries` tool
- [ ] `depth_profile_summary` tool
- [ ] `compare_baseline` tool
- [ ] Evidence record creation
- [ ] CSV export

## Phase 3: Chat Interface
- [ ] Text input UI
- [ ] Structured query planner (LLM + tools)
- [ ] Query executor integration
- [ ] MapLibre float map
- [ ] Recharts depth profile chart
- [ ] Recharts time series chart
- [ ] Evidence card component
- [ ] Query steps accordion
- [ ] Confidence card

## Phase 4: Explainability
- [ ] Numeric verification service
- [ ] Confidence calculation
- [ ] Limitations generation
- [ ] Narrative generation (anomaly)
- [ ] Anomaly storytelling endpoint

## Phase 5: Voice
- [ ] STT provider interface + Malayalam implementation
- [ ] Translation provider interface
- [ ] TTS provider interface + Malayalam implementation
- [ ] Transcript preview UI
- [ ] Clarification flow
- [ ] Voice response playback

## Phase 6: Risk Briefing
- [ ] Route/region input UI
- [ ] Ocean-condition components (waves, wind, currents)
- [ ] Forecast/advisory integration interface
- [ ] Conservative risk engine
- [ ] Official warning disclaimer UI
- [ ] Malayalam risk output

## Phase 7: Scenario Playground
- [ ] Trend fitting service
- [ ] Projection with uncertainty bands
- [ ] Assumption display
- [ ] Scenario narrative generation
- [ ] What-if playground UI

## Phase 8: Demo & Deployment
- [ ] Offline demo mode with cached data
- [ ] Demo manifest (`/data/sample/demo_manifest.json`)
- [ ] Vercel frontend deployment
- [ ] Railway/Render backend deployment
- [ ] Supabase production config
- [ ] GitHub Actions CI
- [ ] Demo recording script
- [ ] SIH presentation screenshots

---

## Immediate Next Steps (Vertical Slice)

### 1. Database Setup
```bash
# Create migration files
apps/api/app/db/migrations/001_initial_schema.sql
apps/api/app/db/migrations/002_indexes.sql
```

### 2. Shared Types Package
```typescript
// packages/shared-types/src/index.ts
export * from './query';
export * from './evidence';
export * from './chat';
```

### 3. Query Contracts Package
```python
# packages/query-contracts/query_schema.py
# Pydantic models for structured queries
```

### 4. Evidence Contracts Package
```python
# packages/evidence-contracts/evidence_schema.py
# Pydantic models for evidence/provenance
```

### 5. Backend Core
```
apps/api/app/main.py
apps/api/app/config.py
apps/api/app/dependencies.py
apps/api/app/schemas/query.py
apps/api/app/schemas/evidence.py
apps/api/app/services/query_planner.py
apps/api/app/services/query_executor.py
apps/api/app/services/verifier.py
apps/api/app/services/confidence.py
apps/api/app/data/argo_client.py
apps/api/app/db/client.py
apps/api/app/db/models.py
apps/api/app/routers/chat.py
apps/api/app/routers/profiles.py
apps/api/requirements.txt
```

### 6. Frontend Core
```
apps/web/package.json
apps/web/tsconfig.json
apps/web/tailwind.config.ts
apps/web/app/page.tsx
apps/web/app/chat/page.tsx
apps/web/components/chat/ChatInterface.tsx
apps/web/components/map/FloatMap.tsx
apps/web/components/charts/DepthProfileChart.tsx
apps/web/components/evidence/EvidenceCard.tsx
apps/web/lib/api-client.ts
apps/web/lib/schemas.ts
```

### 7. Demo Data
```
scripts/generate_sample_cache.py
data/sample/demo_manifest.json
data/cached/argo_sample.parquet
```

### 8. Working Query Test
```
Input: "Show temperature profiles in the Arabian Sea during July 2025"
Expected: Map + Depth Profile Chart + Evidence Card with 12 floats, 47 profiles
```

---

## Dependencies to Install

### Backend (Python)
```
fastapi==0.110.1
uvicorn==0.29.0
pydantic==2.7.1
pydantic-settings==2.3.3
sqlalchemy==2.0.30
asyncpg==0.29.0
supabase==2.3.4
argopy==0.1.8
xarray==2024.5.0
pandas==2.2.2
numpy==1.26.4
scipy==1.13.1
pyarrow==16.1.0
httpx==0.27.0
python-multipart==0.0.9
python-dotenv==1.0.1
structlog==24.1.0
pytest==8.2.1
pytest-asyncio==0.23.3
```

### Frontend (Node)
```
next@15
react@18
react-dom@18
typescript@5
tailwindcss@4
@tanstack/react-query@5
maplibre-gl@4
recharts@2
plotly.js@2
zod@3
lucide-react@0.4
clsx@2
tailwind-merge@2
```

---

## Definition of Done (Vertical Slice)

- [ ] `GET /health` returns 200
- [ ] `POST /api/v1/chat` with text question returns:
  - [ ] Structured query in response
  - [ ] Map with float positions
  - [ ] Depth profile chart
  - [ ] Evidence card with float IDs, profile count, date range, QC filters, confidence
  - [ ] Query steps accordion
- [ ] Offline mode works with cached Parquet
- [ ] No unverified numeric claims in response
- [ ] All charts show units, sample counts, date ranges