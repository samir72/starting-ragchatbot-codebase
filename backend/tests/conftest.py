"""
Shared pytest fixtures and configuration for all tests
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import Mock, MagicMock
from fastapi.testclient import TestClient
from typing import Dict, List

from config import config as app_config
from ai_generator import AIGenerator
from rag_system import RAGSystem
from search_tools import CourseSearchTool, ToolManager
from vector_store import VectorStore
from models import CourseChunk


@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration"""
    return app_config


@pytest.fixture(scope="session")
def vector_store_instance():
    """Create a single VectorStore instance for the test session"""
    return VectorStore(
        chroma_path=app_config.CHROMA_PATH,
        embedding_model=app_config.EMBEDDING_MODEL,
        max_results=app_config.MAX_RESULTS,
    )


@pytest.fixture
def vector_store(vector_store_instance):
    """Provide VectorStore instance to tests"""
    return vector_store_instance


@pytest.fixture
def search_tool(vector_store_instance):
    """Create CourseSearchTool instance"""
    return CourseSearchTool(vector_store_instance)


@pytest.fixture
def tool_manager(vector_store_instance):
    """Create ToolManager with registered CourseSearchTool"""
    manager = ToolManager()
    search_tool = CourseSearchTool(vector_store_instance)
    manager.register_tool(search_tool)
    return manager


@pytest.fixture
def ai_generator():
    """Create AIGenerator instance"""
    return AIGenerator(
        api_key=app_config.ANTHROPIC_API_KEY, model=app_config.ANTHROPIC_MODEL
    )


@pytest.fixture
def rag_system_instance():
    """Create RAGSystem instance"""
    return RAGSystem(app_config)


def pytest_configure(config):
    """Pytest configuration hook"""
    # Add custom markers
    config.addinivalue_line(
        "markers", "integration: mark test as integration test that requires API"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test that doesn't require external services"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically skip tests that require API key if not available"""
    skip_no_api = pytest.mark.skip(reason="No API key configured")

    for item in items:
        # Check if test requires API and skip if no key
        if "real_api" in item.nodeid or "integration" in item.keywords:
            if not app_config.ANTHROPIC_API_KEY:
                item.add_marker(skip_no_api)


# ============================================================================
# FastAPI Testing Fixtures
# ============================================================================

@pytest.fixture
def test_app(mock_rag_system):
    """
    Create a test FastAPI application that doesn't mount static files.
    This prevents errors when frontend directory doesn't exist in test environment.
    """
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    from typing import Optional

    # Create a clean test app
    app = FastAPI(title="Test Course Materials RAG System")

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Import models from main app
    from app import QueryRequest, QueryResponse, CourseStats

    # Attach mock_rag to app state for test access
    app.state.mock_rag = mock_rag_system

    # Define endpoints inline for testing - use app.state.mock_rag to allow overriding
    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        try:
            session_id = request.session_id or "test-session-123"
            # Reference from app.state so tests can override
            answer, sources = app.state.mock_rag.query(request.query, session_id)
            return QueryResponse(
                answer=answer,
                sources=sources,
                session_id=session_id
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        try:
            # Reference from app.state so tests can override
            analytics = app.state.mock_rag.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/")
    async def root():
        return {"message": "Test RAG System API"}

    return app


@pytest.fixture
def test_client(test_app):
    """Create a test client for the FastAPI app"""
    return TestClient(test_app)


@pytest.fixture(scope="function")
def mock_rag_system():
    """Create a mock RAG system with pre-configured responses"""
    mock = MagicMock()

    # Configure default behavior - use return_value for consistent returns
    mock.query.return_value = (
        "This is a test answer about Python programming.",
        [
            {"text": "Introduction to Programming - Lesson 1", "url": "https://example.com/lesson1"},
            {"text": "Python Basics - Lesson 2", "url": "https://example.com/lesson2"}
        ]
    )

    mock.get_course_analytics.return_value = {
        "total_courses": 2,
        "course_titles": ["Introduction to Programming", "Advanced Python"]
    }

    mock.session_manager.create_session.return_value = "test-session-123"

    # Reset call counts for each test
    mock.reset_mock()

    return mock


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_course_chunks() -> List[CourseChunk]:
    """Provide sample course chunks for testing"""
    return [
        CourseChunk(
            text="Python is a high-level programming language known for its simplicity and readability.",
            course_title="Introduction to Programming",
            course_link="https://example.com/course1",
            course_instructor="Dr. Smith",
            lesson_number=1,
            lesson_link="https://example.com/lesson1"
        ),
        CourseChunk(
            text="Variables in Python are created when you assign a value to them. Python is dynamically typed.",
            course_title="Introduction to Programming",
            course_link="https://example.com/course1",
            course_instructor="Dr. Smith",
            lesson_number=2,
            lesson_link="https://example.com/lesson2"
        ),
        CourseChunk(
            text="List comprehensions provide a concise way to create lists in Python.",
            course_title="Advanced Python",
            course_link="https://example.com/course2",
            course_instructor="Prof. Johnson",
            lesson_number=1,
            lesson_link="https://example.com/lesson3"
        )
    ]


@pytest.fixture
def sample_query_request() -> Dict:
    """Provide sample query request data"""
    return {
        "query": "What is Python?",
        "session_id": "test-session-123"
    }


@pytest.fixture
def sample_query_response() -> Dict:
    """Provide sample query response data"""
    return {
        "answer": "Python is a high-level programming language known for its simplicity and readability.",
        "sources": [
            {"text": "Introduction to Programming - Lesson 1", "url": "https://example.com/lesson1"},
            {"text": "Introduction to Programming - Lesson 2", "url": "https://example.com/lesson2"}
        ],
        "session_id": "test-session-123"
    }


@pytest.fixture
def sample_course_stats() -> Dict:
    """Provide sample course statistics"""
    return {
        "total_courses": 2,
        "course_titles": ["Introduction to Programming", "Advanced Python"]
    }


# ============================================================================
# Mock Fixtures for Components
# ============================================================================

@pytest.fixture
def mock_vector_store():
    """Create a mock VectorStore for testing"""
    mock = MagicMock()
    mock.search.return_value = [
        {
            "text": "Python is a high-level programming language.",
            "metadata": {
                "course_title": "Introduction to Programming",
                "lesson_number": 1,
                "course_link": "https://example.com/course1",
                "lesson_link": "https://example.com/lesson1"
            }
        }
    ]
    mock.get_course_count.return_value = 2
    mock.get_existing_course_titles.return_value = ["Introduction to Programming", "Advanced Python"]
    return mock


@pytest.fixture
def mock_ai_generator():
    """Create a mock AIGenerator for testing"""
    mock = MagicMock()

    # Mock first generation call (tool decision)
    mock.generate.return_value = (
        "Here's the answer based on the search results.",
        "end_turn"
    )

    return mock


@pytest.fixture
def mock_tool_manager():
    """Create a mock ToolManager for testing"""
    mock = MagicMock()
    mock.get_tool_definitions.return_value = [
        {
            "name": "search_course_content",
            "description": "Search for relevant course content",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                }
            }
        }
    ]
    mock.execute_tool.return_value = "Search results..."
    return mock
