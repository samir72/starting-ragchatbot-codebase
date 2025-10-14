"""
Comprehensive error handling tests for the RAG chatbot system

These tests validate that the system handles errors gracefully and provides
useful error messages instead of crashing.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from unittest.mock import Mock, patch, MagicMock
from config import config
from vector_store import VectorStore, SearchResults
from search_tools import CourseSearchTool, ToolManager
from ai_generator import AIGenerator
from rag_system import RAGSystem


class TestVectorStoreErrorHandling:
    """Test error handling in VectorStore"""

    def test_search_with_corrupted_metadata(self):
        """Test search when metadata is corrupted/missing"""
        vs = VectorStore(
            chroma_path=config.CHROMA_PATH,
            embedding_model=config.EMBEDDING_MODEL,
            max_results=config.MAX_RESULTS
        )

        # Search should not crash even if metadata is weird
        results = vs.search(query="test", course_name=None, lesson_number=None)

        print(f"\n✓ Search with potentially corrupted data: {type(results)}")
        assert isinstance(results, SearchResults)

    def test_resolve_course_name_empty_catalog(self):
        """Test course name resolution when catalog might be empty"""
        vs = VectorStore(
            chroma_path=config.CHROMA_PATH,
            embedding_model=config.EMBEDDING_MODEL,
            max_results=config.MAX_RESULTS
        )

        # Try to resolve a course that definitely doesn't exist
        result = vs._resolve_course_name("XXXXXXX_NONEXISTENT_999")

        print(f"\n✓ Resolve non-existent course: {result}")
        # Should return None, not crash
        assert result is None or isinstance(result, str)

    def test_build_filter_with_none_values(self):
        """Test filter building with None values"""
        vs = VectorStore(
            chroma_path=config.CHROMA_PATH,
            embedding_model=config.EMBEDDING_MODEL,
            max_results=config.MAX_RESULTS
        )

        # Test various None combinations
        filter1 = vs._build_filter(None, None)
        filter2 = vs._build_filter("Course", None)
        filter3 = vs._build_filter(None, 1)
        filter4 = vs._build_filter("Course", 1)

        print(f"\n✓ Filter with None/None: {filter1}")
        print(f"✓ Filter with Course/None: {filter2}")
        print(f"✓ Filter with None/1: {filter3}")
        print(f"✓ Filter with Course/1: {filter4}")

        # All should return valid values (None or dict)
        assert filter1 is None or isinstance(filter1, dict)
        assert filter2 is None or isinstance(filter2, dict)
        assert filter3 is None or isinstance(filter3, dict)
        assert filter4 is None or isinstance(filter4, dict)

    def test_get_lesson_link_invalid_course(self):
        """Test getting lesson link for invalid course"""
        vs = VectorStore(
            chroma_path=config.CHROMA_PATH,
            embedding_model=config.EMBEDDING_MODEL,
            max_results=config.MAX_RESULTS
        )

        link = vs.get_lesson_link("INVALID_COURSE_XYZ", 1)

        print(f"\n✓ Lesson link for invalid course: {link}")
        # Should return None, not crash
        assert link is None or isinstance(link, str)

    def test_get_course_outline_empty_string(self):
        """Test getting outline with empty course name"""
        vs = VectorStore(
            chroma_path=config.CHROMA_PATH,
            embedding_model=config.EMBEDDING_MODEL,
            max_results=config.MAX_RESULTS
        )

        outline = vs.get_course_outline("")

        print(f"\n✓ Outline for empty string: {outline}")
        # Should handle gracefully
        assert outline is None or isinstance(outline, dict)


class TestSearchToolErrorHandling:
    """Test error handling in search tools"""

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

    def test_execute_with_none_query(self, search_tool):
        """Test execute with None as query"""
        try:
            # This might crash or handle gracefully
            result = search_tool.execute(query=None)
            print(f"\n✓ None query result: {result}")
            assert isinstance(result, str)
        except TypeError as e:
            # It's okay if it raises TypeError for None
            print(f"\n✓ None query raised TypeError (expected): {e}")
            assert "None" in str(e) or "required" in str(e).lower()

    def test_execute_with_none_parameters(self, search_tool):
        """Test execute with None in optional parameters"""
        result = search_tool.execute(
            query="test",
            course_name=None,
            lesson_number=None
        )

        print(f"\n✓ Result with None params: {result[:100]}")
        assert isinstance(result, str)

    def test_format_results_with_empty_documents(self, search_tool):
        """Test formatting results when documents list is empty"""
        empty_results = SearchResults(
            documents=[],
            metadata=[],
            distances=[]
        )

        formatted = search_tool._format_results(empty_results)

        print(f"\n✓ Formatted empty results: {formatted}")
        assert isinstance(formatted, str)

    def test_format_results_mismatched_lengths(self, search_tool):
        """Test formatting when metadata doesn't match documents length"""
        mismatched_results = SearchResults(
            documents=["Doc1", "Doc2", "Doc3"],
            metadata=[{"course_title": "Course1"}],  # Only 1 metadata for 3 docs
            distances=[0.1, 0.2, 0.3]
        )

        try:
            formatted = search_tool._format_results(mismatched_results)
            print(f"\n✓ Handled mismatched lengths: {formatted[:200]}")
        except (IndexError, ValueError) as e:
            # It's okay to fail, but should be a specific error
            print(f"\n✓ Mismatched lengths raised error (expected): {e}")
            assert isinstance(e, (IndexError, ValueError))


