# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Setup

**Install dependencies:**
```bash
uv sync
```

**Run the application:**
```bash
chmod +x run.sh
./run.sh
```

Or manually:
```bash
cd backend && uv run uvicorn app:app --reload --port 8000
```

**Environment setup:**
Create `.env` in root with:
```
ANTHROPIC_API_KEY=your_key_here
```

## Code Quality Tools

This project uses several code quality tools to maintain consistent code style and catch issues early:

**Tools included:**
- **black** - Automatic code formatting (88 character line length)
- **isort** - Import sorting (configured to work with black)
- **flake8** - Linting and style checking
- **mypy** - Static type checking
- **pytest** - Testing framework

**Quick commands:**

Format code:
```bash
./scripts/format.sh
```

Run linting:
```bash
./scripts/lint.sh
```

Run tests:
```bash
./scripts/test.sh
```

Run all quality checks:
```bash
./scripts/quality.sh
```

**Manual usage:**
```bash
# Format code
uv run black backend/
uv run isort backend/

# Check code quality
uv run flake8 backend/
uv run mypy backend/

# Run tests
cd backend && uv run pytest
```

**Configuration files:**
- `pyproject.toml` - Contains configuration for black, isort, mypy, and pytest
- `.flake8` - Configuration for flake8 linting rules

## Architecture Overview

This is a **Retrieval-Augmented Generation (RAG) system** for querying course materials. The architecture follows a **two-stage AI generation pattern** with tool-based search.

### Request Flow (2-Stage Pattern)

1. **Frontend** → User submits query via `/api/query` endpoint
2. **RAGSystem** → Orchestrates the entire flow
3. **First Claude API call** → Claude analyzes query and decides whether to use `search_course_content` tool
4. **Tool execution** (if Claude requests it):
   - VectorStore generates query embedding (384-dim vector via `all-MiniLM-L6-v2`)
   - ChromaDB performs cosine similarity search
   - Returns top 5 relevant chunks
5. **Second Claude API call** → Claude synthesizes final answer using tool results
6. **Response** → Returns answer + source attribution to frontend

### Core Components

**backend/rag_system.py** - Central orchestrator
- Coordinates all components
- Manages query lifecycle
- Handles session state via SessionManager (stores last 2 exchanges)

**backend/ai_generator.py** - Claude API wrapper
- Implements two-stage generation pattern
- First call: Tool decision (`stop_reason: "tool_use"`)
- Second call: Final synthesis (`stop_reason: "end_turn"`)
- System prompt defines strict tool usage rules (max 1 search per query)

**backend/vector_store.py** - ChromaDB interface
- Two collections: `course_catalog` (metadata), `course_content` (chunks)
- Embedding model: `all-MiniLM-L6-v2` (384 dimensions)
- Search supports filters: `course_name`, `lesson_number`

**backend/search_tools.py** - Tool definitions and execution
- `CourseSearchTool` - Implements `search_course_content` tool
- `ToolManager` - Registers tools and routes execution
- Formats results with headers: `[Course Title - Lesson N]`
- Tracks sources for attribution

**backend/document_processor.py** - Document parsing and chunking
- Parses course documents with regex patterns for metadata
- Chunks text using **sentence-based splitting**:
  - Chunk size: 800 characters
  - Overlap: 100 characters (preserves context)
- Creates `CourseChunk` objects with metadata

**backend/app.py** - FastAPI server
- Endpoint: `POST /api/query` → Main query interface
- Endpoint: `GET /api/courses` → Course statistics
- Startup event: Auto-loads documents from `docs/` folder
- Serves static frontend from `frontend/` directory

**backend/session_manager.py** - Conversation state
- UUID-based session tracking
- Stores last `MAX_HISTORY=2` exchanges per session
- Provides conversation context to Claude

### Key Configuration (backend/config.py)

