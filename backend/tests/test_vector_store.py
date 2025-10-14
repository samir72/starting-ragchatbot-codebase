"""
Tests for VectorStore - Verify ChromaDB data integrity and search functionality
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from vector_store import VectorStore, SearchResults
from config import config


class TestVectorStoreDataIntegrity:
    """Test that ChromaDB has data loaded correctly"""

    @pytest.fixture
    def vector_store(self):
        """Create a VectorStore instance"""
        return VectorStore(
            chroma_path=config.CHROMA_PATH,
            embedding_model=config.EMBEDDING_MODEL,
            max_results=config.MAX_RESULTS
        )

    def test_chroma_db_exists(self, vector_store):
        """Test that ChromaDB directory exists"""
        assert os.path.exists(config.CHROMA_PATH), \
            f"ChromaDB directory not found at {config.CHROMA_PATH}"

    def test_courses_loaded(self, vector_store):
        """Test that courses are loaded in the catalog"""
        course_count = vector_store.get_course_count()
        print(f"\n✓ Course count: {course_count}")
        assert course_count > 0, \
            "No courses found in vector store. Database might be empty!"

    def test_course_titles_exist(self, vector_store):
        """Test that course titles can be retrieved"""
        titles = vector_store.get_existing_course_titles()
        print(f"\n✓ Course titles found: {titles}")
        assert len(titles) > 0, \
            "No course titles found. Course catalog might be empty!"

    def test_course_content_exists(self, vector_store):
        """Test that course content collection has data"""
        # Try to get some content from the course_content collection
        try:
            results = vector_store.course_content.get(limit=1)
            has_content = results and 'ids' in results and len(results['ids']) > 0
            print(f"\n✓ Course content exists: {has_content}")
            assert has_content, \
                "Course content collection is empty. No chunks were loaded!"
        except Exception as e:
            pytest.fail(f"Failed to query course_content collection: {e}")

    def test_course_metadata_structure(self, vector_store):
        """Test that course metadata has correct structure"""
        metadata_list = vector_store.get_all_courses_metadata()
        print(f"\n✓ Retrieved {len(metadata_list)} course metadata entries")

        assert len(metadata_list) > 0, "No course metadata found"

        # Check first course has required fields
        first_course = metadata_list[0]
        print(f"\n✓ First course metadata: {first_course}")

        assert 'title' in first_course, "Course metadata missing 'title'"
        assert 'lessons' in first_course, "Course metadata missing 'lessons'"


class TestVectorStoreSearch:
    """Test VectorStore search functionality"""

    @pytest.fixture
    def vector_store(self):
        """Create a VectorStore instance"""
        return VectorStore(
            chroma_path=config.CHROMA_PATH,
            embedding_model=config.EMBEDDING_MODEL,
            max_results=config.MAX_RESULTS
        )

    def test_basic_search(self, vector_store):
        """Test basic search without filters"""
        # Search for something that should be in the course content
        results = vector_store.search(
            query="What is Claude?",
            limit=5
        )

        print(f"\n✓ Search returned {len(results.documents)} documents")
        print(f"✓ Sample document: {results.documents[0][:200] if results.documents else 'None'}...")

        assert not results.is_empty(), \
            "Search returned empty results. Content might not be properly indexed!"
        assert len(results.documents) > 0, "No documents returned from search"
        assert len(results.metadata) > 0, "No metadata returned from search"

    def test_search_with_course_filter(self, vector_store):
        """Test search with course name filter"""
        # Get a course title to search within
        titles = vector_store.get_existing_course_titles()
        if not titles:
            pytest.skip("No courses available to test filtering")

        test_course = titles[0]
        print(f"\n✓ Testing search within course: {test_course}")

        results = vector_store.search(
            query="computer use",
            course_name=test_course,
            limit=3
        )

        print(f"✓ Filtered search returned {len(results.documents)} documents")

        # Results should either have matches or return empty (not error)
        assert results.error is None, f"Search with filter failed: {results.error}"

        if not results.is_empty():
            # Verify all results are from the specified course
            for meta in results.metadata:
                assert meta.get('course_title') == test_course, \
                    f"Result from wrong course: {meta.get('course_title')}"

    def test_search_with_partial_course_name(self, vector_store):
        """Test search with partial course name (semantic matching)"""
        # Try searching with partial course name
        results = vector_store.search(
            query="Anthropic API",
            course_name="Building",  # Partial match
            limit=3
        )

        print(f"\n✓ Partial course name search returned: {len(results.documents)} docs")
        print(f"✓ Error (if any): {results.error}")

        # This should either find the course or return a "no course found" error
        if results.error:
            assert "No course found" in results.error

    def test_search_error_handling(self, vector_store):
        """Test search with invalid course name"""
        results = vector_store.search(
            query="test query",
            course_name="NonExistentCourse12345",
            limit=3
        )

        print(f"\n✓ Invalid course search error: {results.error}")

        assert results.error is not None, \
            "Should return error for non-existent course"
        assert "No course found" in results.error


class TestVectorStoreEmbeddings:
    """Test that embeddings are being generated correctly"""

    @pytest.fixture
    def vector_store(self):
        return VectorStore(
            chroma_path=config.CHROMA_PATH,
            embedding_model=config.EMBEDDING_MODEL,
            max_results=config.MAX_RESULTS
        )

    def test_embedding_function_loaded(self, vector_store):
        """Test that embedding function is properly initialized"""
        assert vector_store.embedding_function is not None, \
            "Embedding function not initialized"

    def test_embedding_model_name(self, vector_store):
        """Test that correct embedding model is configured"""
        # Check the embedding function has the right model
        assert hasattr(vector_store.embedding_function, '_model_name') or \
               hasattr(vector_store.embedding_function, 'model_name'), \
            "Embedding function missing model name attribute"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
