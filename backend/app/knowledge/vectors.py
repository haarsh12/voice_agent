"""Server-side Qdrant adapter and Vertex embedding provider."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence
from urllib.parse import urlsplit

import httpx

from app.config.settings import MissingConfigurationError, Settings
from app.services.gemini import create_gemini_client


class EmbeddingError(RuntimeError):
    """Raised when trusted-text embeddings cannot be created."""


class VectorStoreError(RuntimeError):
    """Raised without exposing Qdrant URLs, credentials, or response content."""


class EmbeddingProvider(Protocol):
    """Provider boundary allows deterministic test embeddings and future models."""

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed text in the same order supplied."""


@dataclass(frozen=True)
class VectorRecord:
    """One Qdrant point for a semantic chunk."""

    point_id: str
    vector: list[float]
    payload: dict[str, object]


@dataclass(frozen=True)
class VectorHit:
    """A score-only result; provenance is resolved from PostgreSQL afterwards."""

    point_id: str
    score: float


class VertexEmbeddingProvider:
    """Uses the same server-only Vertex authentication factory as Gemini chat."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            client = create_gemini_client(self.settings)
            response = client.models.embed_content(
                model=self.settings.knowledge_embedding_model,
                contents=list(texts),
            )
            embeddings = getattr(response, "embeddings", None) or []
            vectors = [list(getattr(embedding, "values", [])) for embedding in embeddings]
        except MissingConfigurationError:
            raise
        except Exception as error:
            raise EmbeddingError("embedding_generation_failed") from error
        if len(vectors) != len(texts) or any(not vector for vector in vectors):
            raise EmbeddingError("embedding_response_invalid")
        return vectors


class QdrantVectorStore:
    """Small HTTP client that keeps Qdrant credentials and queries backend-only."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._base_url = settings.qdrant_url.rstrip("/")

    @property
    def configured(self) -> bool:
        return bool(self._base_url)

    def ensure_collection(self) -> None:
        """Create the collection exactly once, without changing an existing index."""

        self._require_safe_endpoint()
        collection = self.settings.qdrant_collection
        response = self._request("GET", f"/collections/{collection}", expected={200, 404})
        if response.status_code == 200:
            return
        self._request(
            "PUT",
            f"/collections/{collection}",
            json={
                "vectors": {
                    "size": self.settings.knowledge_embedding_dimensions,
                    "distance": "Cosine",
                }
            },
            expected={200},
        )

    def upsert(self, records: Sequence[VectorRecord]) -> None:
        if not records:
            return
        self._require_safe_endpoint()
        self._request(
            "PUT",
            f"/collections/{self.settings.qdrant_collection}/points?wait=true",
            json={
                "points": [
                    {"id": record.point_id, "vector": record.vector, "payload": record.payload}
                    for record in records
                ]
            },
            expected={200},
        )

    def search(self, vector: list[float], *, limit: int, filters: dict[str, str] | None = None) -> list[VectorHit]:
        """Use Qdrant payload filters before relational freshness validation."""

        self._require_safe_endpoint()
        must = [{"key": key, "match": {"value": value}} for key, value in (filters or {}).items()]
        response = self._request(
            "POST",
            f"/collections/{self.settings.qdrant_collection}/points/query",
            json={
                "query": vector,
                "limit": limit,
                "with_payload": False,
                "filter": {"must": must} if must else None,
            },
            expected={200},
        )
        try:
            points = response.json()["result"]["points"]
            return [VectorHit(point_id=str(point["id"]), score=float(point["score"])) for point in points]
        except (KeyError, TypeError, ValueError) as error:
            raise VectorStoreError("qdrant_response_invalid") from error

    def set_document_status(self, point_ids: Sequence[str], status: str) -> None:
        """Keep Qdrant's pre-filter payload aligned when a version is superseded."""

        if not point_ids:
            return
        self._require_safe_endpoint()
        self._request(
            "POST",
            f"/collections/{self.settings.qdrant_collection}/points/payload?wait=true",
            json={"payload": {"document_status": status}, "points": list(point_ids)},
            expected={200},
        )

    def _request(self, method: str, path: str, *, expected: set[int], json: dict[str, object] | None = None) -> httpx.Response:
        headers: dict[str, str] = {}
        if self.settings.qdrant_api_key and self.settings.qdrant_api_key.get_secret_value().strip():
            headers["api-key"] = self.settings.qdrant_api_key.get_secret_value()
        try:
            with httpx.Client(timeout=self.settings.knowledge_fetch_timeout_seconds) as client:
                response = client.request(method, f"{self._base_url}{path}", headers=headers, json=json)
        except httpx.HTTPError as error:
            raise VectorStoreError("qdrant_request_failed") from error
        if response.status_code not in expected:
            raise VectorStoreError("qdrant_request_rejected")
        return response

    def _require_safe_endpoint(self) -> None:
        if not self.configured:
            raise VectorStoreError("qdrant_not_configured")
        try:
            parsed = urlsplit(self._base_url)
        except ValueError as error:
            raise VectorStoreError("qdrant_url_invalid") from error
        if (
            parsed.scheme not in {"https", "http"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            raise VectorStoreError("qdrant_url_invalid")
        if self.settings.is_production and parsed.scheme != "https":
            raise VectorStoreError("qdrant_url_requires_https")
