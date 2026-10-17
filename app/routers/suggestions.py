"""
Suggesting new terms, and reviewing those suggestions.

Anyone can suggest a term. It only becomes part of the glossary once a
reviewer approves it, so the glossary stays accurate.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.database import get_db
from app.models import Suggestion, Term
from app.schemas import ReviewIn, SuggestionIn, SuggestionOut
from app.search import normalise

router = APIRouter(prefix="/api/suggestions", tags=["suggestions"])


def find_term(db: Session, english: str, xhosa: str) -> Term | None:
    return db.scalar(select(Term).where(
        Term.english_norm == normalise(english),
        Term.xhosa_norm == normalise(xhosa),
    ))


@router.post("", response_model=SuggestionOut, status_code=status.HTTP_201_CREATED)
def create_suggestion(data: SuggestionIn, db: Session = Depends(get_db)):
    if find_term(db, data.english, data.xhosa):
        raise HTTPException(status.HTTP_409_CONFLICT, "This term is already in the glossary")

    # Has someone already suggested the same pair, still waiting for review?
    pending = db.scalars(select(Suggestion).where(Suggestion.status == "pending")).all()
    for s in pending:
        if normalise(s.english) == normalise(data.english) and normalise(s.xhosa) == normalise(data.xhosa):
            raise HTTPException(status.HTTP_409_CONFLICT, "This term has already been suggested")

    suggestion = Suggestion(**data.model_dump())
    db.add(suggestion)
    db.commit()
    db.refresh(suggestion)
    return suggestion


@router.get("", response_model=list[SuggestionOut], dependencies=[Depends(require_admin)])
def list_suggestions(
    status_filter: str = Query(default="pending", alias="status",
                               pattern="^(pending|approved|rejected)$"),
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Suggestion)
        .where(Suggestion.status == status_filter)
        .order_by(Suggestion.created_at)
    ).all()


def get_pending(db: Session, suggestion_id: int) -> Suggestion:
    suggestion = db.get(Suggestion, suggestion_id)
    if suggestion is None:
        raise HTTPException(404, "Suggestion not found")
    if suggestion.status != "pending":
        raise HTTPException(status.HTTP_409_CONFLICT, f"Suggestion is already {suggestion.status}")
    return suggestion


@router.post("/{suggestion_id}/approve", response_model=SuggestionOut,
             dependencies=[Depends(require_admin)])
def approve_suggestion(suggestion_id: int, review: ReviewIn | None = None,
                       db: Session = Depends(get_db)):
    suggestion = get_pending(db, suggestion_id)

    # The term may have been added another way since it was suggested
    if find_term(db, suggestion.english, suggestion.xhosa):
        raise HTTPException(status.HTTP_409_CONFLICT, "This term is already in the glossary")

    term = Term(
        english=suggestion.english,
        xhosa=suggestion.xhosa,
        english_norm=normalise(suggestion.english),
        xhosa_norm=normalise(suggestion.xhosa),
        category=suggestion.category,
        definition=suggestion.definition,
        example_xh=suggestion.example_xh,
        source=f"Suggested by {suggestion.submitted_by}" if suggestion.submitted_by else "Community suggestion",
    )
    db.add(term)
    db.flush()  # gives the new term its id before we commit

    suggestion.status = "approved"
    suggestion.term_id = term.id
    suggestion.review_note = review.review_note if review else None
    suggestion.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(suggestion)
    return suggestion


@router.post("/{suggestion_id}/reject", response_model=SuggestionOut,
             dependencies=[Depends(require_admin)])
def reject_suggestion(suggestion_id: int, review: ReviewIn | None = None,
                      db: Session = Depends(get_db)):
    suggestion = get_pending(db, suggestion_id)
    suggestion.status = "rejected"
    suggestion.review_note = review.review_note if review else None
    suggestion.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(suggestion)
    return suggestion
