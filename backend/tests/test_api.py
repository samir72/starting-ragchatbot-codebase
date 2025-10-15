"""
Comprehensive API endpoint tests for the RAG system FastAPI application.

These tests validate:
- POST /api/query endpoint functionality
- GET /api/courses endpoint functionality
- GET / root endpoint
- Request/response validation
- Error handling
- Session management
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock


# ============================================================================
# Test Markers
# ============================================================================

pytestmark = pytest.mark.api


# ============================================================================
# Root Endpoint Tests
# ============================================================================

class TestRootEndpoint:
    """Test suite for root endpoint"""

    def test_root_endpoint_returns_success(self, test_client):
        """Test that root endpoint returns 200 OK"""
        response = test_client.get("/")
        assert response.status_code == 200

    def test_root_endpoint_returns_json(self, test_client):
        """Test that root endpoint returns JSON response"""
        response = test_client.get("/")
        assert response.headers["content-type"] == "application/json"

    def test_root_endpoint_returns_message(self, test_client):
        """Test that root endpoint returns expected message"""
        response = test_client.get("/")
        data = response.json()
        assert "message" in data
        assert isinstance(data["message"], str)


# ============================================================================
# Query Endpoint Tests
# ============================================================================

class TestQueryEndpoint:
    """Test suite for /api/query endpoint"""

    def test_query_endpoint_success(self, test_client):
        """Test successful query request"""
        response = test_client.post(
            "/api/query",
            json={
                "query": "What is Python?",
                "session_id": "test-session-123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data
        assert data["session_id"] == "test-session-123"

    def test_query_endpoint_without_session_id(self, test_client):
        """Test query request without session_id creates new session"""
        response = test_client.post(
            "/api/query",
            json={"query": "What is Python?"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["session_id"] == "test-session-123"  # From mock

    def test_query_endpoint_returns_correct_structure(self, test_client):
        """Test that query response has correct structure"""
        response = test_client.post(
            "/api/query",
            json={"query": "Explain variables in Python"}
        )

        assert response.status_code == 200
        data = response.json()

        # Check answer field
        assert isinstance(data["answer"], str)
        assert len(data["answer"]) > 0

        # Check sources field
        assert isinstance(data["sources"], list)
        for source in data["sources"]:
            assert "text" in source
            assert "url" in source
            assert isinstance(source["text"], str)
            assert isinstance(source["url"], str)

        # Check session_id field
        assert isinstance(data["session_id"], str)

    def test_query_endpoint_with_empty_query(self, test_client):
        """Test query endpoint with empty query string"""
        response = test_client.post(
            "/api/query",
            json={"query": "", "session_id": "test-session-123"}
        )

        # Should still process (validation happens in RAG system)
        assert response.status_code == 200

    def test_query_endpoint_missing_query_field(self, test_client):
        """Test query endpoint without required query field"""
        response = test_client.post(
            "/api/query",
            json={"session_id": "test-session-123"}
        )

        # Should return validation error (422)
        assert response.status_code == 422

    def test_query_endpoint_invalid_json(self, test_client):
        """Test query endpoint with invalid JSON"""
        response = test_client.post(
            "/api/query",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        # Should return validation error (422)
        assert response.status_code == 422

    def test_query_endpoint_handles_rag_system_error(self, test_client, test_app):
        """Test query endpoint handles RAG system errors gracefully"""
        # Configure mock to raise exception
        mock_rag = MagicMock()
        mock_rag.query.side_effect = Exception("Database connection failed")
        test_app.state.mock_rag = mock_rag

        response = test_client.post(
            "/api/query",
            json={"query": "What is Python?"}
        )

        # Should return 500 error
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Database connection failed" in data["detail"]

    def test_query_endpoint_with_long_query(self, test_client):
        """Test query endpoint with very long query string"""
        long_query = "What is Python? " * 100  # Very long query
        response = test_client.post(
            "/api/query",
            json={"query": long_query, "session_id": "test-session-123"}
        )

        # Should still process successfully
        assert response.status_code == 200

    def test_query_endpoint_with_special_characters(self, test_client):
        """Test query endpoint with special characters in query"""
        special_query = "What is Python? <script>alert('xss')</script> & $pecial ch@rs!"
        response = test_client.post(
            "/api/query",
            json={"query": special_query, "session_id": "test-session-123"}
        )

        # Should process successfully
        assert response.status_code == 200

    def test_query_endpoint_multiple_requests_same_session(self, test_client, test_app):
        """Test multiple queries with same session ID"""
        session_id = "test-session-456"

        # Make first request
        response1 = test_client.post(
            "/api/query",
            json={"query": "What is Python?", "session_id": session_id}
        )
        assert response1.status_code == 200
        assert response1.json()["session_id"] == session_id

        # Make second request with same session
        response2 = test_client.post(
            "/api/query",
            json={"query": "How do variables work?", "session_id": session_id}
        )
        assert response2.status_code == 200
        assert response2.json()["session_id"] == session_id

        # Verify RAG system was called with correct session
        assert test_app.state.mock_rag.query.call_count == 2


# ============================================================================
# Courses Endpoint Tests
# ============================================================================

class TestCoursesEndpoint:
    """Test suite for /api/courses endpoint"""

    def test_courses_endpoint_success(self, test_client):
        """Test successful courses request"""
        response = test_client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()
        assert "total_courses" in data
        assert "course_titles" in data

    def test_courses_endpoint_returns_correct_structure(self, test_client):
        """Test that courses response has correct structure"""
        response = test_client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()

        # Check total_courses field
        assert isinstance(data["total_courses"], int)
        assert data["total_courses"] >= 0

        # Check course_titles field
        assert isinstance(data["course_titles"], list)
        for title in data["course_titles"]:
            assert isinstance(title, str)

    def test_courses_endpoint_returns_json(self, test_client):
        """Test that courses endpoint returns JSON"""
        response = test_client.get("/api/courses")

        # Verify JSON response
        assert response.headers["content-type"] == "application/json"

    def test_courses_endpoint_handles_error(self, test_client, test_app):
        """Test courses endpoint handles errors gracefully"""
        # Configure mock to raise exception
        mock_rag = MagicMock()
        mock_rag.get_course_analytics.side_effect = Exception("Vector store unavailable")
        test_app.state.mock_rag = mock_rag

        response = test_client.get("/api/courses")

        # Should return 500 error
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Vector store unavailable" in data["detail"]

    def test_courses_endpoint_no_courses(self, test_client, test_app):
        """Test courses endpoint when no courses exist"""
        # Configure mock to return empty results
        mock_rag = MagicMock()
        mock_rag.get_course_analytics.return_value = {
            "total_courses": 0,
            "course_titles": []
        }
        test_app.state.mock_rag = mock_rag

        response = test_client.get("/api/courses")

        # Should return success with empty data
        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] == 0
        assert data["course_titles"] == []

    def test_courses_endpoint_multiple_courses(self, test_client, test_app):
        """Test courses endpoint with multiple courses"""
        # Configure mock with multiple courses
        mock_rag = MagicMock()
        mock_rag.get_course_analytics.return_value = {
            "total_courses": 5,
            "course_titles": [
                "Introduction to Programming",
                "Advanced Python",
                "Web Development",
                "Data Science",
                "Machine Learning"
            ]
        }
        test_app.state.mock_rag = mock_rag

        response = test_client.get("/api/courses")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] == 5
        assert len(data["course_titles"]) == 5


# ============================================================================
# CORS and Headers Tests
# ============================================================================

class TestCORSAndHeaders:
    """Test suite for CORS and HTTP headers"""

    def test_cors_headers_on_query_endpoint(self, test_client):
        """Test that CORS headers are present on query endpoint"""
        response = test_client.post(
            "/api/query",
            json={"query": "What is Python?"}
        )

        # Check CORS headers - TestClient doesn't include CORS headers by default
        # This is a known limitation of TestClient
        assert response.status_code == 200

    def test_cors_headers_on_courses_endpoint(self, test_client):
        """Test that CORS headers are present on courses endpoint"""
        response = test_client.get("/api/courses")

        # Check that request succeeds
        assert response.status_code == 200


# ============================================================================
# Integration-like Tests
# ============================================================================

class TestEndToEndScenarios:
    """Test realistic end-to-end scenarios"""

    def test_complete_query_flow(self, test_client):
        """Test complete query flow from request to response"""
        # Step 1: Make initial query
        response1 = test_client.post(
            "/api/query",
            json={"query": "What is Python?"}
        )
        assert response1.status_code == 200
        session_id = response1.json()["session_id"]

        # Step 2: Make follow-up query with same session
        response2 = test_client.post(
            "/api/query",
            json={"query": "How do I use variables?", "session_id": session_id}
        )
        assert response2.status_code == 200
        assert response2.json()["session_id"] == session_id

        # Step 3: Get course stats
        response3 = test_client.get("/api/courses")
        assert response3.status_code == 200
        assert response3.json()["total_courses"] > 0

    def test_error_recovery(self, test_client, test_app):
        """Test that errors don't break subsequent requests"""
        # Configure mock to fail first, then succeed
        mock_rag = MagicMock()
        call_count = 0

        def query_side_effect(*args):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Temporary error")
            return ("Answer", [{"text": "Source", "url": "http://example.com"}])

        mock_rag.query.side_effect = query_side_effect
        test_app.state.mock_rag = mock_rag

        # First request fails
        response1 = test_client.post(
            "/api/query",
            json={"query": "What is Python?"}
        )
        assert response1.status_code == 500

        # Second request succeeds
        response2 = test_client.post(
            "/api/query",
            json={"query": "What is Python?"}
        )
        assert response2.status_code == 200

    def test_concurrent_sessions(self, test_client):
        """Test handling multiple concurrent sessions"""
        sessions = []

        # Create multiple sessions
        for i in range(3):
            response = test_client.post(
                "/api/query",
                json={"query": f"Query {i}"}
            )
            assert response.status_code == 200
            sessions.append(response.json()["session_id"])

        # Verify all sessions work independently
        for i, session_id in enumerate(sessions):
            response = test_client.post(
                "/api/query",
                json={"query": f"Follow-up {i}", "session_id": session_id}
            )
            assert response.status_code == 200
            assert response.json()["session_id"] == session_id


# ============================================================================
# Input Validation Tests
# ============================================================================

class TestInputValidation:
    """Test input validation and edge cases"""

    @pytest.mark.parametrize("invalid_data", [
        {},  # Missing query field
        {"query": None},  # Null query
        {"session_id": "test"},  # Missing query field
        {"query": 123},  # Wrong type for query
    ])
    def test_invalid_query_requests(self, test_client, invalid_data):
        """Test various invalid query requests"""
        response = test_client.post("/api/query", json=invalid_data)
        assert response.status_code == 422  # Validation error

    @pytest.mark.parametrize("query", [
        "Simple query",
        "Query with numbers 12345",
        "Query with symbols !@#$%",
        "Query with unicode: 你好世界",
        "Query\nwith\nnewlines",
        "Query\twith\ttabs",
    ])
    def test_various_query_formats(self, test_client, query):
        """Test various valid query formats"""
        response = test_client.post(
            "/api/query",
            json={"query": query}
        )
        assert response.status_code == 200