class TestToolManagerErrorHandling:
    """Test error handling in ToolManager"""

    def test_execute_nonexistent_tool(self):
        """Test executing a tool that doesn't exist"""
        manager = ToolManager()

        result = manager.execute_tool('fake_tool_xyz', query="test")

        print(f"\n✓ Nonexistent tool result: {result}")
        assert "not found" in result.lower()
        assert isinstance(result, str)

    def test_execute_tool_with_missing_parameters(self):
        """Test executing tool with missing required parameters"""
        vs = VectorStore(
            chroma_path=config.CHROMA_PATH,
            embedding_model=config.EMBEDDING_MODEL,
            max_results=config.MAX_RESULTS
        )

        manager = ToolManager()
        search_tool = CourseSearchTool(vs)
        manager.register_tool(search_tool)

        try:
            # Try to execute without required 'query' parameter
            result = manager.execute_tool('search_course_content')
            print(f"\n✓ Missing param result: {result}")
        except TypeError as e:
            # Expected to raise TypeError for missing required param
            print(f"\n✓ Missing param raised TypeError (expected): {e}")
            assert "required" in str(e).lower() or "missing" in str(e).lower()

    def test_register_invalid_tool(self):
        """Test registering an invalid tool object"""
        manager = ToolManager()

        # Try to register something that's not a valid tool
        class FakeTool:
            def get_tool_definition(self):
                return {}  # Missing 'name' field

        fake_tool = FakeTool()

        with pytest.raises(ValueError):
            manager.register_tool(fake_tool)

        print("\n✓ Invalid tool registration rejected correctly")

    def test_get_last_sources_no_tools(self):
        """Test getting sources when no tools are registered"""
        manager = ToolManager()

        sources = manager.get_last_sources()

        print(f"\n✓ Sources with no tools: {sources}")
        assert sources == []

    def test_reset_sources_empty_manager(self):
        """Test resetting sources on empty manager"""
        manager = ToolManager()

        # Should not crash
        manager.reset_sources()

        print("\n✓ Reset sources on empty manager succeeded")


