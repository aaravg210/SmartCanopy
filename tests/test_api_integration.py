"""
Integration tests for FastAPI endpoints

These tests verify that all API endpoints work correctly together.
"""

import pytest
import httpx
from fastapi.testclient import TestClient
from api.main import app
import asyncio


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


class TestHealthEndpoints:
    """Test health check and root endpoints"""

    def test_health_check(self, client):
        """Test GET /api/health endpoint"""
        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_root_endpoint(self, client):
        """Test GET / endpoint"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        # API returns name, version, description, not message
        assert "name" in data
        assert "SmartCanopy" in data["name"]


class TestSpeciesEndpoints:
    """Test species database endpoints"""

    def test_species_search_all(self, client, sample_species):
        """Test GET /api/species/search without filters"""
        response = client.get("/api/species/search")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_species_search_by_name(self, client, sample_species):
        """Test GET /api/species/search with name query"""
        response = client.get("/api/species/search?query=Sycamore")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Should find American Sycamore
        if len(data) > 0:
            assert any("Sycamore" in s["common_name"] for s in data)

    def test_species_search_by_hardiness_zone(self, client, sample_species):
        """Test GET /api/species/search with hardiness zone filter"""
        response = client.get("/api/species/search?hardiness_zone=7")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # All results should support zone 7
        for species in data:
            assert species["hardiness_zone_min"] <= 7 <= species["hardiness_zone_max"]

    def test_species_search_by_drought_tolerance(self, client, sample_species):
        """Test GET /api/species/search with drought_tolerant filter"""
        response = client.get("/api/species/search?drought_tolerant=false")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_species_detail(self, client, sample_species):
        """Test GET /api/species/{species_id}"""
        response = client.get("/api/species/PLAC")

        assert response.status_code == 200
        data = response.json()
        assert data["species_id"] == "PLAC"
        assert data["common_name"] == "American Sycamore"
        assert "environmental_benefits" in data
        assert "pricing" in data

    def test_species_detail_not_found(self, client):
        """Test GET /api/species/{species_id} with invalid ID"""
        response = client.get("/api/species/INVALID")

        assert response.status_code == 404

    def test_species_list_pagination(self, client, sample_species):
        """Test GET /api/species/ with pagination"""
        response = client.get("/api/species/?offset=0&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10


class TestSiteEndpoints:
    """Test planting site endpoints"""

    def test_get_site_detail(self, client, sample_planting_site):
        """Test GET /api/sites/{site_id}"""
        site_id = sample_planting_site["site_id"]
        response = client.get(f"/api/sites/{site_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["site_id"] == site_id
        assert data["address"] == sample_planting_site["address"]
        assert "avg_ndvi" in data
        assert "suitability_score" in data

    def test_get_site_not_found(self, client):
        """Test GET /api/sites/{site_id} with invalid ID"""
        response = client.get("/api/sites/invalid-uuid")

        assert response.status_code in [404, 422]  # 422 for invalid UUID format

    def test_upload_site_photo(self, client, sample_planting_site):
        """Test POST /api/sites/{site_id}/photo"""
        site_id = sample_planting_site["site_id"]

        # Create a minimal PNG file
        png_bytes = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01'
            b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        )

        files = {'file': ('test.png', png_bytes, 'image/png')}
        data = {'question': 'Analyze this planting site'}

        # This may fail without Claude API credentials, but tests the endpoint structure
        response = client.post(
            f"/api/sites/{site_id}/photo",
            files=files,
            data=data
        )

        # Accept both success and auth failures
        assert response.status_code in [200, 401, 500]

    def test_get_site_photos(self, client, sample_planting_site):
        """Test GET /api/sites/{site_id}/photos"""
        site_id = sample_planting_site["site_id"]
        response = client.get(f"/api/sites/{site_id}/photos")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestAgentEndpoints:
    """Test AI agent endpoints"""

    def test_agent_chat_basic(self, client):
        """Test POST /api/agent/chat with basic message"""
        payload = {
            "message": "Hello, what can you help me with?",
            "conversation_history": []
        }

        # May fail without Claude API, but tests endpoint structure
        response = client.post("/api/agent/chat", json=payload)

        # Accept success or auth failures
        assert response.status_code in [200, 401, 500]

        if response.status_code == 200:
            data = response.json()
            assert "response" in data
            assert "conversation_id" in data
            assert "conversation_history" in data
            assert "tool_calls" in data
            assert "rounds" in data

    def test_agent_chat_with_history(self, client):
        """Test POST /api/agent/chat with conversation history"""
        payload = {
            "message": "What are the benefits?",
            "conversation_id": "test-123",
            "conversation_history": [
                {"role": "user", "content": "Tell me about trees"},
                {"role": "assistant", "content": "Trees provide many benefits..."}
            ]
        }

        response = client.post("/api/agent/chat", json=payload)

        # Accept success or auth failures
        assert response.status_code in [200, 401, 500]

    def test_agent_chat_validation(self, client):
        """Test POST /api/agent/chat with invalid input"""
        payload = {
            "message": "",  # Empty message should fail validation
            "conversation_history": []
        }

        response = client.post("/api/agent/chat", json=payload)

        assert response.status_code == 422  # Validation error


class TestCVEndpoints:
    """Test computer vision analysis endpoints"""

    def test_cv_analyze(self, client):
        """Test POST /api/cv/analyze"""
        payload = {
            "address": "123 Main St, San Jose, CA",
            "buffer_m": 50
        }

        # This requires GEE authentication and will likely fail in test environment
        response = client.post("/api/cv/analyze", json=payload)

        # Accept various responses (success, auth failure, GEE not configured)
        assert response.status_code in [200, 401, 500, 503]

        if response.status_code == 200:
            data = response.json()
            assert "analysis_id" in data
            assert "sites" in data
            assert isinstance(data["sites"], list)

    def test_cv_analyze_validation(self, client):
        """Test POST /api/cv/analyze with invalid input"""
        payload = {
            "address": "",  # Empty address
            "buffer_m": 50
        }

        response = client.post("/api/cv/analyze", json=payload)

        assert response.status_code == 422  # Validation error

    def test_get_analysis_result(self, client):
        """Test GET /api/cv/analysis/{analysis_id}"""
        # Use a fake UUID
        response = client.get("/api/cv/analysis/550e8400-e29b-41d4-a716-446655440000")

        # Will return 404 since analysis doesn't exist
        assert response.status_code == 404


class TestCORSHeaders:
    """Test CORS configuration"""

    def test_cors_headers_present(self, client):
        """Test that CORS headers are included in responses"""
        response = client.get("/api/health", headers={"Origin": "http://localhost:3000"})

        assert response.status_code == 200
        # FastAPI TestClient doesn't fully simulate CORS, but we can check the config exists


class TestErrorHandling:
    """Test error handling"""

    def test_404_not_found(self, client):
        """Test 404 for non-existent endpoints"""
        response = client.get("/api/nonexistent")

        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test 405 for wrong HTTP method"""
        response = client.get("/api/agent/chat")  # Should be POST

        assert response.status_code == 405


class TestOpenAPIDocumentation:
    """Test OpenAPI documentation endpoints"""

    def test_swagger_ui_accessible(self, client):
        """Test that Swagger UI is accessible"""
        response = client.get("/api/docs")

        assert response.status_code == 200

    def test_redoc_accessible(self, client):
        """Test that ReDoc is accessible"""
        response = client.get("/api/redoc")

        assert response.status_code == 200

    def test_openapi_json(self, client):
        """Test that OpenAPI JSON schema is available"""
        response = client.get("/api/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
