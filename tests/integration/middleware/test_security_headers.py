"""Integration tests for security headers middleware."""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestSecurityHeadersMiddleware:
    """Tests for security headers middleware."""

    async def test_security_headers_on_health_endpoint(self, client: AsyncClient):
        """Test security headers are present on health endpoint."""
        response = await client.get("/health")

        assert response.status_code in [200, 503]

        # Verify all required security headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        assert "Strict-Transport-Security" in response.headers
        assert "max-age=31536000" in response.headers["Strict-Transport-Security"]
        assert "includeSubDomains" in response.headers["Strict-Transport-Security"]
        assert "default-src 'self'" in response.headers["Content-Security-Policy"]
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert "Permissions-Policy" in response.headers

    async def test_security_headers_on_api_endpoints(self, authenticated_client):
        """Test security headers on authenticated API endpoints."""
        client, headers = authenticated_client

        response = await client.get("/api/v1/auth/me", headers=headers)

        assert response.status_code == 200

        # Verify headers
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"

    async def test_security_headers_on_error_responses(self, client: AsyncClient):
        """Test security headers are present even on error responses."""
        # Trigger 404
        response = await client.get("/api/v1/nonexistent-endpoint")

        assert response.status_code == 404

        # Headers should still be present
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"

    async def test_security_headers_on_unauthenticated_request(self, client: AsyncClient):
        """Test security headers on unauthenticated requests."""
        # Try to access protected endpoint without auth
        response = await client.get("/api/v1/designs")

        assert response.status_code == 403

        # Headers should be present
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-Content-Type-Options"] == "nosniff"

    async def test_security_headers_on_post_request(self, client: AsyncClient):
        """Test security headers on POST requests."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "security_test@test.com",
                "password": "Test1234!",
                "full_name": "Security Test",
            },
        )

        # Should have headers regardless of success/failure
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers

    async def test_hsts_header_format(self, client: AsyncClient):
        """Test Strict-Transport-Security header format."""
        response = await client.get("/health")

        hsts = response.headers.get("Strict-Transport-Security")
        assert hsts is not None

        # Should include max-age
        assert "max-age=" in hsts

        # Should include includeSubDomains
        assert "includeSubDomains" in hsts

        # Max-age should be at least 1 year (31536000 seconds)
        import re

        match = re.search(r"max-age=(\d+)", hsts)
        assert match is not None
        max_age = int(match.group(1))
        assert max_age >= 31536000

    async def test_csp_header_prevents_inline_scripts(self, client: AsyncClient):
        """Test Content-Security-Policy header configuration."""
        response = await client.get("/health")

        csp = response.headers.get("Content-Security-Policy")
        assert csp is not None

        # Should restrict to self
        assert "default-src 'self'" in csp

    async def test_permissions_policy_header_present(self, client: AsyncClient):
        """Test Permissions-Policy header is present."""
        response = await client.get("/health")

        permissions = response.headers.get("Permissions-Policy")
        assert permissions is not None

        # Should disable dangerous features
        assert "geolocation=()" in permissions
        assert "microphone=()" in permissions
        assert "camera=()" in permissions
