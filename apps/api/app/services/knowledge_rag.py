# KnowledgeRagService - hybrid retrieval over the curated knowledge base.
#
# Honest retrieval only:
#   * lexical (FTS ts_rank) always runs on PostgreSQL;
#   * vector search runs ONLY when a real embedding provider is configured and
#     an actual embedding is produced; otherwise the mode is "fts_only" and the
#     response says so (no fake vectors are ever used).
# Reranking is a transparent lexical/boundary merge with a documented query
# token coverage bonus - never a claimed ML model.
#
# Validity-aware retrieval (Phase 3.5): by default only documents that are
# active AND within their [effective_date, expiry_date] window are returned as
# current guidance.  Expired advisories never surface as current guidance.
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.db.models import KnowledgeChunk, KnowledgeDocument

_TOKEN_RE = re.compile(r"[a-z0-9]{3,}")


def tokenize(text: str) -> List[str]:
    return _TOKEN_RE.findall((text or "").lower())


# ------------------------------------------------------------------ embedders
class BaseEmbedder:
    name: str = "base"
    available: bool = False
    dimensions: int = 0

    async def embed(self, text: str) -> Optional[List[float]]:
        raise NotImplementedError

    async def embed_many(self, texts: List[str]) -> List[Optional[List[float]]]:
        return [await self.embed(text) for text in texts]


class NotConfiguredEmbedder(BaseEmbedder):
    name = "not_configured"
    available = False
    dimensions = 1536

    async def embed(self, text: str) -> Optional[List[float]]:
        return None


class OpenAICompatibleEmbedder(BaseEmbedder):
    """Embeddings via an OpenAI-compatible /embeddings endpoint.

    Configured through settings: EMBEDDINGS_API_KEY, EMBEDDINGS_ENDPOINT,
    EMBEDDINGS_MODEL.  When the key/endpoint are absent the embedder reports
    not available and retrieval stays FTS-only.
    """

    def __init__(self, api_key: Optional[str], endpoint: Optional[str],
                 model: str = "text-embedding-3-small", dimensions: int = 1536):
        self._api_key = api_key
        self._endpoint = endpoint
        self._model = model
        self.dimensions = dimensions
        self.name = model
        self.available = bool(api_key and endpoint)

    async def embed(self, text: str) -> Optional[List[float]]:
        if not self.available:
            return None
        import httpx

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self._endpoint,
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={"model": self._model, "input": text},
            )
            response.raise_for_status()
            data = response.json()
        entries = data.get("data") or []
        if not entries:
            return None
        embedding = entries[0].get("embedding")
        return [float(v) for v in embedding] if embedding else None


# ---------------------------------------------------------------------- store
def _validity_filters():
    from sqlalchemy import func, or_

    return (
        KnowledgeDocument.active.is_(True),
        or_(KnowledgeDocument.expiry_date.is_(None),
            KnowledgeDocument.expiry_date > func.now()),
        or_(KnowledgeDocument.effective_date.is_(None),
            KnowledgeDocument.effective_date <= func.now()),
    )


_DOC_FIELDS = (
    "section", "page", "heading", "chunk_hash", "authority", "document_type",
    "publication_date", "effective_date", "expiry_date", "active",
    "version", "source_reference", "language", "tags",
)


class KnowledgeChunkStore:
    """Chunk store abstraction; production impl hits PostgreSQL."""

    async def search_fts(self, query: str, limit: int,
                         validity_only: bool = False) -> List[Dict[str, Any]]:
        """Lexical search ranked by ts_rank.  chunk_id/document rows only."""
        raise NotImplementedError

    async def search_vector(self, vector: List[float],
                            limit: int,
                            validity_only: bool = False) -> List[Dict[str, Any]]:
        """Cosine search in pgvector column (PostgreSQL only)."""
        raise NotImplementedError


def _entry_from_row(row, has_score: bool = True) -> Dict[str, Any]:
    entry = {
        "chunk_id": row[0],
        "document_id": row[1],
        "content": row[2],
        "metadata": row[3],
        "title": row[4],
        "source_url": row[5],
    }
    if has_score:
        entry["score"] = float(row[6])
    for index, key in enumerate(_DOC_FIELDS, start=7 if has_score else 6):
        entry[key] = row[index]
    return entry


