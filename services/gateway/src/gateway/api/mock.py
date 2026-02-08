"""Mock redirect endpoints proxied through the gateway."""

from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse

from gateway.config import settings

router = APIRouter()


async def _proxy_static(asset: str) -> HTMLResponse:
    url = f"{settings.payment_service_url}/static/{asset}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            return HTMLResponse(
                content=response.text,
                status_code=response.status_code,
                media_type="text/html; charset=utf-8",
            )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Payment service static assets unavailable: {exc}",
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail="Unable to load mock page from payment service",
        ) from exc


@router.get("/mock-success", response_class=HTMLResponse, include_in_schema=False)
async def mock_success_page():
    """Serve branded mock success page."""
    return await _proxy_static("mock-success.html")


@router.get("/mock-3ds", response_class=HTMLResponse, include_in_schema=False)
async def mock_three_ds_page():
    """Serve 3DS challenge page."""
    return await _proxy_static("mock-3ds.html")


@router.post("/mock-3ds-complete", include_in_schema=False)
async def mock_three_ds_complete(
    payment_id: str = Form(...),
    merchant_name: str = Form("Demo Merchant"),
    logo_url: str = Form("https://via.placeholder.com/120?text=Logo"),
    primary_color: str = Form("#4F46E5"),
    background_color: str = Form("#EEF2FF"),
    amount: str = Form(""),
    currency: str = Form("RUB"),
):
    """Mark payment as succeeded and redirect to branded success page."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.payment_service_url}/api/v1/payments/{payment_id}/complete-3ds",
                timeout=10.0,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Payment not found",
                )
            raise HTTPException(
                status_code=exc.response.status_code,
                detail="Unable to finalize payment",
            ) from exc
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Payment service unavailable: {exc}",
            ) from exc

    query = urlencode(
        {
            "paymentId": payment_id,
            "merchantName": merchant_name,
            "logoUrl": logo_url,
            "primaryColor": primary_color,
            "backgroundColor": background_color,
            "amount": amount,
            "currency": currency,
        }
    )
    return RedirectResponse(
        url=f"/mock-success?{query}",
        status_code=status.HTTP_303_SEE_OTHER,
    )
