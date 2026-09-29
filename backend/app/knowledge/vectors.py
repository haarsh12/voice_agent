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
            vectors: list[list[float]] = []
            batch_size = self.settings.knowledge_embedding_batch_size
            for start in range(0, len(texts), batch_size):
                vectors.extend(self._embed_batch(client, list(texts[start : start + batch_size])))
        except MissingConfigurationError:
            raise
        except Exception as error:
            raise EmbeddingError("embedding_generation_failed") from error
        if len(vectors) != len(texts) or any(not vector for vector in vectors):
            raise EmbeddingError("embedding_response_invalid")
        if any(len(vector) != self.settings.knowledge_embedding_dimensions for vector in vectors):
            raise EmbeddingError("embedding_dimension_mismatch")
        return vectors

    def _embed_batch(self, client: object, texts: list[str]) -> list[list[float]]:
        """Embed a bounded batch, bisecting only provider-rejected batches.

        Government PDFs occasionally yield dense, encoding-heavy text. A
        provider can reject an otherwise valid multi-item request because of a
        request-level limit. Retrying recursively preserves order and lets a
        single bad chunk fail closed without discarding an entire document.
        """

        try:
            response = client.models.embed_content(  # type: ignore[attr-defined]
                model=self.settings.knowledge_embedding_model,
                contents=texts,
            )
            embeddings = getattr(response, "embeddings", None) or []
            vectors = [list(getattr(embedding, "values", [])) for embedding in embeddings]
            if len(vectors) != len(texts) or any(not vector for vector in vectors):
                raise EmbeddingError("embedding_response_invalid")
            return vectors
        except EmbeddingError:
            raise
        except Exception as error:
            if len(texts) == 1:
                raise EmbeddingError("embedding_generation_failed") from error
            midpoint = len(texts) // 2
            return self._embed_batch(client, texts[:midpoint]) + self._embed_batch(client, texts[midpoint:])


class QdrantVectorStore:
    """Small HTTP client that keeps Qdrant credentials and queries backend-only."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._base_url = settings.qdrant_url.rstrip("/")
        self._collection_ready = False

    @property
    def configured(self) -> bool:
        return bool(self._base_url)

    def ensure_collection(self) -> None:
        """Create and validate the vector and payload contracts exactly once."""

        if self._collection_ready:
            return
        self._require_safe_endpoint()
        collection = self.settings.qdrant_collection
        response = self._request("GET", f"/collections/{collection}", expected={200, 404})
        if response.status_code == 200:
            self._validate_existing_collection(response)
        else:
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
        self._ensure_payload_indexes()
        self._collection_ready = True

    def _ensure_payload_indexes(self) -> None:
        """Create the keyword indexes required by server-side Qdrant filters."""

        for field_name in (
            "document_status",
            "source_key",
            "state",
            "district",
            "language",
            "scheme_key",
        ):
            self._request(
                "PUT",
                f"/collections/{self.settings.qdrant_collection}/index?wait=true",
                json={"field_name": field_name, "field_schema": "keyword"},
                expected={200},
            )

    def _validate_existing_collection(self, response: httpx.Response) -> None:
        """Refuse a collection whose vector contract differs from this service."""

        try:
            vectors = response.json()["result"]["config"]["params"]["vectors"]
            if not isinstance(vectors, dict):
                raise ValueError("unnamed vectors missing")
            size = int(vectors["size"])
            distance = str(vectors["distance"])
        except (KeyError, TypeError, ValueError) as error:
            raise VectorStoreError("qdrant_collection_config_invalid") from error
        if size != self.settings.knowledge_embedding_dimensions:
            raise VectorStoreError("qdrant_collection_dimension_mismatch")
        if distance.casefold() != "cosine":
            raise VectorStoreError("qdrant_collection_distance_mismatch")

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
            # Qdrant 1.10 returned ``result.points`` while current Cloud
            # releases return the points array directly in ``result``. Accept
            # only these two documented envelopes, never arbitrary payloads.
            result = response.json()["result"]
            points = result["points"] if isinstance(result, dict) else result
            if not isinstance(points, list):
                raise TypeError("query result is not a point list")
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
            # The status code is safe operational telemetry; response bodies
            # may contain provider or proxy details and stay private.
            raise VectorStoreError(f"qdrant_request_rejected_{response.status_code}")
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