class PgChunkStore(KnowledgeChunkStore):
    def __init__(self, session_factory=None):
        from app.db.client import get_session

        self._session_factory = session_factory or get_session

    async def search_fts(self, query: str, limit: int,
                         validity_only: bool = False) -> List[Dict[str, Any]]:
        from sqlalchemy import func, select

        words = tokenize(query)
        rows: List[Dict[str, Any]] = []
        if not words:
            return rows
        try:
            async with self._session_factory() as session:
                if session.bind and session.bind.dialect.name == "postgresql":
                    tsq = func.to_tsquery("english", " & ".join(words))
                    tsvec = func.to_tsvector("english", KnowledgeChunk.content)
                    score = func.ts_rank_cd(tsvec, tsq)
                    stmt = (
                        select(
                            KnowledgeChunk.id,
                            KnowledgeChunk.document_id,
                            KnowledgeChunk.content,
                            KnowledgeChunk.metadata_json,
                            KnowledgeDocument.title,
                            KnowledgeDocument.source_url,
                            score.label("score"),
                            KnowledgeChunk.section,
                            KnowledgeChunk.page,
                            KnowledgeChunk.heading,
                            KnowledgeChunk.chunk_hash,
                            KnowledgeDocument.authority,
                            KnowledgeDocument.document_type,
                            KnowledgeDocument.publication_date,
                            KnowledgeDocument.effective_date,
                            KnowledgeDocument.expiry_date,
                            KnowledgeDocument.active,
                            KnowledgeDocument.version,
                            KnowledgeDocument.source_reference,
                            KnowledgeDocument.language,
                            KnowledgeDocument.tags,
                        )
                        .join(KnowledgeDocument,
                              KnowledgeDocument.id == KnowledgeChunk.document_id)
                        .where(score > 0)
                    )
                    if validity_only:
                        stmt = stmt.where(*_validity_filters())
                    stmt = stmt.order_by(score.desc()).limit(limit)
                    result = await session.execute(stmt)
                else:
                    pattern = "%" + "%".join(words) + "%"
                    stmt = (
                        select(
                            KnowledgeChunk.id,
                            KnowledgeChunk.document_id,
                            KnowledgeChunk.content,
                            KnowledgeChunk.metadata_json,
                            KnowledgeDocument.title,
                            KnowledgeDocument.source_url,
                            KnowledgeChunk.section,
                            KnowledgeChunk.page,
                            KnowledgeChunk.heading,
                            KnowledgeChunk.chunk_hash,
                            KnowledgeDocument.authority,
                            KnowledgeDocument.document_type,
                            KnowledgeDocument.publication_date,
                            KnowledgeDocument.effective_date,
                            KnowledgeDocument.expiry_date,
                            KnowledgeDocument.active,
                            KnowledgeDocument.version,
                            KnowledgeDocument.source_reference,
                            KnowledgeDocument.language,
                            KnowledgeDocument.tags,
                        )
                        .join(KnowledgeDocument,
                              KnowledgeDocument.id == KnowledgeChunk.document_id)
                    )
                    if validity_only:
                        stmt = stmt.where(*_validity_filters())
                    stmt = stmt.where(KnowledgeChunk.content.ilike(pattern)).limit(limit)
                    result = await session.execute(stmt)
                for row in result.all():
                    rows.append(_entry_from_row(
                        row, has_score=session.bind
                        and session.bind.dialect.name == "postgresql"))
        except Exception:  # noqa: BLE001 - retrieval must stay non-fatal
            pass
        return rows

    async def search_vector(self, vector: List[float],
                            limit: int,
                            validity_only: bool = False) -> List[Dict[str, Any]]:
        from sqlalchemy import text

        rows: List[Dict[str, Any]] = []
        try:
            async with self._session_factory() as session:
                if not session.bind or session.bind.dialect.name != "postgresql":
                    return rows
                vec_literal = ",".join(repr(float(v)) for v in vector)
                validity = ""
                if validity_only:
                    validity = (
                        "AND d.active = TRUE "
                        "AND (d.expiry_date IS NULL "
                        "OR d.expiry_date > now()) "
                        "AND (d.effective_date IS NULL "
                        "OR d.effective_date <= now()) "
                    )
                sql = text(
                    "SELECT c.id AS chunk_id, c.document_id, c.content, "
                    "c.metadata_json, d.title, d.source_url, "
                    "1.0 - (c.embedding <=> :qvec) AS score, "
                    "c.section, c.page, c.heading, c.chunk_hash, "
                    "d.authority, d.document_type, d.publication_date, "
                    "d.effective_date, d.expiry_date, d.active, d.version, "
                    "d.source_reference, d.language, d.tags "
                    "FROM knowledge_chunks c "
                    "JOIN knowledge_documents d ON d.id = c.document_id "
                    "WHERE c.embedding IS NOT NULL "
                    f"{validity}"
                    "ORDER BY 1.0 - (c.embedding <=> :qvec) DESC "
                    "LIMIT :lim")
                result = await session.execute(
                    sql, {"qvec": f"[{vec_literal}]", "lim": limit})
                for row in result.all():
                    rows.append({
                        "chunk_id": row.chunk_id,
                        "document_id": row.document_id,
                        "content": row.content,
                        "metadata": row.metadata_json,
                        "title": row.title,
                        "source_url": row.source_url,
                        "score": float(row.score),
                        "section": row.section,
                        "page": row.page,
                        "heading": row.heading,
                        "chunk_hash": row.chunk_hash,
                        "authority": row.authority,
                        "document_type": row.document_type,
                        "publication_date": row.publication_date,
                        "effective_date": row.effective_date,
                        "expiry_date": row.expiry_date,
                        "active": row.active,
                        "version": row.version,
                        "source_reference": row.source_reference,
                        "language": row.language,
                        "tags": row.tags,
                    })
        except Exception:  # noqa: BLE001
            pass
        return rows


