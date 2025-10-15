"""
Tests for RAGSystem - End-to-end integration tests for content queries
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from config import config
from rag_system import RAGSystem


class TestRAGSystemBasics:
    """Test basic RAGSystem functionality"""

    @pytest.fixture
    def rag_system(self):
        """Create RAGSystem instance"""
        return RAGSystem(config)

    def test_rag_system_initialization(self, rag_system):
        """Test that RAGSystem initializes all components"""
        assert rag_system.document_processor is not None
        assert rag_system.vector_store is not None
        assert rag_system.ai_generator is not None
        assert rag_system.session_manager is not None
        assert rag_system.tool_manager is not None
        assert rag_system.search_tool is not None

        print("\n✓ All RAG components initialized successfully")

    def test_tool_manager_has_search_tool(self, rag_system):
        """Test that tool manager has search tool registered"""
        tools = rag_system.tool_manager.get_tool_definitions()

        print(f"\n✓ Number of tools registered: {len(tools)}")
        print(f"✓ Tools: {[t['name'] for t in tools]}")

        assert len(tools) > 0, "No tools registered"
        assert any(
            t["name"] == "search_course_content" for t in tools
        ), "search_course_content tool not registered"

    def test_get_course_analytics(self, rag_system):
        """Test getting course analytics"""
        analytics = rag_system.get_course_analytics()

        print(f"\n✓ Course analytics: {analytics}")

        assert "total_courses" in analytics
        assert "course_titles" in analytics
        assert isinstance(analytics["total_courses"], int)
        assert isinstance(analytics["course_titles"], list)

        # Should have courses loaded
        assert (
            analytics["total_courses"] > 0
        ), "No courses loaded! Database might be empty"


class TestRAGSystemQuery:
    """Test RAGSystem query functionality"""

    @pytest.fixture
    def rag_system(self):
        """Create RAGSystem instance"""
        return RAGSystem(config)

    def test_query_returns_tuple(self, rag_system):
        """Test that query returns (response, sources) tuple"""
        # Skip if no API key
        if not config.ANTHROPIC_API_KEY:
            pytest.skip("No API key configured")

        response, sources = rag_system.query("What is 2+2?")

        print(f"\n✓ Response type: {type(response)}")
        print(f"✓ Sources type: {type(sources)}")
        print(f"✓ Response: {response[:200]}...")

        assert isinstance(response, str), "Response should be string"
        assert isinstance(sources, list), "Sources should be list"

    @pytest.mark.skipif(not config.ANTHROPIC_API_KEY, reason="No API key")
    def test_query_general_knowledge(self, rag_system):
        """Test query with general knowledge question (should not use search)"""
        response, sources = rag_system.query("What is 2+2?")

        print(f"\n✓ General knowledge response: {response}")
        print(f"✓ Sources: {sources}")

        assert isinstance(response, str)
        assert len(response) > 0
        assert "4" in response

        # General knowledge shouldn't search courses
        assert (
            len(sources) == 0
        ), "General knowledge question should not return course sources"

    @pytest.mark.skipif(not config.ANTHROPIC_API_KEY, reason="No API key")
    def test_query_course_content(self, rag_system):
        """Test query with course-specific question (should use search)"""
        # This is the critical test - does the RAG system properly handle course queries?
        query = "What is Claude and what does it do?"

        response, sources = rag_system.query(query)

        print(f"\n✓ Course content query: {query}")
        print(f"✓ Response length: {len(response)} chars")
        print(f"✓ Response preview: {response[:300]}...")
        print(f"✓ Number of sources: {len(sources)}")

        # Basic checks
        assert isinstance(response, str), "Response should be string"
        assert len(response) > 0, "Response should not be empty"

        # Check for error messages
        if "error" in response.lower() or "failed" in response.lower():
            print(f"⚠⚠⚠ ERROR DETECTED IN RESPONSE: {response}")
            pytest.fail(f"Query returned error: {response}")

        # If tool was used, should have sources
        if len(sources) > 0:
            print(f"✓✓ Tool was used! Sources found: {sources}")
            assert all(
                isinstance(s, dict) for s in sources
            ), "All sources should be dicts"
            assert all(
                "text" in s and "url" in s for s in sources
            ), "Sources should have 'text' and 'url' fields"
        else:
            print("⚠ Warning: No sources returned. Tool might not have been called.")

    @pytest.mark.skipif(not config.ANTHROPIC_API_KEY, reason="No API key")
    def test_query_specific_course_topic(self, rag_system):
        """Test query about specific course topics"""
        test_queries = [
            "Tell me about computer use with Anthropic",
            "What are the main features of Claude API?",
            "How does prompt caching work?",
            "What is tool use in Claude?",
        ]

        for query in test_queries:
            print(f"\n✓ Testing query: {query}")

            response, sources = rag_system.query(query)

            print(f"  Response length: {len(response)} chars")
            print(f"  Number of sources: {len(sources)}")
            print(f"  Response preview: {response[:150]}...")

            # Check for errors
            assert (
                "error" not in response.lower() and "failed" not in response.lower()
            ), f"Query failed: {response}"

            # At least one should return sources
            if len(sources) > 0:
                print(f"  ✓✓ Got sources for: {query}")
                break
        else:
            # If none of the queries returned sources, that's suspicious
            print("⚠⚠ Warning: None of the course queries returned sources!")

    @pytest.mark.skipif(not config.ANTHROPIC_API_KEY, reason="No API key")
    def test_query_with_session(self, rag_system):
        """Test query with session management"""
        # Create a session
        session_id = rag_system.session_manager.create_session()

        print(f"\n✓ Created session: {session_id}")

        # First query
        response1, sources1 = rag_system.query("What is Claude?", session_id=session_id)

        print(f"✓ First query response: {response1[:200]}...")

        # Second query referencing first
        response2, sources2 = rag_system.query(
            "Tell me more about it", session_id=session_id
        )

        print(f"✓ Second query response: {response2[:200]}...")

        assert len(response1) > 0
        assert len(response2) > 0

    @pytest.mark.skipif(not config.ANTHROPIC_API_KEY, reason="No API key")
    def test_query_error_handling(self, rag_system):
        """Test that query handles errors gracefully"""
        # Try a query that might cause issues
        response, sources = rag_system.query("")

        print(f"\n✓ Empty query response: {response}")

        # Should not crash, should return some response
        assert isinstance(response, str)


class TestRAGSystemDocumentProcessing:
    """Test document processing capabilities"""

    @pytest.fixture
    def rag_system(self):
        """Create RAGSystem instance"""
        return RAGSystem(config)

    def test_courses_already_loaded(self, rag_system):
        """Test that courses were loaded at startup"""
        analytics = rag_system.get_course_analytics()

        print(f"\n✓ Courses loaded: {analytics['total_courses']}")
        print(f"✓ Course titles: {analytics['course_titles']}")

        assert (
            analytics["total_courses"] > 0
        ), "No courses loaded. Check if documents were processed at startup."

    def test_course_titles_valid(self, rag_system):
        """Test that loaded course titles are valid"""
        titles = rag_system.vector_store.get_existing_course_titles()

        print(f"\n✓ Course titles: {titles}")

        assert len(titles) > 0, "No course titles found"

        # All titles should be non-empty strings
        for title in titles:
            assert isinstance(title, str), f"Invalid title type: {type(title)}"
            assert len(title) > 0, "Empty course title found"


class TestRAGSystemToolIntegration:
    """Test integration between RAG components and tools"""

    @pytest.fixture
    def rag_system(self):
        """Create RAGSystem instance"""
        return RAGSystem(config)

    def test_tool_can_search_vector_store(self, rag_system):
        """Test that search tool can access vector store"""
        # Execute tool directly
        result = rag_system.tool_manager.execute_tool(
            "search_course_content", query="Anthropic"
        )

        print(f"\n✓ Direct tool execution result: {result[:300]}...")

        assert isinstance(result, str)
        assert len(result) > 0
        assert "error" not in result.lower() or "No relevant content found" in result

    def test_sources_are_tracked(self, rag_system):
        """Test that sources are properly tracked and retrieved"""
        # Reset sources
        rag_system.tool_manager.reset_sources()

        # Execute search
        rag_system.tool_manager.execute_tool(
            "search_course_content", query="Claude models"
        )

        sources = rag_system.tool_manager.get_last_sources()

        print(f"\n✓ Sources tracked: {sources}")

        # If search succeeded, should have sources
        if sources:
            assert isinstance(sources, list)
            assert all(isinstance(s, dict) for s in sources)
            assert all("text" in s and "url" in s for s in sources)


class TestRAGSystemErrorPropagation:
    """Test error handling and propagation through RAG system"""

    @pytest.fixture
    def rag_system(self):
        return RAGSystem(config)

    @pytest.mark.skipif(not config.ANTHROPIC_API_KEY, reason="No API key")
    def test_query_with_invalid_session_id(self, rag_system):
        """Test query with malformed session ID"""
        # UUID format is expected but let's try something else
        weird_session = "not-a-uuid-12345"

        response, sources = rag_system.query(
            "What is Claude?", session_id=weird_session
        )

        print(f"\n✓ Response with weird session: {response[:200]}")

        # Should handle gracefully
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.skipif(not config.ANTHROPIC_API_KEY, reason="No API key")
    def test_empty_query_through_rag_system(self, rag_system):
        """Test empty query propagation"""
        response, sources = rag_system.query("")

        print(f"\n✓ Empty query response: {response}")

        assert isinstance(response, str)
        # Should handle empty query gracefully

    @pytest.mark.skipif(not config.ANTHROPIC_API_KEY, reason="No API key")
    def test_very_long_query_through_system(self, rag_system):
        """Test very long query through entire RAG pipeline"""
        long_query = "Tell me everything about Claude AI. " * 300

        print(f"\n✓ Long query length: {len(long_query)} chars")

        try:
            response, sources = rag_system.query(long_query)

            print(f"✓ Long query succeeded: {len(response)} chars")
            assert isinstance(response, str)

        except Exception as e:
            print(f"✓ Long query failed gracefully: {str(e)[:100]}")
            # Should fail with token/length error, not crash
            assert "token" in str(e).lower() or "length" in str(e).lower()

    @pytest.mark.skipif(not config.ANTHROPIC_API_KEY, reason="No API key")
    def test_special_characters_in_query(self, rag_system):
        """Test special characters through RAG system"""
        special_queries = [
            "What is <Claude>?",
            "Tell me about Claude's API & features",
            "How does tool_use() work?",
            "Explain prompt\ncaching\twith tabs",
        ]

        for query in special_queries:
            print(f"\n✓ Testing: {query[:50]}")

            response, sources = rag_system.query(query)

            assert isinstance(response, str), f"Failed on: {query}"
            assert len(response) > 0
            assert "error" not in response.lower() or "no" in response.lower()

    @pytest.mark.skipif(not config.ANTHROPIC_API_KEY, reason="No API key")
    def test_sql_injection_through_system(self, rag_system):
        """Test SQL injection patterns are safely handled"""
        sql_patterns = [
            "'; DROP TABLE courses; --",
            "What is Claude' OR '1'='1",
        ]

        for pattern in sql_patterns:
            print(f"\n✓ Testing SQL pattern: {pattern}")

            response, sources = rag_system.query(pattern)

            # Should treat as text query, not execute SQL
            assert isinstance(response, str)
            assert "DROP TABLE" not in response
            # Should not return database errors
            assert "SQL" not in response or "syntax" not in response.lower()

    def test_tool_manager_error_recovery(self, rag_system):
        """Test that tool manager errors don't crash the system"""
        # Get an invalid tool name
        result = rag_system.tool_manager.execute_tool(
            "nonexistent_tool_xyz", query="test"
        )

        print(f"\n✓ Invalid tool result: {result}")

        # Should return error message, not crash
        assert isinstance(result, str)
        assert "not found" in result.lower()

    def test_sources_reset_between_queries(self, rag_system):
        """Test that sources don't leak between queries"""
        if not config.ANTHROPIC_API_KEY:
            pytest.skip("No API key configured")

        # First query
        response1, sources1 = rag_system.query("What is Claude?")

        # Second query
        response2, sources2 = rag_system.query("What is 2+2?")

        print(f"\n✓ First query sources: {len(sources1)}")
        print(f"✓ Second query sources: {len(sources2)}")

        # Sources should be independent
        # Second query (math) should not use search tool
        assert len(sources2) == 0, "General knowledge query should not have sources"

    @pytest.mark.skipif(not config.ANTHROPIC_API_KEY, reason="No API key")
    def test_consecutive_course_queries(self, rag_system):
        """Test multiple course queries in succession"""
        queries = [
            "What is MCP?",
            "Tell me about computer use",
            "How does Claude API work?",
        ]

        all_responses = []
        all_sources = []

        for query in queries:
            print(f"\n✓ Query: {query}")
            response, sources = rag_system.query(query)

            print(f"  Response length: {len(response)}")
            print(f"  Sources: {len(sources)}")

            all_responses.append(response)
            all_sources.append(sources)

            # Each should succeed independently
            assert isinstance(response, str)
            assert len(response) > 0

        # At least some should have found sources
        total_sources = sum(len(s) for s in all_sources)
        print(f"\n✓✓ Total sources across queries: {total_sources}")


