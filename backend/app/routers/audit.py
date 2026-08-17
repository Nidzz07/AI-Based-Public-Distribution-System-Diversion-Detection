"""Audit endpoint — F6 surface.

Read-only, and permanently so. There is one route here and it returns rows.
No route in this file may ever offer an edit or a removal of an audit row: the
trail is the one thing in LEAKPROOF that a magistrate is entitled to assume
nobody in this codebase can touch.

Ordered oldest first — the trail is read as a narrative of what happened to the
case, and a narrative runs forwards.
"""

import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import AuditLog
from ..schemas import AuditEventOut
from .cases import ensure_cases

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/{case_id}", response_model=list[AuditEventOut])
def get_trail(case_id: str, db: Session = Depends(get_db)):
    """Every event written against this case, oldest first.

    An empty list is a real answer: it means nothing has happened to this case
    yet, not that the case is missing.

    Cases are opened here too. Reaching the trail first on a cold database
    would otherwise show an auditor an empty history for a case that simply had
    not been derived yet — the most misleading screen in the app.
    """
    ensure_cases(db)

    rows = (
        db.query(AuditLog)
        .filter(AuditLog.case_id == case_id)
        .order_by(AuditLog.created_at, AuditLog.id)
        .all()
    )

    return [
        AuditEventOut(
            id=row.id,
            case_id=row.case_id,
            event_type=row.event_type,
            actor_role=row.actor_role,
            # Stored as text so an old row survives a payload shape change;
            # decoded here so the client does not have to parse twice.
            payload=json.loads(row.payload) if row.payload else None,
            rulebook_version=row.rulebook_version,
            created_at=row.created_at,
        )
        for row in rows
    ]