def document_validity(entry: Dict[str, Any],
                      now: Optional[datetime] = None) -> str:
    now = now or datetime.now(timezone.utc)

    def _parse(value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        try:
            parsed = datetime.fromisoformat(value)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            return None

    effective = _parse(entry.get("effective_date"))
    expiry = _parse(entry.get("expiry_date"))
    if effective is not None and now < effective:
        return "not_yet_effective"
    if expiry is not None and now > expiry:
        return "expired"
    return "active"


@dataclass
class RetrievalResult:
    query: str
    mode: str  # hybrid | fts_only
    note: str
    chunks: List[Dict[str, Any]] = field(default_factory=list)
    citations: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "mode": self.mode,
            "note": self.note,
            "chunks": self.chunks,
            "citations": self.citations,
        }


class KnowledgeRagService:
    def __init__(self, store: Optional[KnowledgeChunkStore] = None,
                 embedder: Optional[BaseEmbedder] = None):
        self.store = store or PgChunkStore()
        self.embedder = embedder or self._default_embedder()

    @staticmethod
    def _default_embedder() -> BaseEmbedder:
        embedder = NotConfiguredEmbedder()
        try:
            from app.config import get_settings

            settings = get_settings()
            embedder = OpenAICompatibleEmbedder(
                api_key=settings.embeddings_api_key,
                endpoint=settings.embeddings_endpoint,
                model=settings.embeddings_model,
                dimensions=settings.embeddings_dimensions,
            )
        except Exception:  # noqa: BLE001 - settings access must not break RAG
            pass
        return embedder

    async def retrieve(self, query: str, limit: int = 5,
                       validity_only: bool = True,
                       now: Optional[datetime] = None) -> RetrievalResult:
        tokens = tokenize(query)
        if not tokens:
            return RetrievalResult(query=query, mode="fts_only",
                                   note="query empty after tokenization")

        fts = await self.store.search_fts(query, limit=limit * 4,
                                          validity_only=validity_only)
        vectors: List[Dict[str, Any]] = []
        hybrid = False
        note = "lexical FTS retrieval (ts_rank); no embedding provider"
        if self.embedder.available:
            vector = await self.embedder.embed(query)
            if vector:
                vectors = await self.store.search_vector(
                    vector, limit=limit * 4, validity_only=validity_only)
                if vectors:
                    hybrid = True
                    note = ("hybrid retrieval: pgvector cosine + PostgreSQL FTS "
                            f"with {self.embedder.name}")
                else:
                    note = ("embedding produced but no vector matches; lexical "
                            "FTS results used")
        if validity_only:
            note += "; expired/inactive documents filtered out"

        merged = self._rerank(fts, vectors, tokens)
        chunks = []
        for rank, candidate in enumerate(merged[:limit], start=1):
            chunks.append(self._chunk_view(candidate, rank, now))

        citations = [
            {
                "chunk_id": c["chunk_id"],
                "title": c["title"],
                "source_url": c.get("source_url"),
                "excerpt": c["content"][:220],
                "score": c["score"],
                "rank": c["rank"],
                "document_type": c.get("document_type"),
                "publication_date": c.get("publication_date"),
                "expiry_date": c.get("expiry_date") if
                c.get("document_validity") == "active" else c.get("expiry_date"),
            }
            for c in chunks
        ]
        return RetrievalResult(
            query=query,
            mode="hybrid" if hybrid else "fts_only",
            note=note,
            chunks=chunks,
            citations=citations,
        )

    @staticmethod
    def _chunk_view(candidate: Dict[str, Any], rank: int,
                    now: Optional[datetime]) -> Dict[str, Any]:
        return {
            "chunk_id": candidate["chunk_id"],
            "document_id": candidate.get("document_id"),
            "content": candidate["content"],
            "section": candidate.get("section"),
            "page": candidate.get("page"),
            "heading": candidate.get("heading"),
            "chunk_hash": candidate.get("chunk_hash"),
            "metadata": candidate.get("metadata") or {},
            "title": candidate.get("title"),
            "source_url": candidate.get("source_url"),
            "authority": candidate.get("authority"),
            "document_type": candidate.get("document_type"),
            "publication_date": candidate.get("publication_date"),
            "effective_date": candidate.get("effective_date"),
            "expiry_date": candidate.get("expiry_date"),
            "language": candidate.get("language"),
            "version": candidate.get("version"),
            "source_reference": candidate.get("source_reference"),
            "retrieval_source": candidate.get("retrieval_source"),
            "rank": rank,
            "score": candidate["combined_score"],
            "combined_score": candidate["combined_score"],
            "fts_score": candidate.get("fts_score"),
            "vector_score": candidate.get("vector_score"),
            "document_validity": document_validity(candidate, now),
            "document_active": candidate.get("active", True),
        }

    def _rerank(self, fts: List[Dict[str, Any]],
                vectors: List[Dict[str, Any]], tokens: List[str],
                ) -> List[Dict[str, Any]]:
        """Transparent merge: FTS ts_rank + (real) vector cosine + query-token
        coverage bonus.  Not a learned reranker - documented heuristic."""
        by_id: Dict[Any, Dict[str, Any]] = {}
        for entry in fts:
            entry = dict(entry)
            entry.setdefault("fts_score", float(entry.get("score") or 0.0))
            entry.setdefault("vector_score", None)
            entry["retrieval_source"] = "fts"
            by_id[entry["chunk_id"]] = entry
        for entry in vectors:
            entry = dict(entry)
            vector_score = float(entry.get("score") or 0.0)
            existing = by_id.get(entry["chunk_id"])
            if existing is None:
                entry.setdefault("fts_score", 0.0)
                entry["vector_score"] = vector_score
                entry["retrieval_source"] = "vector"
                by_id[entry["chunk_id"]] = entry
            else:
                existing["vector_score"] = vector_score
                existing["retrieval_source"] = "hybrid"

        ordered = []
        for chunk_id, entry in by_id.items():
            fts_score = entry["fts_score"]
            vector_score = entry.get("vector_score")
            content = (entry.get("content") or "").lower()
            coverage = sum(1 for t in tokens if t in content) / len(tokens)
            if vector_score is not None:
                base = 0.7 * fts_score + 0.3 * vector_score
            else:
                base = fts_score
            entry["combined_score"] = round(base + 0.10 * coverage, 4)
            ordered.append(entry)
        ordered.sort(key=lambda e: e["combined_score"], reverse=True)
        return ordered


def get_knowledge_rag_service() -> KnowledgeRagService:
    global _knowledge_rag
    if _knowledge_rag is None:
        _knowledge_rag = KnowledgeRagService()
    return _knowledge_rag


_knowledge_rag: Optional[KnowledgeRagService] = None