"""Public government services directory API with pagination support."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.session import get_auth_session

router = APIRouter(prefix="/api/services", tags=["services"])


class ServiceSummary(BaseModel):
    """Government service summary for mobile app."""
    id: str
    name: str
    description: str | None = None
    category: str | None = None
    icon: str | None = None
    status: str = "active"


class ServicesListResponse(BaseModel):
    """Paginated services list."""
    services: list[ServiceSummary]
    total: int
    page: int
    limit: int
    has_more: bool


# Hardcoded government services for now - can be replaced with database later
_SERVICES = [
    ServiceSummary(id="1", name="Cooperative Registration", description="Register new cooperative societies", category="cooperative", icon="business"),
    ServiceSummary(id="2", name="PMFBY Insurance", description="Pradhan Mantri Fasal Bima Yojana crop insurance", category="insurance", icon="security"),
    ServiceSummary(id="3", name="Agricultural Laws", description="Information on agricultural laws and regulations", category="laws", icon="gavel"),
    ServiceSummary(id="4", name="Loan Applications", description="Apply for cooperative loans and credit", category="financial", icon="account_balance"),
    ServiceSummary(id="5", name="Grievance Filing", description="File and track grievances", category="grievance", icon="report_problem"),
    ServiceSummary(id="6", name="Document Verification", description="Verify and authenticate documents", category="documents", icon="description"),
    ServiceSummary(id="7", name="Subsidy Claims", description="Apply for agricultural subsidies", category="financial", icon="account_balance_wallet"),
    ServiceSummary(id="8", name="Market Prices", description="Check current market prices for crops", category="cooperative", icon="trending_up"),
    ServiceSummary(id="9", name="Farmer Training", description="Register for farmer training programs", category="education", icon="school"),
    ServiceSummary(id="10", name="Equipment Rental", description="Rent agricultural equipment from cooperatives", category="cooperative", icon="build"),
    ServiceSummary(id="11", name="Crop Advisory", description="Get expert crop advisory services", category="agricultural", icon="agriculture"),
    ServiceSummary(id="12", name="Weather Updates", description="Receive weather alerts and forecasts", category="information", icon="cloud"),
    ServiceSummary(id="13", name="Soil Testing", description="Request soil testing services", category="agricultural", icon="science"),
    ServiceSummary(id="14", name="Seed Distribution", description="Access quality seed distribution", category="agricultural", icon="eco"),
    ServiceSummary(id="15", name="Fertilizer Subsidy", description="Apply for fertilizer subsidies", category="financial", icon="savings"),
    ServiceSummary(id="16", name="Land Records", description="View and update land records", category="documents", icon="map"),
    ServiceSummary(id="17", name="Water Management", description="Irrigation and water resource management", category="agricultural", icon="water_drop"),
    ServiceSummary(id="18", name="Livestock Services", description="Animal husbandry and veterinary services", category="agricultural", icon="pets"),
    ServiceSummary(id="19", name="Organic Certification", description="Get organic farming certification", category="documents", icon="verified"),
    ServiceSummary(id="20", name="Export Support", description="Support for agricultural exports", category="financial", icon="flight_takeoff"),
    ServiceSummary(id="21", name="Cold Storage", description="Book cold storage facilities", category="cooperative", icon="ac_unit"),
    ServiceSummary(id="22", name="Pest Control", description="Pest management and control services", category="agricultural", icon="bug_report"),
    ServiceSummary(id="23", name="Farm Mechanization", description="Access to modern farming equipment", category="cooperative", icon="precision_manufacturing"),
    ServiceSummary(id="24", name="Crop Insurance Claims", description="File crop insurance claims", category="insurance", icon="assignment"),
]


@router.get("", response_model=ServicesListResponse)
async def list_services(
    page: int = Query(default=1, ge=1, le=1000),
    limit: int = Query(default=20, ge=1, le=50),
    query: str | None = Query(default=None, max_length=200),
    category: str | None = Query(default=None, max_length=50),
    session: AsyncSession = Depends(get_auth_session),
) -> ServicesListResponse:
    """List government services with pagination and filtering."""
    
    # Filter services based on query and category
    filtered_services = _SERVICES
    
    if query:
        query_lower = query.lower()
        filtered_services = [
            s for s in filtered_services
            if query_lower in s.name.lower() or (s.description and query_lower in s.description.lower())
        ]
    
    if category:
        category_lower = category.lower()
        filtered_services = [
            s for s in filtered_services
            if s.category and category_lower in s.category.lower()
        ]
    
    # Calculate pagination
    total = len(filtered_services)
    offset = (page - 1) * limit
    paginated = filtered_services[offset:offset + limit]
    has_more = (offset + limit) < total
    
    return ServicesListResponse(
        services=paginated,
        total=total,
        page=page,
        limit=limit,
        has_more=has_more,
    )


@router.get("/{service_id}", response_model=ServiceSummary)
async def get_service(
    service_id: str,
    session: AsyncSession = Depends(get_auth_session),
) -> ServiceSummary:
    """Get detailed information about a specific service."""
    
    service = next((s for s in _SERVICES if s.id == service_id), None)
    if service is None:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found."
        )
    
    return service