```python
ANTHROPIC_MODEL: "claude-sonnet-4-20250514"
EMBEDDING_MODEL: "all-MiniLM-L6-v2"
CHUNK_SIZE: 800           # Text chunk size
CHUNK_OVERLAP: 100        # Overlap between chunks
MAX_RESULTS: 5            # Top-k search results
MAX_HISTORY: 2            # Conversation exchanges to remember
CHROMA_PATH: "./chroma_db"  # Vector DB location
```

## Document Processing

**Adding new course documents:**

Course documents must follow this format at the top:
```
Course Title: Your Course Name
Course Link: https://...
Course Instructor: Name

Lesson 0: Introduction
Lesson Link: https://...
[Content...]

Lesson 1: Title
...
```

Place `.txt`, `.pdf`, or `.docx` files in `docs/` folder - they're auto-loaded on startup.

To manually rebuild the vector database:
```python
# In backend/ directory
from rag_system import RAGSystem
from config import config

rag = RAGSystem(config)
courses, chunks = rag.add_course_folder("../docs", clear_existing=True)
print(f"Loaded {courses} courses, {chunks} chunks")
```

## AI System Prompt Behavior

The system prompt in `ai_generator.py` enforces:
- **One search maximum** per query
- **General knowledge questions** → No search, use Claude's knowledge
- **Course-specific questions** → Search first, then answer
- **No meta-commentary** → Direct answers only, no "based on the search results" phrases
- Response style: Brief, educational, clear, example-supported

## Frontend Architecture

- **Vanilla JavaScript** (no framework)
- **Markdown rendering** via `marked.js`
- **Session persistence** via `currentSessionId` variable
- **Security**: HTML escaping for user input, markdown parsing for assistant responses

## Performance Characteristics

Typical query latency: ~2.4 seconds
- First Claude API call: 1.2s (50%)
- Tool execution + vector search: 0.17s (7%)
- Second Claude API call: 0.75s (32%)
- Frontend processing: 0.2s (8%)

**Bottleneck:** Claude API calls (82% of total time)

## Testing & Debugging

**View API docs:**
```
http://localhost:8000/docs
```

**Check ChromaDB contents:**
```python
from vector_store import VectorStore

vs = VectorStore("./chroma_db", "all-MiniLM-L6-v2", 5)
print(vs.get_course_count())
print(vs.get_existing_course_titles())
```

**Monitor tool execution:**
Tool calls are logged via ToolManager. Check if Claude is using the search tool appropriately.

## Important Implementation Details

**Two-stage pattern is critical:**
- Never collapse into single API call
- First call determines IF search is needed
- Second call synthesizes the answer
- Tool results must be formatted as `{type: "tool_result", tool_use_id: ..., content: ...}`

**Session management:**
- Sessions auto-created if not provided
- Max 2 previous exchanges stored
- History passed to Claude for context continuity

**Vector search:**
- ChromaDB uses cosine similarity
- Embeddings generated on-the-fly for each query
- Results include metadata for source attribution

**Document chunking overlap:**
- 100-character overlap ensures context isn't lost at boundaries
- Sentence-based splitting preserves semantic coherence
- Each chunk includes course title and lesson number metadata

## Common Modifications

**Adjust chunk size/overlap:**
Edit `CHUNK_SIZE` and `CHUNK_OVERLAP` in `backend/config.py`, then rebuild:
```python
rag.add_course_folder("../docs", clear_existing=True)
```

**Change number of search results:**
Edit `MAX_RESULTS` in `backend/config.py`

**Modify AI behavior:**
Edit `SYSTEM_PROMPT` in `backend/ai_generator.py`

**Add new tools:**
1. Create tool class inheriting from base in `search_tools.py`
2. Register with `tool_manager.register_tool()`
3. Define `get_tool_definition()` and `execute()` methods

**Change conversation memory:**
Edit `MAX_HISTORY` in `backend/config.py`
- always use uv to run the server do not use pip directly
- make sure to use UV to manage all dependencies
- don't run the server using ./run.sh I will start it myself