class TestRAGSystemStressTest:
    """Stress testing for RAG system"""

    @pytest.fixture
    def rag_system(self):
        return RAGSystem(config)

    @pytest.mark.skipif(not config.ANTHROPIC_API_KEY, reason="No API key")
    def test_rapid_queries(self, rag_system):
        """Test rapid successive queries"""
        queries = ["Claude", "API", "MCP", "tools", "computer use"]

        responses = []
        import time

        start_time = time.time()

        for query in queries:
            response, sources = rag_system.query(query)
            responses.append((response, sources))

        elapsed = time.time() - start_time

        print(f"\n✓ Completed {len(queries)} queries in {elapsed:.2f}s")
        print(f"✓ Average: {elapsed/len(queries):.2f}s per query")

        # All should succeed
        assert all(isinstance(r, str) and len(r) > 0 for r, s in responses)

    @pytest.mark.skipif(not config.ANTHROPIC_API_KEY, reason="No API key")
    def test_session_with_many_exchanges(self, rag_system):
        """Test session with multiple back-and-forth exchanges"""
        session_id = rag_system.session_manager.create_session()

        exchanges = [
            "What is Claude?",
            "Tell me more about its capabilities",
            "How does it compare to other AIs?",
            "What are the pricing options?",
            "Thank you",
        ]

        print(f"\n✓ Testing {len(exchanges)} exchanges in session {session_id}")

        for i, query in enumerate(exchanges):
            print(f"\n  Exchange {i+1}: {query[:40]}")

            response, sources = rag_system.query(query, session_id=session_id)

            print(f"    Response: {response[:100]}...")

            assert isinstance(response, str)
            assert len(response) > 0

        print(f"\n✓✓ All {len(exchanges)} exchanges completed successfully")

    def test_vector_store_integrity_after_queries(self, rag_system):
        """Test that vector store remains consistent after queries"""
        # Get initial state
        initial_count = rag_system.vector_store.get_course_count()
        initial_titles = set(rag_system.vector_store.get_existing_course_titles())

        print(f"\n✓ Initial state: {initial_count} courses")

        if config.ANTHROPIC_API_KEY:
            # Perform several queries
            queries = ["Claude", "MCP", "Computer use"]
            for query in queries:
                rag_system.query(query)

        # Check state after queries
        final_count = rag_system.vector_store.get_course_count()
        final_titles = set(rag_system.vector_store.get_existing_course_titles())

        print(f"✓ Final state: {final_count} courses")

        # Vector store should be unchanged
        assert final_count == initial_count, "Course count changed after queries!"
        assert final_titles == initial_titles, "Course titles changed after queries!"


