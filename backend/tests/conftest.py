"""
Shared pytest fixtures and configuration for all tests
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from ai_generator import AIGenerator
from config import config as app_config
from rag_system import RAGSystem
from search_tools import CourseSearchTool, ToolManager
from vector_store import VectorStore


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
