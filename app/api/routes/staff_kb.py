from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
from app.api.deps import get_current_staff_user

router = APIRouter(prefix="/api/staff/kb", tags=["staff-kb"])

class KbDocOut(BaseModel):
    doc_id: str
    title: str
    snippet: str
    score: float
    source_url: Optional[str] = None

# Pre‑populated mock KB documents
MOCK_KB: List[KbDocOut] = [
    KbDocOut(
        doc_id="kb1",
        title="Garbage Collection Schedule",
        snippet="Garbage is collected every Monday and Thursday in Zone A. Place bins before 7:00 AM.",
        score=0.95,
        source_url="https://city.gov/garbage-schedule"
    ),
    KbDocOut(
        doc_id="kb2",
        title="Recycling Rules",
        snippet="Recycling pickup is every Wednesday. Rinse containers thoroughly and avoid plastic bags.",
        score=0.92,
        source_url="https://city.gov/recycling"
    ),
    KbDocOut(
        doc_id="kb3",
        title="Streetlight Outage Reporting",
        snippet="Report outages via the 311 hotline or online form. Include the pole number and nearest address.",
        score=0.89,
        source_url="https://city.gov/streetlight"
    ),
    KbDocOut(
        doc_id="kb4",
        title="Water Service Interruption Alerts",
        snippet="Check the city's alert page for scheduled maintenance or emergency water service interruptions.",
        score=0.87,
        source_url="https://city.gov/water-alerts"
    ),
    KbDocOut(
        doc_id="kb5",
        title="Snow Removal Policy",
        snippet="Snow removal begins once snowfall exceeds 2 inches. Priority is given to main roads and hospitals.",
        score=0.85,
        source_url="https://city.gov/snow-removal"
    ),
]

@router.get("/search", response_model=dict)
async def search_kb(
    query: str = Query(..., min_length=2, description="Search term"),
    staff_user=Depends(get_current_staff_user)
):
    """
    Search the Knowledge Base for the given query term.
    This mock implementation filters from MOCK_KB by matching the query
    in the title or snippet (case-insensitive).
    """
    query_lower = query.lower()
    filtered = [
        doc for doc in MOCK_KB
        if query_lower in doc.title.lower() or query_lower in doc.snippet.lower()
    ]
    return {"results": filtered}