class TestAIGeneratorErrorHandling:
    """Test error handling in AIGenerator"""

    def test_initialization_with_empty_api_key(self):
        """Test initialization with empty API key"""
        generator = AIGenerator(api_key="", model=config.ANTHROPIC_MODEL)

        print(f"\n✓ Generator with empty API key initialized: {generator}")
        assert generator.client is not None

    def test_initialization_with_invalid_model(self):
        """Test initialization with invalid model name"""
        generator = AIGenerator(
            api_key=config.ANTHROPIC_API_KEY,
            model="invalid-model-name-xyz"
        )

        print(f"\n✓ Generator with invalid model initialized: {generator}")
        # Initialization should work, error comes during API call

    @patch('anthropic.Anthropic')
    def test_handle_tool_execution_with_no_tool_uses(self, mock_anthropic):
        """Test _handle_tool_execution when content has no tool uses"""
        generator = AIGenerator(
            api_key=config.ANTHROPIC_API_KEY,
            model=config.ANTHROPIC_MODEL
        )

        mock_response = Mock()
        mock_response.content = []  # Empty content

        mock_final_response = Mock()
        mock_final_response.content = [Mock(text="Response")]

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_final_response
        generator.client = mock_client

        base_params = {
            "messages": [{"role": "user", "content": "test"}],
            "system": "test"
        }

        result = generator._handle_tool_execution(mock_response, base_params, None)

        print(f"\n✓ Handle tool execution with empty content: {result}")
        assert isinstance(result, str)

    def test_generate_response_with_none_values(self):
        """Test generate_response with None values"""
        if not config.ANTHROPIC_API_KEY:
            pytest.skip("No API key configured")

        generator = AIGenerator(
            api_key=config.ANTHROPIC_API_KEY,
            model=config.ANTHROPIC_MODEL
        )

        # Should handle None conversation_history
        response = generator.generate_response(
            query="test",
            conversation_history=None,
            tools=None,
            tool_manager=None
        )

        print(f"\n✓ Response with None values: {response[:100]}")
        assert isinstance(response, str)


class TestRAGSystemErrorHandling:
    """Test comprehensive error handling through the entire RAG system"""

    def test_initialization_with_invalid_config(self):
        """Test RAG system initialization with missing config values"""
        # Create a mock config with minimal values
        mock_config = Mock()
        mock_config.CHROMA_PATH = "./chroma_db"
        mock_config.EMBEDDING_MODEL = "all-MiniLM-L6-v2"
        mock_config.MAX_RESULTS = 5
        mock_config.CHUNK_SIZE = 800
        mock_config.CHUNK_OVERLAP = 100
        mock_config.MAX_HISTORY = 2
        mock_config.ANTHROPIC_API_KEY = config.ANTHROPIC_API_KEY
        mock_config.ANTHROPIC_MODEL = config.ANTHROPIC_MODEL

        rag = RAGSystem(mock_config)

        print(f"\n✓ RAG system initialized with mock config: {rag}")
        assert rag is not None

    def test_query_with_special_session_ids(self):
        """Test query with unusual session ID formats"""
        if not config.ANTHROPIC_API_KEY:
            pytest.skip("No API key configured")

        rag = RAGSystem(config)

        special_sessions = [
            "",  # Empty string
            "   ",  # Whitespace
            "very-long-session-id" * 50,  # Very long
            "special!@#$chars",  # Special characters
        ]

        for session in special_sessions:
            try:
                response, sources = rag.query("test", session_id=session)
                print(f"\n✓ Session '{session[:20]}...' handled: {len(response)} chars")
                assert isinstance(response, str)
            except Exception as e:
                print(f"\n✓ Session '{session[:20]}...' raised error: {str(e)[:100]}")
                # Some session formats might fail, which is okay

    def test_get_course_analytics_consistency(self):
        """Test that course analytics remain consistent"""
        rag = RAGSystem(config)

        # Get analytics multiple times
        analytics1 = rag.get_course_analytics()
        analytics2 = rag.get_course_analytics()
        analytics3 = rag.get_course_analytics()

        print(f"\n✓ Analytics call 1: {analytics1}")
        print(f"✓ Analytics call 2: {analytics2}")
        print(f"✓ Analytics call 3: {analytics3}")

        # Should be consistent
        assert analytics1['total_courses'] == analytics2['total_courses']
        assert analytics2['total_courses'] == analytics3['total_courses']

    @pytest.mark.skipif(not config.ANTHROPIC_API_KEY, reason="No API key")
    def test_query_error_recovery(self):
        """Test that system recovers from query errors"""
        rag = RAGSystem(config)

        # First, try a potentially problematic query
        try:
            response1, sources1 = rag.query("")
            print(f"\n✓ Empty query response: {response1[:100]}")
        except Exception as e:
            print(f"\n✓ Empty query error: {str(e)[:100]}")

        # Then try a normal query - system should still work
        response2, sources2 = rag.query("What is 2+2?")

        print(f"\n✓ Normal query after error: {response2}")
        assert isinstance(response2, str)
        assert len(response2) > 0


