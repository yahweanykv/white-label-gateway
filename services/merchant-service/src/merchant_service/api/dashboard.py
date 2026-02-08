"""Dashboard API routes."""

from decimal import Decimal
from typing import Annotated, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from merchant_service.config import settings
from merchant_service.deps import get_db
from merchant_service.models import Merchant
from shared.utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


async def get_payment_stats(merchant_id: str) -> dict:
    """Get payment statistics for a merchant."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{settings.payment_service_url}/api/v1/payments/by-merchant/{merchant_id}",
            )
            response.raise_for_status()
            payments = response.json()
    except httpx.HTTPError as exc:
        logger.warning(f"Failed to fetch payments for merchant {merchant_id}: {exc}")
        payments = []

    total_payments = len(payments)
    successful = sum(1 for p in payments if p.get("status") == "succeeded")
    pending = sum(1 for p in payments if p.get("status") in ["processing", "requires_action"])
    revenue = sum(
        Decimal(str(p.get("amount", 0))) for p in payments if p.get("status") == "succeeded"
    )

    # Get currency from first successful payment, or default to USD
    currency = "USD"
    for p in payments:
        if p.get("status") == "succeeded" and p.get("currency"):
            currency = p.get("currency")
            break

    return {
        "total": total_payments,
        "successful": successful,
        "pending": pending,
        "revenue": revenue,
        "currency": currency,
    }


@router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """
    Get merchant dashboard with branding.

    Can accept API key either via X-API-Key header or via api_key query parameter (for demo purposes).

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        HTML dashboard page
    """
    from sqlalchemy import select

    # Try to get merchant from header first
    current_merchant = None
    x_api_key = (
        request.headers.get("X-API-Key")
        or request.headers.get("x-api-key")
        or request.headers.get("X-Api-Key")
    )

    if x_api_key:
        try:
            result = await db.execute(
                select(Merchant).where(
                    Merchant.api_keys.contains([x_api_key]), Merchant.is_active == True
                )
            )
            current_merchant = result.scalar_one_or_none()
        except Exception as e:
            logger.warning(f"Error getting merchant from header: {e}")

    # If no merchant from header auth, try query parameter
    if not current_merchant:
        api_key = request.query_params.get("api_key")
        if api_key:
            try:
                result = await db.execute(
                    select(Merchant).where(
                        Merchant.api_keys.contains([api_key]), Merchant.is_active == True
                    )
                )
                current_merchant = result.scalar_one_or_none()

                if not current_merchant:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid API key",
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Error getting merchant from query param: {e}")

    if not current_merchant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key header or api_key query parameter is required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    primary_color = current_merchant.primary_color or "#256569"
    background_color = current_merchant.background_color or "#E6F2F3"
    logo_url = current_merchant.logo_url or "https://via.placeholder.com/150"
    merchant_name = current_merchant.name

    # Get payment statistics
    stats = await get_payment_stats(str(current_merchant.id))

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{merchant_name} - Dashboard</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: linear-gradient(135deg, {primary_color}15 0%, {primary_color}05 100%);
                background-color: {background_color};
                min-height: 100vh;
                padding: 20px;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            .header {{
                background: white;
                border-radius: 12px;
                padding: 30px;
                margin-bottom: 30px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                display: flex;
                align-items: center;
                gap: 20px;
            }}
            .logo {{
                width: 80px;
                height: 80px;
                border-radius: 12px;
                object-fit: cover;
                border: 2px solid {primary_color}20;
            }}
            .header-content h1 {{
                color: {primary_color};
                font-size: 32px;
                margin-bottom: 5px;
            }}
            .header-content p {{
                color: #666;
                font-size: 14px;
            }}
            .stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .stat-card {{
                background: white;
                border-radius: 12px;
                padding: 25px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                border-left: 4px solid {primary_color};
            }}
            .stat-card h3 {{
                color: #666;
                font-size: 14px;
                text-transform: uppercase;
                margin-bottom: 10px;
            }}
            .stat-card .value {{
                color: {primary_color};
                font-size: 32px;
                font-weight: bold;
            }}
            .content-card {{
                background: white;
                border-radius: 12px;
                padding: 30px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .content-card h2 {{
                color: {primary_color};
                margin-bottom: 20px;
                font-size: 24px;
            }}
            .api-key-section {{
                background: #f8f9fa;
                border-radius: 8px;
                padding: 20px;
                margin-top: 20px;
            }}
            .api-key {{
                font-family: 'Courier New', monospace;
                background: white;
                padding: 12px;
                border-radius: 6px;
                border: 1px solid #ddd;
                word-break: break-all;
                margin-top: 10px;
            }}
            .btn {{
                background: linear-gradient(135deg, #256569 0%, #2d7a7f 100%);
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px 0 rgba(37, 101, 105, 0.4);
            }}
            .btn:hover {{
                background: linear-gradient(135deg, #2d7a7f 0%, #256569 100%);
                box-shadow: 0 6px 20px 0 rgba(37, 101, 105, 0.6);
                transform: translateY(-2px);
            }}
            .btn:active {{
                transform: translateY(0);
                box-shadow: 0 2px 10px 0 rgba(37, 101, 105, 0.4);
            }}
            .info-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }}
            .info-item {{
                padding: 15px;
                background: #f8f9fa;
                border-radius: 8px;
            }}
            .info-item label {{
                display: block;
                color: #666;
                font-size: 12px;
                text-transform: uppercase;
                margin-bottom: 5px;
            }}
            .info-item value {{
                display: block;
                color: #333;
                font-size: 16px;
                font-weight: 500;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <img src="{logo_url}" alt="{merchant_name} Logo" class="logo">
                <div class="header-content">
                    <h1>{merchant_name}</h1>
                    <p>Payment Gateway Dashboard</p>
                </div>
            </div>

            <div class="stats">
                <div class="stat-card">
                    <h3>Total Payments</h3>
                    <div class="value">{stats["total"]}</div>
                </div>
                <div class="stat-card">
                    <h3>Successful</h3>
                    <div class="value">{stats["successful"]}</div>
                </div>
                <div class="stat-card">
                    <h3>Pending</h3>
                    <div class="value">{stats["pending"]}</div>
                </div>
                <div class="stat-card">
                    <h3>Revenue</h3>
                    <div class="value">{stats["currency"]} {float(stats["revenue"]):.2f}</div>
                </div>
            </div>

            <div class="content-card">
                <h2>Merchant Information</h2>
                <div class="info-grid">
                    <div class="info-item">
                        <label>Merchant ID</label>
                        <value>{current_merchant.id}</value>
                    </div>
                    <div class="info-item">
                        <label>Domain</label>
                        <value>{current_merchant.domain or 'Not set'}</value>
                    </div>
                    <div class="info-item">
                        <label>Status</label>
                        <value>{'Active' if current_merchant.is_active else 'Inactive'}</value>
                    </div>
                    <div class="info-item">
                        <label>Webhook URL</label>
                        <value>{current_merchant.webhook_url or 'Not set'}</value>
                    </div>
                </div>

                <div class="api-key-section">
                    <h3 style="margin-bottom: 10px; color: {primary_color};">API Keys</h3>
                    <p style="color: #666; font-size: 14px; margin-bottom: 10px;">
                        Use these API keys to authenticate your requests:
                    </p>
                    {"".join([f'<div class="api-key">{key}</div>' for key in current_merchant.api_keys])}
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)
