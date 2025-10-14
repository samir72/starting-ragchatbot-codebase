"""
Tests for CourseSearchTool - Verify the execute method works correctly
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from search_tools import CourseSearchTool, ToolManager
from vector_store import VectorStore, SearchResults
from config import config


class TestCourseSearchToolExecute:
    """Test CourseSearchTool.execute() method"""

    @pytest.fixture
    def vector_store(self):
        """Create a VectorStore instance"""
        return VectorStore(
            chroma_path=config.CHROMA_PATH,
            embedding_model=config.EMBEDDING_MODEL,
            max_results=config.MAX_RESULTS
        )

    @pytest.fixture
    def search_tool(self, vector_store):
        """Create a CourseSearchTool instance"""
        return CourseSearchTool(vector_store)

    def test_tool_definition(self, search_tool):
        """Test that tool definition is properly formatted"""
        tool_def = search_tool.get_tool_definition()

        print(f"\n✓ Tool definition: {tool_def}")

        assert 'name' in tool_def, "Tool definition missing 'name'"
        assert tool_def['name'] == 'search_course_content', \
            f"Expected tool name 'search_course_content', got '{tool_def['name']}'"

        assert 'description' in tool_def, "Tool definition missing 'description'"
        assert 'input_schema' in tool_def, "Tool definition missing 'input_schema'"

        # Check input schema
        schema = tool_def['input_schema']
        assert 'properties' in schema, "Input schema missing 'properties'"
        assert 'query' in schema['properties'], "Input schema missing 'query' parameter"
        assert 'required' in schema, "Input schema missing 'required' fields"
        assert 'query' in schema['required'], "'query' should be required"

    def test_execute_basic_search(self, search_tool):
        """Test basic execute with just a query"""
        result = search_tool.execute(query="What is Claude?")

        print(f"\n✓ Execute result type: {type(result)}")
        print(f"✓ Execute result (first 300 chars): {result[:300]}...")

        assert isinstance(result, str), \
            f"execute() should return string, got {type(result)}"
        assert len(result) > 0, "execute() returned empty string"

        # Should not return error messages for valid queries
        assert "No relevant content found" not in result or "error" not in result.lower(), \
            f"Search failed with error: {result}"

    def test_execute_with_course_filter(self, search_tool, vector_store):
        """Test execute with course_name parameter"""
        # Get a valid course title
        titles = vector_store.get_existing_course_titles()
        if not titles:
            pytest.skip("No courses available for testing")

        test_course = titles[0]
        print(f"\n✓ Testing with course: {test_course}")

        result = search_tool.execute(
            query="API requests",
            course_name=test_course
        )

        print(f"✓ Filtered search result (first 300 chars): {result[:300]}...")

        assert isinstance(result, str), "execute() should return string"

        # Should either have results or a "no content found" message (not an error)
        if "No relevant content found" in result:
            print(f"✓ No content found (expected if query doesn't match course)")
        else:
            # Should contain the course title in the results
            assert test_course in result, \
                f"Results should mention course '{test_course}'"

    def test_execute_with_lesson_filter(self, search_tool):
        """Test execute with lesson_number parameter"""
        result = search_tool.execute(
            query="introduction",
            lesson_number=0
        )

        print(f"\n✓ Lesson-filtered result (first 300 chars): {result[:300]}...")

        assert isinstance(result, str), "execute() should return string"
        # Should either have results or "no content found"
        assert "error" not in result.lower() or "No relevant content found" in result

    def test_execute_nonexistent_course(self, search_tool):
        """Test execute with non-existent course name"""
        result = search_tool.execute(
            query="test",
            course_name="NonExistentCourse12345"
        )

        print(f"\n✓ Non-existent course result: {result}")

        assert isinstance(result, str), "execute() should return string"
        assert "No course found" in result or "No relevant content found" in result, \
            "Should return error message for non-existent course"

    def test_execute_empty_query(self, search_tool):
        """Test execute with empty query string"""
        result = search_tool.execute(query="")

        print(f"\n✓ Empty query result: {result}")

        # Should handle empty query gracefully (might return results or error)
        assert isinstance(result, str), "execute() should return string"

    def test_execute_tracks_sources(self, search_tool):
        """Test that execute() properly tracks sources"""
        # Clear any previous sources
        search_tool.last_sources = []

        result = search_tool.execute(query="What is Anthropic?")

        print(f"\n✓ Execute completed, checking sources...")
        print(f"✓ last_sources: {search_tool.last_sources}")

        # If search found results, sources should be populated
        if "No relevant content found" not in result:
            assert len(search_tool.last_sources) > 0, \
                "last_sources should be populated after successful search"

            # Check source structure
            first_source = search_tool.last_sources[0]
            assert isinstance(first_source, dict), \
                f"Source should be dict, got {type(first_source)}"
            assert 'text' in first_source, "Source missing 'text' field"
            assert 'url' in first_source, "Source missing 'url' field"

    def test_format_results(self, search_tool, vector_store):
        """Test the _format_results method"""
        # Create mock SearchResults
        mock_results = SearchResults(
            documents=["Sample content about Claude"],
            metadata=[{
                'course_title': 'Test Course',
                'lesson_number': 1
            }],
            distances=[0.5]
        )

        formatted = search_tool._format_results(mock_results)

        print(f"\n✓ Formatted result: {formatted}")

        assert isinstance(formatted, str), "Formatted result should be string"
        assert "Test Course" in formatted, "Should contain course title"
        assert "Lesson 1" in formatted, "Should contain lesson number"
        assert "Sample content" in formatted, "Should contain document content"


class TestToolManager:
    """Test ToolManager functionality"""

    @pytest.fixture
    def vector_store(self):
        return VectorStore(
            chroma_path=config.CHROMA_PATH,
            embedding_model=config.EMBEDDING_MODEL,
            max_results=config.MAX_RESULTS
        )

    @pytest.fixture
    def tool_manager(self, vector_store):
        """Create ToolManager with registered CourseSearchTool"""
        manager = ToolManager()
        search_tool = CourseSearchTool(vector_store)
        manager.register_tool(search_tool)
        return manager

    def test_tool_registration(self, tool_manager):
        """Test that tool is registered correctly"""
        assert 'search_course_content' in tool_manager.tools, \
            "CourseSearchTool not registered in ToolManager"

    def test_get_tool_definitions(self, tool_manager):
        """Test getting tool definitions"""
        definitions = tool_manager.get_tool_definitions()

        print(f"\n✓ Tool definitions: {definitions}")

        assert isinstance(definitions, list), "Should return list"
        assert len(definitions) == 1, "Should have 1 tool registered"
        assert definitions[0]['name'] == 'search_course_content'

    def test_execute_tool(self, tool_manager):
        """Test executing a tool through ToolManager"""
        result = tool_manager.execute_tool(
            'search_course_content',
            query="What is Claude?"
        )

        print(f"\n✓ ToolManager execute result (first 300 chars): {result[:300]}...")

        assert isinstance(result, str), "Should return string"
        assert len(result) > 0, "Should return non-empty result"

    def test_execute_nonexistent_tool(self, tool_manager):
        """Test executing a non-existent tool"""
        result = tool_manager.execute_tool(
            'nonexistent_tool',
            query="test"
        )

        print(f"\n✓ Non-existent tool result: {result}")

        assert "not found" in result.lower(), \
            "Should return error for non-existent tool"

    def test_get_last_sources(self, tool_manager):
        """Test retrieving last sources from ToolManager"""
        # Execute a search
        tool_manager.execute_tool(
            'search_course_content',
            query="Anthropic models"
        )

        sources = tool_manager.get_last_sources()

        print(f"\n✓ Retrieved sources: {sources}")

        # If search succeeded, should have sources
        if sources:
            assert isinstance(sources, list), "Should return list"
            assert all(isinstance(s, dict) for s in sources), \
                "All sources should be dicts"

    def test_reset_sources(self, tool_manager):
        """Test resetting sources"""
        # Execute a search to populate sources
        tool_manager.execute_tool(
            'search_course_content',
            query="Claude API"
        )

        # Reset sources
        tool_manager.reset_sources()

        sources = tool_manager.get_last_sources()

        print(f"\n✓ Sources after reset: {sources}")

        assert sources == [], "Sources should be empty after reset"


class TestCourseSearchToolEdgeCases:
    """Test edge cases and error scenarios for CourseSearchTool"""

    @pytest.fixture
    def vector_store(self):
        return VectorStore(
            chroma_path=config.CHROMA_PATH,
            embedding_model=config.EMBEDDING_MODEL,
            max_results=config.MAX_RESULTS
        )

    @pytest.fixture
    def search_tool(self, vector_store):
        return CourseSearchTool(vector_store)

    def test_execute_very_long_query(self, search_tool):
        """Test execute with extremely long query"""
        long_query = "What is Claude? " * 200  # 3600+ characters

        print(f"\n✓ Long query length: {len(long_query)} chars")

        result = search_tool.execute(query=long_query)

        print(f"✓ Result type: {type(result)}")
        print(f"✓ Result length: {len(result)}")

        assert isinstance(result, str), "Should return string even for long query"
        # Should handle long query without crashing
        assert len(result) > 0, "Should return some result"

    def test_execute_special_characters(self, search_tool):
        """Test execute with special characters in query"""
        special_queries = [
            "What is Claude?!@#$%^&*()",
            "Tell me about <script>alert('test')</script>",
            "Claude's API & SDK's features",
            "Line1\nLine2\tTabbed"
        ]

        for query in special_queries:
            print(f"\n✓ Testing special char query: {query[:50]}...")
            result = search_tool.execute(query=query)

            assert isinstance(result, str), f"Should handle special chars: {query}"
            assert len(result) > 0, "Should return some result"

    def test_execute_unicode_query(self, search_tool):
        """Test execute with unicode characters"""
        unicode_queries = [
            "¿Qué es Claude?",
            "Claude是什么？",
            "Что такое Claude?",
            "🤖 What is AI? 🚀"
        ]

        for query in unicode_queries:
            print(f"\n✓ Testing unicode query: {query}")
            result = search_tool.execute(query=query)

            assert isinstance(result, str), f"Should handle unicode: {query}"

    def test_execute_sql_injection_attempt(self, search_tool):
        """Test that SQL injection patterns are safely handled"""
        sql_patterns = [
            "'; DROP TABLE courses; --",
            "1' OR '1'='1",
            "' UNION SELECT * FROM users --"
        ]

        for pattern in sql_patterns:
            print(f"\n✓ Testing SQL pattern: {pattern}")
            result = search_tool.execute(query=pattern)

            # Should safely handle as a text query, not SQL
            assert isinstance(result, str), "Should treat as text, not SQL"
            # Should not crash or expose database structure
            assert "DROP TABLE" not in result, "Should not execute SQL"

    def test_execute_multiple_filters_no_results(self, search_tool):
        """Test execute with filters that yield no results"""
        result = search_tool.execute(
            query="nonexistent topic xyz123",
            course_name="NonexistentCourse999",
            lesson_number=9999
        )

        print(f"\n✓ No results scenario: {result}")

        assert isinstance(result, str), "Should return string"
        assert "No" in result or "not found" in result.lower(), \
            "Should indicate no results found"

    def test_execute_negative_lesson_number(self, search_tool):
        """Test execute with negative lesson number"""
        result = search_tool.execute(
            query="test",
            lesson_number=-1
        )

        print(f"\n✓ Negative lesson result: {result}")

        assert isinstance(result, str), "Should handle negative lesson number"

    def test_execute_very_large_lesson_number(self, search_tool):
        """Test execute with extremely large lesson number"""
        result = search_tool.execute(
            query="test",
            lesson_number=99999
        )

        print(f"\n✓ Large lesson number result: {result}")

        assert isinstance(result, str), "Should handle large lesson number"

    def test_format_results_empty_metadata(self, search_tool):
        """Test _format_results with incomplete metadata"""
        mock_results = SearchResults(
            documents=["Content without full metadata"],
            metadata=[{}],  # Empty metadata
            distances=[0.5]
        )

        formatted = search_tool._format_results(mock_results)

        print(f"\n✓ Formatted with empty metadata: {formatted}")

        assert isinstance(formatted, str), "Should handle empty metadata"
        assert "Content without full metadata" in formatted, "Should include content"

    def test_format_results_missing_lesson_number(self, search_tool):
        """Test _format_results with missing lesson_number"""
        mock_results = SearchResults(
            documents=["Content from course"],
            metadata=[{
                'course_title': 'Test Course',
                # lesson_number is missing
            }],
            distances=[0.5]
        )

        formatted = search_tool._format_results(mock_results)

        print(f"\n✓ Formatted without lesson number: {formatted}")

        assert isinstance(formatted, str), "Should handle missing lesson_number"
        assert "Test Course" in formatted, "Should include course title"

    def test_sources_structure_consistency(self, search_tool):
        """Test that sources always have consistent structure"""
        search_tool.last_sources = []

        result = search_tool.execute(query="Claude API")

        if search_tool.last_sources:
            print(f"\n✓ Checking {len(search_tool.last_sources)} sources for consistency")

            for i, source in enumerate(search_tool.last_sources):
                print(f"  Source {i+1}: {source}")

                assert isinstance(source, dict), f"Source {i} should be dict"
                assert 'text' in source, f"Source {i} missing 'text' field"
                assert 'url' in source, f"Source {i} missing 'url' field"
                assert isinstance(source['text'], str), f"Source {i} 'text' should be string"
                assert isinstance(source['url'], str), f"Source {i} 'url' should be string"


class TestCourseSearchToolPerformance:
    """Test performance characteristics of CourseSearchTool"""

    @pytest.fixture
    def vector_store(self):
        return VectorStore(
            chroma_path=config.CHROMA_PATH,
            embedding_model=config.EMBEDDING_MODEL,
            max_results=config.MAX_RESULTS
        )

    @pytest.fixture
    def search_tool(self, vector_store):
        return CourseSearchTool(vector_store)

    def test_search_performance_baseline(self, search_tool):
        """Benchmark basic search performance"""
        import time

        queries = [
            "What is Claude?",
            "How does tool use work?",
            "Tell me about MCP",
            "Computer use with Anthropic",
            "Prompt caching features"
        ]

        times = []
        for query in queries:
            start = time.time()
            result = search_tool.execute(query=query)
            elapsed = time.time() - start
            times.append(elapsed)

            print(f"\n✓ Query: {query[:40]}")
            print(f"  Time: {elapsed:.3f}s")
            print(f"  Result length: {len(result)} chars")

        avg_time = sum(times) / len(times)
        print(f"\n✓✓ Average search time: {avg_time:.3f}s")
        print(f"✓✓ Min: {min(times):.3f}s, Max: {max(times):.3f}s")

        # Performance assertion - should be reasonably fast
        assert avg_time < 5.0, f"Average search time {avg_time:.3f}s exceeds 5s threshold"

    def test_concurrent_searches(self, search_tool):
        """Test that tool handles rapid successive searches"""
        queries = [
            "Claude",
            "API",
            "MCP",
            "Computer use",
            "Tools"
        ]

        results = []
        for query in queries:
            result = search_tool.execute(query=query)
            results.append(result)

        print(f"\n✓ Completed {len(results)} rapid searches")

        # All should succeed
        assert all(isinstance(r, str) and len(r) > 0 for r in results), \
            "All rapid searches should succeed"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
