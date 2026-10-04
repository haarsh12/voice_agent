import asyncio
import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import hashlib

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

# Add backend dir to pythonpath
backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from app.config.settings import get_settings
from app.auth.session import get_session_factory
from app.knowledge.models import (
    KnowledgeSource,
    KnowledgeDocument,
    KnowledgeDocumentVersion,
    KnowledgeChunk,
    SchemeRecord,
    SchemeVersion,
    SchemeSource,
)
from app.knowledge.vectors import QdrantVectorStore, VertexEmbeddingProvider, VectorRecord
from app.schemes.contracts import SchemeStatus, SchemeVerificationStatus

logger = logging.getLogger(__name__)

def hash_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

def normalize_name(name: str) -> str:
    # Match the knowledge system's normalization
    s = str(name).casefold()
    s = re.sub(r"[^\w\s-]", "", s)
    return re.sub(r"\s+", " ", s).strip()

async def ensure_source(session: AsyncSession) -> tuple[KnowledgeSource, KnowledgeDocument, KnowledgeDocumentVersion]:
    source_key = "static_catalogue"
    now = datetime.now(timezone.utc)
    
    source = await session.get(KnowledgeSource, source_key)
    if not source:
        source = KnowledgeSource(
            key=source_key,
            name="Sahayak Static Catalogue",
            category="Catalogue",
            authority_level=1,
            geographic_scope="NATIONAL",
            check_interval_hours=0,
            approved_domains=[],
            entry_urls=["internal://catalogue"],
            validation_status="APPROVED",
            created_at=now,
            updated_at=now
        )
        session.add(source)
        await session.flush()

    doc_id = str(uuid4())
    doc = await session.scalar(select(KnowledgeDocument).where(KnowledgeDocument.source_key == source_key).limit(1))
    if not doc:
        doc = KnowledgeDocument(
            id=doc_id,
            source_key=source_key,
            canonical_url="internal://catalogue",
            title="Static Catalogue Schemes",
            created_at=now,
            updated_at=now
        )
        session.add(doc)
        await session.flush()
    else:
        doc_id = doc.id

    ver_id = str(uuid4())
    ver = await session.scalar(select(KnowledgeDocumentVersion).where(KnowledgeDocumentVersion.document_id == doc_id).order_by(KnowledgeDocumentVersion.version_number.desc()).limit(1))
    if not ver:
        ver = KnowledgeDocumentVersion(
            id=ver_id,
            document_id=doc_id,
            version_number=1,
            source_url="internal://catalogue",
            title="Static Catalogue Schemes",
            content_hash="static",
            status="CURRENT",
            first_retrieved_at=now,
            last_checked_at=now,
            created_at=now
        )
        session.add(ver)
        await session.flush()

    return source, doc, ver

