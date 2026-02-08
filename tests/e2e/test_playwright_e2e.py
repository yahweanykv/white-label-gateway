"""E2E tests using Playwright."""

import os
import time
from uuid import uuid4

import httpx
import pytest
from playwright.async_api import Page, async_playwright

# Use 127.0.0.1 to avoid IPv6 localhost issues on Windows/Docker
DEFAULT_HOST = "127.0.0.1"
E2E_TIMEOUT = 30.0  # Increased for cold start / slow first request


@pytest.fixture(scope="module")
def gateway_url():
    """Get gateway URL from environment or use default."""
    return os.getenv("GATEWAY_URL", f"http://{DEFAULT_HOST}:8000")


@pytest.fixture(scope="module")
def merchant_service_url():
    """Get merchant service URL from environment or use default."""
    return os.getenv("MERCHANT_SERVICE_URL", f"http://{DEFAULT_HOST}:8001")


@pytest.fixture(scope="module")
def payment_service_url():
    """Get payment service URL from environment or use default."""
    return os.getenv("PAYMENT_SERVICE_URL", f"http://{DEFAULT_HOST}:8002")


@pytest.mark.asyncio
async def test_create_merchant_e2e(gateway_url, merchant_service_url):
    """E2E test: Create merchant through API."""
    async with httpx.AsyncClient(timeout=E2E_TIMEOUT) as client:
        # Create merchant
        merchant_data = {
            "name": "E2E Test Merchant",
            "domain": f"e2e-{uuid4().hex[:8]}.test",
            "logo_url": "https://example.com/logo.png",
            "primary_color": "#4F46E5",
            "background_color": "#EEF2FF",
        }

        response = await client.post(
            f"{merchant_service_url}/api/v1/merchants/", json=merchant_data
        )
        assert response.status_code == 201
        merchant = response.json()
        assert merchant["name"] == "E2E Test Merchant"
        assert len(merchant["api_keys"]) > 0
        api_key = merchant["api_keys"][0]

        return api_key, merchant["id"]


@pytest.mark.asyncio
async def test_payment_success_e2e(gateway_url, merchant_service_url):
    """E2E test: Complete payment flow with success."""
    async with httpx.AsyncClient(timeout=E2E_TIMEOUT) as client:
        # Create merchant
        merchant_data = {
            "name": "Success Test Merchant",
            "domain": f"success-{uuid4().hex[:8]}.test",
        }
        merchant_response = await client.post(
            f"{merchant_service_url}/api/v1/merchants/", json=merchant_data
        )
        assert merchant_response.status_code == 201
        api_key = merchant_response.json()["api_keys"][0]
        merchant_id = merchant_response.json()["id"]

        # Create payment with mock_success provider
        payment_data = {
            "merchant_id": merchant_id,
            "amount": "100.00",
            "currency": "USD",
            "payment_method": "card",
        }

        payment_response = await client.post(
            f"{gateway_url}/v1/payments/",
            json=payment_data,
            headers={"X-API-Key": api_key},
        )
        assert payment_response.status_code == 201
        payment = payment_response.json()
        assert payment["status"] == "succeeded"
        assert payment["amount"] == "100.00"
        assert "transaction_id" in payment


@pytest.mark.asyncio
async def test_payment_3ds_e2e(gateway_url, merchant_service_url, payment_service_url):
    """E2E test: Complete 3DS payment flow with Playwright."""
    async with httpx.AsyncClient(timeout=E2E_TIMEOUT) as client:
        # Create merchant
        merchant_data = {
            "name": "3DS Test Merchant",
            "domain": f"3ds-{uuid4().hex[:8]}.test",
            "logo_url": "https://example.com/logo.png",
            "primary_color": "#FF0000",
            "background_color": "#FFFFFF",
        }
        merchant_response = await client.post(
            f"{merchant_service_url}/api/v1/merchants/", json=merchant_data
        )
        assert merchant_response.status_code == 201
        api_key = merchant_response.json()["api_keys"][0]
        merchant_id = merchant_response.json()["id"]

        # Create payment with mock_3ds provider
        payment_data = {
            "merchant_id": merchant_id,
            "amount": "150.00",
            "currency": "EUR",
            "payment_method": "card",
        }

        payment_response = await client.post(
            f"{gateway_url}/v1/payments/",
            json=payment_data,
            headers={"X-API-Key": api_key},
        )
        assert payment_response.status_code == 201
        payment = payment_response.json()
        if payment["status"] != "requires_action":
            pytest.skip(
                "test_payment_3ds_e2e requires PAYMENT_PROVIDER=mock_3ds. "
                "Restart: PAYMENT_PROVIDER=mock_3ds docker-compose up -d gateway payment-service"
            )
        assert payment["requires_action"] is True
        assert "next_action_url" in payment

        payment_id = payment["payment_id"]

        # Use Playwright to complete 3DS flow
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Navigate to 3DS page
            next_action_url = payment["next_action_url"]
            full_url = f"{gateway_url}{next_action_url}"
            await page.goto(full_url, wait_until="networkidle")

            # Wait for page to load
            await page.wait_for_selector("button", timeout=5000)

            # Check that page contains merchant branding
            page_content = await page.content()
            assert "3DS Test Merchant" in page_content or "merchant" in page_content.lower()

            # Click confirm button
            confirm_button = (
                page.locator("button:has-text('Подтвердить')")
                .or_(page.locator("button:has-text('Confirm')"))
                .or_(page.locator("button[type='submit']"))
                .first()
            )

            if await confirm_button.count() > 0:
                await confirm_button.click()
                await page.wait_for_load_state("networkidle", timeout=10000)

                # Should redirect to success page
                current_url = page.url
                assert "mock-success" in current_url or "success" in current_url.lower()

                # Verify payment is completed
                payment_check = await client.get(
                    f"{payment_service_url}/api/v1/payments/{payment_id}"
                )
                assert payment_check.status_code == 200
                completed_payment = payment_check.json()
                assert completed_payment["status"] == "succeeded"
                assert completed_payment["requires_action"] is False

            await browser.close()


@pytest.mark.asyncio
async def test_merchant_dashboard_e2e(merchant_service_url):
    """E2E test: Access merchant dashboard."""
    async with httpx.AsyncClient(timeout=E2E_TIMEOUT) as client:
        # Create merchant
        merchant_data = {
            "name": "Dashboard Test Merchant",
            "domain": f"dashboard-{uuid4().hex[:8]}.test",
        }
        merchant_response = await client.post(
            f"{merchant_service_url}/api/v1/merchants/", json=merchant_data
        )
        assert merchant_response.status_code == 201
        merchant = merchant_response.json()
        merchant_id = merchant["id"]
        api_key = merchant["api_keys"][0]

        # Access dashboard (requires api_key for auth)
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            dashboard_url = f"{merchant_service_url}/api/v1/dashboard?api_key={api_key}"
            await page.goto(dashboard_url, wait_until="networkidle")

            # Check dashboard content
            page_content = await page.content()
            assert "Dashboard" in page_content or "dashboard" in page_content.lower()

            await browser.close()