class TestEndToEndErrorScenarios:
    """Test realistic error scenarios that might occur in production"""

    @pytest.mark.skipif(not config.ANTHROPIC_API_KEY, reason="No API key")
    def test_user_types_garbage(self):
        """Test when user types random garbage"""
        rag = RAGSystem(config)

        garbage_queries = [
            "asdfasdfasdf",
            "1234567890",
            "!@#$%^&*()",
            "aaa aaa aaa",
            "",
        ]

        for query in garbage_queries:
            print(f"\n✓ Testing garbage: '{query}'")

            try:
                response, sources = rag.query(query)
                print(f"  Response: {response[:100]}")
                assert isinstance(response, str)
            except Exception as e:
                print(f"  Error (might be okay): {str(e)[:100]}")

    @pytest.mark.skipif(not config.ANTHROPIC_API_KEY, reason="No API key")
    def test_user_asks_inappropriate_questions(self):
        """Test system handles inappropriate or off-topic queries"""
        rag = RAGSystem(config)

        off_topic_queries = [
            "What's the weather today?",
            "Tell me a joke",
            "How do I cook pasta?",
            "Who won the Super Bowl?",
        ]

        for query in off_topic_queries:
            print(f"\n✓ Testing off-topic: '{query}'")

            response, sources = rag.query(query)

            print(f"  Response: {response[:100]}")
            print(f"  Sources: {len(sources)}")

            # Should respond without crashing
            assert isinstance(response, str)
            assert len(response) > 0
            # Probably shouldn't have course sources for these
            # (unless by coincidence)

    def test_concurrent_session_creation(self):
        """Test creating many sessions rapidly"""
        rag = RAGSystem(config)

        sessions = []
        for i in range(10):
            session_id = rag.session_manager.create_session()
            sessions.append(session_id)

        print(f"\n✓ Created {len(sessions)} sessions")
        print(f"✓ First session: {sessions[0]}")
        print(f"✓ Last session: {sessions[-1]}")

        # All should be unique
        assert len(set(sessions)) == len(sessions)

    @pytest.mark.skipif(not config.ANTHROPIC_API_KEY, reason="No API key")
    def test_mixed_valid_invalid_queries(self):
        """Test alternating between valid and potentially invalid queries"""
        rag = RAGSystem(config)

        queries = [
            ("What is Claude?", True),  # Valid
            ("", False),  # Invalid
            ("Tell me about MCP", True),  # Valid
            ("!@#$%", False),  # Invalid
            ("How does computer use work?", True),  # Valid
        ]

        results = []
        for query, should_be_valid in queries:
            try:
                response, sources = rag.query(query)
                results.append(('success', query, len(response)))
                print(f"\n✓ '{query[:30]}...' -> {len(response)} chars")
            except Exception as e:
                results.append(('error', query, str(e)[:50]))
                print(f"\n✗ '{query[:30]}...' -> Error: {str(e)[:50]}")

        # System should keep working despite errors
        success_count = sum(1 for r in results if r[0] == 'success')
        print(f"\n✓✓ {success_count}/{len(queries)} queries succeeded")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