async def seed_schemes():
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    
    # 1. Load data
    json_path = backend_dir.parent / "frontend" / "schemes.json"
    if not json_path.exists():
        logger.error(f"Cannot find {json_path}")
        return
        
    with open(json_path, "r", encoding="utf-8") as f:
        schemes_data = json.load(f)
        
    logger.info(f"Loaded {len(schemes_data)} schemes from catalogue")
    
    # 2. Setup Vector Store
    vector_store = QdrantVectorStore(settings)
    vector_store.ensure_collection()
    embedder = VertexEmbeddingProvider(settings)

    # 3. DB Session
    session_factory = get_session_factory()
    if not session_factory:
        logger.error("DB Engine not initialized")
        return
        
    async with session_factory() as session:
        source, doc, doc_version = await ensure_source(session)
        now = datetime.now(timezone.utc)
        
        all_vector_records = []
        
        for idx, item in enumerate(schemes_data):
            # Upsert SchemeRecord
            norm_name = normalize_name(item["official_name"])
            record = await session.scalar(select(SchemeRecord).where(SchemeRecord.slug == item["slug"]))
            if not record:
                record = SchemeRecord(
                    id=str(uuid4()),
                    slug=item["slug"],
                    normalized_name=norm_name,
                    official_name=item["official_name"],
                    short_name=item.get("short_name"),
                    scheme_type=item["scheme_type"],
                    category=item["category"],
                    ministry=item.get("ministry"),
                    implementing_authority=item.get("implementing_authority"),
                    geographic_scope=item.get("geographic_scope", "NATIONAL"),
                    applicable_states=item.get("applicable_states", []),
                    beneficiary_categories=item.get("relevant_user_types", []),
                    relevant_user_types=item.get("relevant_user_types", []),
                    status=SchemeStatus.ACTIVE.value,
                    verification_status=SchemeVerificationStatus.APPROVED.value,
                    first_discovered_at=now,
                    last_checked_at=now,
                    created_at=now
                )
                session.add(record)
                await session.flush()
            else:
                # Update existing
                record.normalized_name = norm_name
                record.official_name = item["official_name"]
                record.short_name = item.get("short_name")
                record.scheme_type = item["scheme_type"]
                record.category = item["category"]
                record.ministry = item.get("ministry")
                record.geographic_scope = item.get("geographic_scope", "NATIONAL")
                record.applicable_states = item.get("applicable_states", [])
                record.beneficiary_categories = item.get("relevant_user_types", [])
                record.relevant_user_types = item.get("relevant_user_types", [])
                record.status = SchemeStatus.ACTIVE.value
                record.verification_status = SchemeVerificationStatus.APPROVED.value
                record.last_checked_at = now
                await session.flush()
            
            # Form data dict
            data = {
                "description": item.get("description"),
                "objective": item.get("objective"),
                "benefits": item.get("benefits"),
                "eligibility": item.get("eligibility"),
                "application_process": item.get("application_process"),
                "required_documents": item.get("required_documents"),
                "subcategory": item.get("subcategory"),
            }
            
            # Content Hash
            content_str = json.dumps(data, sort_keys=True)
            c_hash = hash_content(content_str)
            
            # Check if current version matches
            current_ver = await session.scalar(
                select(SchemeVersion)
                .where(SchemeVersion.scheme_id == record.id, SchemeVersion.is_current.is_(True))
                .order_by(SchemeVersion.version_number.desc())
                .limit(1)
            )
            
            if not current_ver or current_ver.content_hash != c_hash:
                if current_ver:
                    current_ver.is_current = False
                    current_ver.status = SchemeStatus.SUPERSEDED.value
                
                next_number = (current_ver.version_number if current_ver else 0) + 1
                current_ver = SchemeVersion(
                    id=str(uuid4()),
                    scheme_id=record.id,
                    version_number=next_number,
                    content_hash=c_hash,
                    status=SchemeStatus.ACTIVE.value,
                    verification_status=SchemeVerificationStatus.APPROVED.value,
                    data=data,
                    evidence_summary="Sourced directly from Sahayak AI Static Catalogue.",
                    first_retrieved_at=now,
                    last_checked_at=now,
                    last_changed_at=now,
                    is_current=True,
                    created_at=now
                )
                session.add(current_ver)
                await session.flush()
                record.current_version_number = next_number
            
            # Generate Embeddings Text
            chunks_text = [
                f"Scheme Overview: {item['official_name']} ({item.get('short_name','')})\nType: {item['scheme_type']}\nCategory: {item['category']}\nMinistry: {item.get('ministry','')}\nDescription: {item.get('description','')}\nObjective: {item.get('objective','')}",
                f"Scheme Eligibility & Benefits: {item['official_name']}\nBeneficiaries: {', '.join(item.get('beneficiary_tags',[]))}\nEligibility: {item.get('eligibility','')}\nBenefits: {item.get('benefits','')}",
                f"Scheme Application: {item['official_name']}\nHow to apply: {item.get('application_process','')}\nDocuments needed: {item.get('required_documents','')}"
            ]
            
            vectors = embedder.embed(chunks_text)
            
            # Create KnowledgeChunk and VectorRecord
            for i, (text, vector) in enumerate(zip(chunks_text, vectors)):
                chunk_id = str(uuid4())
                point_id = str(uuid4())
                kc = KnowledgeChunk(
                    id=chunk_id,
                    document_version_id=doc_version.id,
                    ordinal=(idx * 10) + i,
                    content=text,
                    content_hash=hash_content(text),
                    vector_point_id=point_id,
                    scheme_key=record.id,
                    created_at=now
                )
                session.add(kc)
                await session.flush()
                
                # Link source
                ss = SchemeSource(
                    id=str(uuid4()),
                    scheme_version_id=current_ver.id,
                    source_key=source.key,
                    document_version_id=doc_version.id,
                    chunk_id=chunk_id,
                    source_name=source.name,
                    document_title=doc.title,
                    source_url=item.get("official_url", "internal://catalogue"),
                    created_at=now
                )
                session.add(ss)
                
                # Prepare Vector
                all_vector_records.append(VectorRecord(
                    point_id=point_id,
                    vector=vector,
                    payload={
                        "document_status": doc_version.status,
                        "source_key": source.key,
                        "scheme_key": record.id,
                        "chunk_type": "catalogue",
                        "content": text
                    }
                ))

        await session.commit()
        
        # Batch insert into Qdrant
        if all_vector_records:
            logger.info(f"Upserting {len(all_vector_records)} vectors to Qdrant")
            # Batch in 50 chunks
            for i in range(0, len(all_vector_records), 50):
                vector_store.upsert(all_vector_records[i:i+50])
            logger.info("Qdrant seeding complete!")
        
    logger.info("Database seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed_schemes())
