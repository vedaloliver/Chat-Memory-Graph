# src/app/core/memory/entities.py

from datetime import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session

from src.app.core.logging_utils import get_logger
from src.app.models.database_models import EntityModel

logger = get_logger(__name__)


def make_entity_key(name: str, entity_type: Optional[str]) -> str:
    """
    Canonical key for entity dedup: lowercased "name|type".
    """
    name_norm = (name or "").strip().lower()
    type_norm = (entity_type or "").strip().lower()
    return f"{name_norm}|{type_norm}"


def upsert_entities(
    db: Session,
    entities_data: List[Dict[str, Any]],
) -> Dict[str, EntityModel]:
    """
    Upsert EntityModel rows.

    Returns:
        dict keyed by canonical (name|type) -> EntityModel
    """
    cache: Dict[str, EntityModel] = {}

    # Collect the canonical keys we actually need.
    keys_needed: Dict[str, Dict[str, str]] = {}
    for e in entities_data:
        name = (e.get("canonical_name") or "").strip()
        if not name:
            continue
        entity_type = e.get("entity_type")
        key = make_entity_key(name, entity_type)
        keys_needed[key] = {"canonical_name": name, "entity_type": entity_type}

    if not keys_needed:
        return cache

    # Query existing entities by canonical_name (type will be resolved via key).
    name_type_pairs = list(keys_needed.values())
    existing_entities = (
        db.query(EntityModel)
        .filter(
            EntityModel.canonical_name.in_(
                [p["canonical_name"] for p in name_type_pairs]
            )
        )
        .all()
    )

    for ent in existing_entities:
        key = make_entity_key(ent.canonical_name, ent.entity_type)
        cache[key] = ent

    new_count = 0
    reused_count = 0

    for e in entities_data:
        name = (e.get("canonical_name") or "").strip()
        if not name:
            continue
        entity_type = e.get("entity_type")
        aliases = e.get("aliases") or []

        key = make_entity_key(name, entity_type)
        if key in cache:
            ent = cache[key]
            # Update last_seen_at & optional aliases
            ent.last_seen_at = datetime.now()
            if aliases:
                existing_aliases = set(ent.aliases or [])
                for a in aliases:
                    if a and a not in existing_aliases:
                        existing_aliases.add(a)
                ent.aliases = list(existing_aliases)
            reused_count += 1
            continue

        ent = EntityModel(
            canonical_name=name,
            entity_type=entity_type,
            aliases=aliases or [],
            first_seen_at=datetime.now(),
            last_seen_at=datetime.now(),
        )
        db.add(ent)
        db.flush()
        cache[key] = ent
        new_count += 1

    logger.info(
        "Entity upsert complete: total=%d, new=%d, reused=%d",
        len(cache),
        new_count,
        reused_count,
    )
    return cache