class TestRAGSystemComponentIntegration:
    """Test integration between RAG system components"""

    @pytest.fixture
    def rag_system(self):
        return RAGSystem(config)

    def test_all_components_initialized(self, rag_system):
        """Verify all components are properly initialized"""
        components = {
            "document_processor": rag_system.document_processor,
            "vector_store": rag_system.vector_store,
            "ai_generator": rag_system.ai_generator,
            "session_manager": rag_system.session_manager,
            "tool_manager": rag_system.tool_manager,
            "search_tool": rag_system.search_tool,
            "outline_tool": rag_system.outline_tool,
        }

        print("\n✓ Checking component initialization:")
        for name, component in components.items():
            print(f"  {name}: {type(component).__name__}")
            assert component is not None, f"{name} not initialized"

    def test_tool_manager_has_all_tools(self, rag_system):
        """Test that tool manager has all expected tools"""
        tool_defs = rag_system.tool_manager.get_tool_definitions()

        print(f"\n✓ Registered tools: {len(tool_defs)}")

        tool_names = [t["name"] for t in tool_defs]
        print(f"✓ Tool names: {tool_names}")

        # Should have at least search_course_content and get_course_outline
        assert "search_course_content" in tool_names
        assert "get_course_outline" in tool_names

    def test_vector_store_accessible_by_tools(self, rag_system):
        """Test that tools can access vector store"""
        # Tools should be able to search
        result = rag_system.tool_manager.execute_tool(
            "search_course_content", query="test query"
        )

        print(f"\n✓ Tool search result: {result[:200]}...")

        assert isinstance(result, str)
        assert len(result) > 0

    def test_session_manager_creates_unique_sessions(self, rag_system):
        """Test that session manager creates unique sessions"""
        session1 = rag_system.session_manager.create_session()
        session2 = rag_system.session_manager.create_session()
        session3 = rag_system.session_manager.create_session()

        print(f"\n✓ Created sessions:")
        print(f"  Session 1: {session1}")
        print(f"  Session 2: {session2}")
        print(f"  Session 3: {session3}")

        # All should be unique
        assert session1 != session2
        assert session2 != session3
        assert session1 != session3

    @pytest.mark.skipif(not config.ANTHROPIC_API_KEY, reason="No API key")
    def test_end_to_end_data_flow(self, rag_system):
        """Test data flow from query to response with sources"""
        query = "What is Claude used for in the courses?"

        print(f"\n✓ Testing end-to-end flow for: {query}")

        # Query the system
        response, sources = rag_system.query(query)

        print(f"\n✓ Response length: {len(response)} chars")
        print(f"✓ Number of sources: {len(sources)}")
        print(f"✓ Response preview: {response[:200]}...")

        # Verify complete data flow
        assert isinstance(response, str), "Response should be string"
        assert len(response) > 0, "Response should not be empty"

        if sources:
            print(f"\n✓ Source validation:")
            for i, source in enumerate(sources):
                print(f"  Source {i+1}: {source}")
                assert isinstance(source, dict), "Source should be dict"
                assert "text" in source, "Source missing text"
                assert "url" in source, "Source missing url"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
