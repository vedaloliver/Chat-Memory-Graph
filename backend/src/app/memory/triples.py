# src/app/core/memory/triples.py

from datetime import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session

from src.app.core.logging_utils import get_logger
from src.app.models.database_models import (
    TripleModel,
    TripleSessionLinkModel,
    TripleChunkLinkModel,
    SessionSummaryModel,
    MemoryChunkModel,
)
from .entities import make_entity_key, EntityModel  # type: ignore[attr-defined]

logger = get_logger(__name__)


def make_triple_key(
    subject_id: str,
    relation_type: str,
    object_id: Optional[str],
) -> str:
    """
    Canonical key for triple dedup:
        subject_id | lower(relation_type) | object_id_or_empty
    """
    rel_norm = (relation_type or "").strip().lower()
    obj_part = object_id or ""
    return f"{subject_id}|{rel_norm}|{obj_part}"


def ensure_triple_session_link(
    db: Session,
    triple: TripleModel,
    session_summary: SessionSummaryModel,
) -> None:
    existing = (
        db.query(TripleSessionLinkModel)
        .filter(
            TripleSessionLinkModel.triple_id == triple.id,
            TripleSessionLinkModel.session_summary_id == session_summary.id,
        )
        .first()
    )
    if existing:
        return

    link = TripleSessionLinkModel(
        triple_id=triple.id,
        session_summary_id=session_summary.id,
    )
    db.add(link)
    db.flush()


def ensure_triple_chunk_link(
    db: Session,
    triple: TripleModel,
    chunk: MemoryChunkModel,
) -> None:
    existing = (
        db.query(TripleChunkLinkModel)
        .filter(
            TripleChunkLinkModel.triple_id == triple.id,
            TripleChunkLinkModel.chunk_id == chunk.id,
        )
        .first()
    )
    if existing:
        return

    link = TripleChunkLinkModel(
        triple_id=triple.id,
        chunk_id=chunk.id,
    )
    db.add(link)
    db.flush()


def upsert_triples_and_links(
    db: Session,
    triples_data: List[Dict[str, Any]],
    entity_cache: Dict[str, EntityModel],
    session_summary: SessionSummaryModel,
    chunk: MemoryChunkModel,
) -> None:
    """
    Upsert TripleModel rows and link them to the session + chunk.

    Dedup heuristic:
      key = subject_entity_id | lower(relation_type) | object_entity_id_or_empty
    """
    if not triples_data:
        return

    # Map canonical entity key -> EntityModel.id
    entity_id_by_key: Dict[str, str] = {
        make_entity_key(ent.canonical_name, ent.entity_type): ent.id
        for ent in entity_cache.values()
    }

    # Preload existing triples for relevant subjects to keep DB load reasonable.
    subject_ids = set()
    for t in triples_data:
        subj_name = (t.get("subject") or "").strip()
        subj_type = t.get("subject_type")
        if not subj_name:
            continue
        key = make_entity_key(subj_name, subj_type)
        ent_id = entity_id_by_key.get(key)
        if ent_id:
            subject_ids.add(ent_id)

    existing_triples: List[TripleModel] = []
    if subject_ids:
        existing_triples = (
            db.query(TripleModel)
            .filter(TripleModel.subject_entity_id.in_(list(subject_ids)))
            .all()
        )

    existing_by_key: Dict[str, TripleModel] = {}
    for triple in existing_triples:
        triple_key = make_triple_key(
            triple.subject_entity_id,
            triple.relation_type,
            triple.object_entity_id,
        )
        existing_by_key[triple_key] = triple

    new_triples = 0
    reused_triples = 0

    for t in triples_data:
        subj_name = (t.get("subject") or "").strip()
        subj_type = t.get("subject_type")
        obj_name = (t.get("object") or "").strip() or None
        obj_type = t.get("object_type")
        relation_type = (t.get("relation_type") or "").strip()
        relation_text = t.get("relation_text")
        importance = t.get("importance")
        is_state = t.get("is_state")
        confidence = t.get("confidence")

        if not subj_name or not relation_type:
            # Not enough info to make a triple
            continue

        # Resolve subject entity
        subj_key = make_entity_key(subj_name, subj_type)
        subj_id = entity_id_by_key.get(subj_key)
        if not subj_id:
            # If subject wasn't in entities list, skip (MVP simplicity)
            continue

        # Resolve object entity if present
        obj_id: Optional[str] = None
        if obj_name:
            obj_key = make_entity_key(obj_name, obj_type)
            obj_id = entity_id_by_key.get(obj_key)
            # If the object entity wasn't declared, we simply leave object_entity_id=None
            # and keep object_name encoded in relation_text.

        triple_key = make_triple_key(subj_id, relation_type, obj_id)
        triple = existing_by_key.get(triple_key)

        if triple:
            # Update last_seen_at and importance / confidence if provided
            triple.last_seen_at = datetime.now()
            if isinstance(importance, (int, float)):
                if triple.importance is None or importance > triple.importance:
                    triple.importance = float(importance)
            if isinstance(confidence, (int, float)):
                if triple.confidence is None or confidence > triple.confidence:
                    triple.confidence = float(confidence)
            if is_state is not None:
                triple.is_state = bool(is_state)
            reused_triples += 1
        else:
            triple = TripleModel(
                subject_entity_id=subj_id,
                object_entity_id=obj_id,
                relation_type=relation_type,
                relation_text=relation_text,
                importance=float(importance) if isinstance(importance, (int, float)) else None,
                is_state=bool(is_state) if is_state is not None else False,
                confidence=float(confidence) if isinstance(confidence, (int, float)) else None,
                first_seen_at=datetime.now(),
                last_seen_at=datetime.now(),
            )
            db.add(triple)
            db.flush()
            existing_by_key[triple_key] = triple
            new_triples += 1

        # Ensure links
        ensure_triple_session_link(db, triple, session_summary)
        ensure_triple_chunk_link(db, triple, chunk)

    logger.info(
        "Triple upsert complete: total_keys=%d, new=%d, reused=%d",
        len(existing_by_key),
        new_triples,
        reused_triples,
    )
