"""Public endpoints for searching and reading terms."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import CATEGORIES
from app.database import get_db
from app.models import Term
from app.schemas import CategoryOut, TermOut, TermPage
from app.search import build_search_query

router = APIRouter(prefix="/api", tags=["terms"])


@router.get("/terms", response_model=TermPage)
def list_terms(
    q: str | None = Query(default=None, max_length=100,
                          description="Search text, in English or isiXhosa"),
    category: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = build_search_query(q, category)
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
    items = db.scalars(stmt.limit(limit).offset(offset)).all()
    return TermPage(total=total, limit=limit, offset=offset, items=items)


@router.get("/terms/{term_id}", response_model=TermOut)
def get_term(term_id: int, db: Session = Depends(get_db)):
    term = db.get(Term, term_id)
    if term is None:
        raise HTTPException(404, "Term not found")
    return term


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    counts = dict(db.execute(
        select(Term.category, func.count()).group_by(Term.category)
    ).all())
    return [CategoryOut(name=c, count=counts.get(c, 0)) for c in CATEGORIES]
