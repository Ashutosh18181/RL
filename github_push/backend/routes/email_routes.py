"""
Email data routes — browse the full email corpus.
Endpoints: GET /emails, GET /emails/{id}
"""

from fastapi import APIRouter, HTTPException

from env.email_data import EMAIL_CORPUS, get_email

router = APIRouter()


@router.get("/emails")
async def list_emails(
    category: str | None = None,
    min_urgency: float = 0.0,
    limit: int = 50,
):
    """
    List all emails in the corpus with optional filters.
    
    Query params:
    - category: filter by category (complaint/refund/inquiry/spam/urgent/abuse)
    - min_urgency: minimum urgency_score (0.0–1.0)
    - limit: max results (default 50)
    """
    results = [e for e in EMAIL_CORPUS]

    if category:
        results = [e for e in results if e.category.value == category]

    if min_urgency > 0.0:
        results = [e for e in results if e.urgency_score >= min_urgency]

    results = results[:limit]
    return {
        "count": len(results),
        "emails": [e.model_dump() for e in results],
    }


@router.get("/emails/{email_id}")
async def get_email_by_id(email_id: str):
    """Get full detail for a single email by ID."""
    email = get_email(email_id)
    if email is None:
        raise HTTPException(status_code=404, detail=f"Email '{email_id}' not found.")
    return email.model_dump()
