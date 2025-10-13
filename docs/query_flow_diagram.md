# Complete Query Flow Diagram: RAG Chatbot System

This document provides a comprehensive visual representation of how a user query flows through the RAG chatbot system, from frontend input to displayed response.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│                      (frontend/index.html)                      │
│                                                                 │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐  │
│  │   Sidebar    │     │  Chat Area   │     │ Input Field  │  │
│  │  (courses)   │     │  (messages)  │     │  + Button    │  │
│  └──────────────┘     └──────────────┘     └──────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↕ HTTP POST
┌─────────────────────────────────────────────────────────────────┐
│                        BACKEND API                              │
│                      (backend/app.py)                           │
│                                                                 │
│  POST /api/query → QueryRequest → QueryResponse                │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                      RAG ORCHESTRATOR                           │
│                   (backend/rag_system.py)                       │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   Session    │  │      AI      │  │     Tool     │        │
│  │   Manager    │  │  Generator   │  │   Manager    │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                            │
│                                                                 │
│  ┌────────────────────┐         ┌────────────────────┐        │
│  │  Anthropic API     │         │    ChromaDB        │        │
│  │  (Claude Sonnet 4) │         │  (Vector Store)    │        │
│  └────────────────────┘         └────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

## Detailed Step-by-Step Flow

### Example Query: "What is RAG?"

```
TIME    LAYER           COMPONENT              ACTION
────────────────────────────────────────────────────────────────────

0ms     Frontend        User Input             User types "What is RAG?"
                                               and clicks Send button

10ms    Frontend        script.js              ┌──────────────────────┐
                        sendMessage()          │ Query validation     │
                                               │ Disable input        │
                                               │ Add user message     │
                                               │ Show loading spinner │
                                               └──────────────────────┘

30ms    Frontend        Fetch API              POST /api/query
                                               ┌────────────────────────┐
                                               │ {                      │
                                               │   "query": "What...",  │
                                               │   "session_id": "abc"  │
                                               │ }                      │
                                               └────────────────────────┘

50ms    Backend         app.py                 Receive request at
                        @app.post("/api/query") /api/query endpoint

60ms    Backend         RAGSystem              ┌──────────────────────┐
                        query()                │ session_id check     │
                                               │ Get history (2 prev) │
                                               │ Prepare prompt       │
                                               └──────────────────────┘

80ms    Backend         AIGenerator            First Claude API call
                        generate_response()    ┌──────────────────────────────┐
                                               │ System prompt loaded        │
                                               │ Conversation history added  │
                                               │ Tool definitions included   │
                                               │ Model: claude-sonnet-4      │
                                               └──────────────────────────────┘

100ms   External        Anthropic API          Request sent to Claude
                                               ┌─────────────────────────────┐
                                               │ system: [instructions...]   │
                                               │ messages: [                 │
                                               │   {role: "user",            │
                                               │    content: "Answer...RAG"} │
                                               │ ]                           │
                                               │ tools: [search_course...]   │
                                               │ max_tokens: 4096            │
                                               └─────────────────────────────┘

1200ms  External        Claude Processing      AI analyzes query
                                               ┌──────────────────────────┐
                                               │ Determines: Need to      │
                                               │ search course content    │
                                               │ Decision: Use tool       │
                                               └──────────────────────────┘

1300ms  External        Claude Response        Returns tool_use request
                                               ┌──────────────────────────────┐
                                               │ stop_reason: "tool_use"      │
                                               │ content: [                   │
                                               │   {                          │
                                               │     type: "tool_use",        │
                                               │     name: "search_course...", │
                                               │     input: {                 │
                                               │       query: "RAG retrieval" │
                                               │     }                        │
                                               │   }                          │
                                               │ ]                            │
                                               └──────────────────────────────┘

1320ms  Backend         AIGenerator            Detect tool_use in response
                        _handle_tool_execution()

1330ms  Backend         ToolManager            Execute tool
                        execute_tool()         ┌──────────────────────────┐
                                               │ Tool: search_course_...  │
                                               │ Query: "RAG retrieval"   │
                                               └──────────────────────────┘

1340ms  Backend         CourseSearchTool       Process search request
                        execute()              ┌──────────────────────────┐
                                               │ Parse parameters         │
                                               │ Call vector_store.search │
                                               └──────────────────────────┘

1360ms  Backend         VectorStore            Semantic search
                        search()               ┌──────────────────────────────┐
                                               │ Embedding model loads        │
                                               │ Query → 384-dim vector       │
                                               │ ChromaDB query prepared      │
                                               └──────────────────────────────┘

1380ms  External        ChromaDB               Vector similarity search
                        collection.query()     ┌──────────────────────────────┐
                                               │ Compare query embedding      │
                                               │ with stored embeddings       │
                                               │ Cosine similarity calc       │
                                               │ Return top 5 matches         │
                                               └──────────────────────────────┘

1450ms  Backend         VectorStore            Format search results
                                               ┌──────────────────────────────┐
                                               │ SearchResults object:        │
                                               │ - documents: [5 chunks]      │
                                               │ - metadata: [course, lesson] │
                                               │ - distances: [similarities]  │
                                               └──────────────────────────────┘

1470ms  Backend         CourseSearchTool       Format for Claude
                        _format_results()      ┌──────────────────────────────┐
                                               │ [Course1 - Lesson 2]         │
                                               │ RAG stands for...            │
                                               │                              │
                                               │ [Course1 - Lesson 3]         │
                                               │ Retrieval process...         │
                                               │                              │
                                               │ [Course2 - Lesson 1]         │
                                               │ Vector databases...          │
                                               └──────────────────────────────┘

1490ms  Backend         AIGenerator            Second Claude API call
                        _handle_tool_execution() ┌────────────────────────────┐
                                               │ Add assistant message      │
                                               │ Add tool_result message    │
                                               │ Request final synthesis    │
                                               └────────────────────────────┘

1510ms  External        Anthropic API          Second request
                                               ┌─────────────────────────────┐
                                               │ messages: [                 │
                                               │   {role: "user", ...},      │
                                               │   {role: "assistant",       │
                                               │    content: [tool_use]},    │
                                               │   {role: "user",            │
                                               │    content: [tool_result]}  │
                                               │ ]                           │
                                               └─────────────────────────────┘

2200ms  External        Claude Processing      Synthesize answer
                                               ┌──────────────────────────┐
                                               │ Read tool results        │
                                               │ Analyze context          │
                                               │ Generate concise answer  │
                                               │ Include examples         │
                                               └──────────────────────────┘

2250ms  External        Claude Response        Final answer
                                               ┌──────────────────────────────┐
                                               │ stop_reason: "end_turn"      │
                                               │ content: [                   │
                                               │   {                          │
                                               │     type: "text",            │
                                               │     text: "RAG (Retrieval... │
                                               │   }                          │
                                               │ ]                            │
                                               └──────────────────────────────┘

2270ms  Backend         AIGenerator            Extract text response
                                               Return: "RAG (Retrieval..."

2280ms  Backend         RAGSystem              ┌──────────────────────────┐
                                               │ Get sources from tool    │
                                               │ Save to session history  │
                                               │ Prepare response         │
                                               └──────────────────────────┘

2300ms  Backend         app.py                 Create QueryResponse
                                               ┌────────────────────────────┐
                                               │ {                          │
                                               │   "answer": "RAG...",      │
                                               │   "sources": [             │
                                               │     "Course1 - Lesson 2",  │
                                               │     "Course1 - Lesson 3"   │
                                               │   ],                       │
                                               │   "session_id": "abc"      │
                                               │ }                          │
                                               └────────────────────────────┘

2320ms  Frontend        Fetch API              Response received

2330ms  Frontend        script.js              ┌──────────────────────────┐
                        sendMessage()          │ Parse JSON response      │
                                               │ Update session_id        │
                                               │ Remove loading spinner   │
                                               │ Call addMessage()        │
                                               └──────────────────────────┘

2350ms  Frontend        script.js              Process assistant message
                        addMessage()           ┌──────────────────────────┐
                                               │ Create message element   │
                                               │ Render markdown          │
                                               │ Add sources collapsible  │
                                               │ Append to chatMessages   │
                                               └──────────────────────────┘

2360ms  Frontend        marked.js              Convert markdown to HTML
                                               ┌──────────────────────────┐
                                               │ **RAG** → <strong>       │
                                               │ Lists → <ul><li>         │
                                               │ Code → <code>            │
                                               └──────────────────────────┘

2370ms  Frontend        DOM Update             ┌──────────────────────────┐
                                               │ Message appears          │
                                               │ Scroll to bottom         │
                                               │ Re-enable input          │
                                               │ Focus input field        │
                                               └──────────────────────────┘

DONE    Frontend        User Interface         User sees complete answer
                                               with source attribution
```

## Component Interaction Map

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   USER QUERY: "What is RAG?"                                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  FRONTEND (script.js)                                                   │
│                                                                         │
│  • sendMessage() captures query                                         │
│  • Disables input, shows loading                                        │
│  • Makes POST request to /api/query                                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  BACKEND API (app.py)                                                   │
│                                                                         │
│  • @app.post("/api/query") receives QueryRequest                        │
│  • Extracts query and session_id                                        │
│  • Calls rag_system.query(query, session_id)                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  RAG SYSTEM (rag_system.py)                                             │
│                                                                         │
│  • Retrieves conversation history from SessionManager                   │
│  • Builds prompt: "Answer this question about course materials: ..."    │
│  • Calls ai_generator.generate_response() with:                         │
│    - Query                                                              │
│    - Conversation history                                               │
│    - Tool definitions                                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  AI GENERATOR (ai_generator.py) - FIRST CALL                            │
│                                                                         │
│  • Prepares messages with system prompt                                 │
│  • Includes SYSTEM_PROMPT with tool usage instructions                  │
│  • Calls anthropic.messages.create() with:                              │
│    - model: "claude-sonnet-4-20250514"                                  │
│    - max_tokens: 4096                                                   │
│    - tools: [search_course_content]                                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  ANTHROPIC API (Claude Sonnet 4)                                        │
│                                                                         │
│  • Analyzes query: "What is RAG?"                                       │
│  • Determines it's a course-specific question                           │
│  • Decides to use search_course_content tool                            │
│  • Returns: stop_reason="tool_use" with tool request                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  AI GENERATOR (ai_generator.py)                                         │
│                                                                         │
│  • Detects tool_use in response                                         │
│  • Calls _handle_tool_execution()                                       │
│  • Extracts tool name and parameters                                    │
│  • Calls tool_manager.execute_tool()                                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  TOOL MANAGER & COURSE SEARCH TOOL (search_tools.py)                    │
│                                                                         │
│  • Receives: {query: "RAG retrieval", course_name: null, ...}           │
│  • Calls vector_store.search(query)                                     │
│  • Waits for search results                                             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  VECTOR STORE (vector_store.py)                                         │
│                                                                         │
│  • Loads embedding model: all-MiniLM-L6-v2                              │
│  • Converts "RAG retrieval" → 384-dim vector                            │
│  • Queries ChromaDB course_content collection                           │
│  • Requests top 5 results                                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  CHROMADB (External Service)                                            │
│                                                                         │
│  • Performs cosine similarity search                                    │
│  • Compares query embedding with all stored embeddings                  │
│  • Returns top 5 most similar chunks with:                              │
│    - Document text                                                      │
│    - Metadata (course_title, lesson_number)                             │
│    - Similarity scores                                                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  VECTOR STORE (vector_store.py)                                         │
│                                                                         │
│  • Wraps results in SearchResults object                                │
│  • Returns to CourseSearchTool                                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  COURSE SEARCH TOOL (search_tools.py)                                   │
│                                                                         │
│  • Formats results with headers:                                        │
│    "[Course Title - Lesson N]"                                          │
│  • Stores sources for later attribution                                 │
│  • Returns formatted string to AIGenerator                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  AI GENERATOR (ai_generator.py) - SECOND CALL                           │
│                                                                         │
│  • Appends tool_result to conversation                                  │
│  • Calls anthropic.messages.create() again with:                        │
│    - Original user message                                              │
│    - Assistant's tool_use message                                       │
│    - User's tool_result message (with search results)                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  ANTHROPIC API (Claude Sonnet 4)                                        │
│                                                                         │
│  • Receives tool results with course content                            │
│  • Synthesizes concise answer based on retrieved context                │
│  • Generates educational, example-supported response                    │
│  • Returns: stop_reason="end_turn" with final text                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  AI GENERATOR (ai_generator.py)                                         │
│                                                                         │
│  • Extracts text from content[0].text                                   │
│  • Returns final answer to RAGSystem                                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  RAG SYSTEM (rag_system.py)                                             │
│                                                                         │
│  • Gets sources from tool_manager.get_last_sources()                    │
│  • Saves conversation exchange to SessionManager                        │
│  • Returns (answer, sources) tuple to API                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  BACKEND API (app.py)                                                   │
│                                                                         │
│  • Creates QueryResponse object:                                        │
│    {                                                                    │
│      answer: "RAG stands for...",                                       │
│      sources: ["Course1 - Lesson 2", ...],                              │
│      session_id: "abc123"                                               │
│    }                                                                    │
│  • Returns JSON response                                                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  FRONTEND (script.js)                                                   │
│                                                                         │
│  • Receives response from fetch()                                       │
│  • Updates currentSessionId                                             │
│  • Removes loading spinner                                              │
│  • Calls addMessage(data.answer, 'assistant', data.sources)             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  FRONTEND (script.js - addMessage)                                      │
│                                                                         │
│  • Creates message div with class "message assistant"                   │
│  • Uses marked.parse() to convert markdown to HTML                      │
│  • Creates collapsible <details> for sources                            │
│  • Appends to chatMessages container                                    │
│  • Scrolls to bottom                                                    │
│  • Re-enables input field                                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   USER SEES ANSWER with source attribution                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Transformation Flow

```
┌──────────────────────┐
│  User Input String   │
│  "What is RAG?"      │
└──────────────────────┘
         ↓
┌──────────────────────────────────┐
│  QueryRequest (Pydantic)         │
│  {                               │
│    query: "What is RAG?",        │
│    session_id: "abc-123-def"     │
│  }                               │
└──────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────┐
│  Claude API Request (Dict)                   │
│  {                                           │
│    model: "claude-sonnet-4-20250514",        │
│    system: [SYSTEM_PROMPT],                  │
│    messages: [                               │
│      {                                       │
│        role: "user",                         │
│        content: "Answer this question..."    │
│      }                                       │
│    ],                                        │
│    tools: [                                  │
│      {                                       │
│        name: "search_course_content",        │
│        description: "Search course...",      │
│        input_schema: {...}                   │
│      }                                       │
│    ],                                        │
│    max_tokens: 4096                          │
│  }                                           │
└──────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────┐
│  Claude Response #1 (Message object)         │
│  {                                           │
│    id: "msg_...",                            │
│    role: "assistant",                        │
│    content: [                                │
│      {                                       │
│        type: "tool_use",                     │
│        id: "toolu_...",                      │
│        name: "search_course_content",        │
│        input: {                              │
│          query: "RAG retrieval augmented"    │
│        }                                     │
│      }                                       │
│    ],                                        │
│    stop_reason: "tool_use"                   │
│  }                                           │
└──────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────┐
│  Tool Execution Parameters       │
│  {                               │
│    query: "RAG retrieval",       │
│    course_name: null,            │
│    lesson_number: null           │
│  }                               │
└──────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────┐
│  Embedding Vector (numpy array)              │
│  [0.123, -0.456, 0.789, ..., 0.321]         │
│  Shape: (384,)                               │
└──────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────┐
│  ChromaDB Query Results                      │
│  {                                           │
│    ids: [["chunk_1_2_0", "chunk_1_3_1", ...]], │
│    documents: [[                             │
│      "RAG stands for Retrieval-Augmented...", │
│      "The retrieval component uses...",      │
│      ...                                     │
│    ]],                                       │
│    metadatas: [[                             │
│      {course_title: "Course1",               │
│       lesson_number: 2, chunk_index: 0},     │
│      {course_title: "Course1",               │
│       lesson_number: 3, chunk_index: 1},     │
│      ...                                     │
│    ]],                                       │
│    distances: [[0.234, 0.267, 0.301, ...]]  │
│  }                                           │
└──────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────┐
│  SearchResults (Pydantic)                    │
│  SearchResults(                              │
│    documents=[                               │
│      "RAG stands for...",                    │
│      "The retrieval component...",           │
│      ...                                     │
│    ],                                        │
│    metadata=[                                │
│      {course_title: "Course1", lesson: 2},   │
│      {course_title: "Course1", lesson: 3},   │
│      ...                                     │
│    ],                                        │
│    distances=[0.234, 0.267, ...]            │
│  )                                           │
└──────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────┐
│  Formatted Tool Result (String)              │
│                                              │
│  [Course1 - Lesson 2]                        │
│  RAG stands for Retrieval-Augmented          │
│  Generation. It's a technique that...        │
│                                              │
│  [Course1 - Lesson 3]                        │
│  The retrieval component uses vector         │
│  databases to find relevant context...       │
│                                              │
│  [Course2 - Lesson 1]                        │
│  Vector databases store embeddings...        │
└──────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────┐
│  Claude API Request #2 (Dict)                │
│  {                                           │
│    model: "claude-sonnet-4-20250514",        │
│    system: [SYSTEM_PROMPT],                  │
│    messages: [                               │
│      {role: "user", content: "Answer..."},   │
│      {role: "assistant",                     │
│       content: [tool_use]},                  │
│      {role: "user",                          │
│       content: [                             │
│         {type: "tool_result",                │
│          tool_use_id: "toolu_...",           │
│          content: "[Course1 - Lesson 2]..."}  │
│       ]}                                     │
│    ],                                        │
│    max_tokens: 4096                          │
│  }                                           │
└──────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────┐
│  Claude Response #2 (Message object)         │
│  {                                           │
│    id: "msg_...",                            │
│    role: "assistant",                        │
│    content: [                                │
│      {                                       │
│        type: "text",                         │
│        text: "**RAG (Retrieval-Augmented    │
│               Generation)** is a technique   │
│               that combines:\n\n             │
│               1. **Retrieval**: Finding...   │
│               2. **Generation**: Using...    │
│               \n\nExample: When you ask..." │
│      }                                       │
│    ],                                        │
│    stop_reason: "end_turn"                   │
│  }                                           │
└──────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────┐
│  QueryResponse (Pydantic)                    │
│  {                                           │
│    answer: "**RAG (Retrieval-Augmented...", │
│    sources: [                                │
│      "Course1 - Lesson 2",                   │
│      "Course1 - Lesson 3",                   │
│      "Course2 - Lesson 1"                    │
│    ],                                        │
│    session_id: "abc-123-def"                 │
│  }                                           │
└──────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────┐
│  JSON Response (String)                      │
│  {                                           │
│    "answer": "**RAG (Retrieval-Augmented...", │
│    "sources": ["Course1 - Lesson 2", ...],   │
│    "session_id": "abc-123-def"               │
│  }                                           │
└──────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────┐
│  Parsed JavaScript Object                    │
│  {                                           │
│    answer: "**RAG (Retrieval-Augmented...", │
│    sources: ["Course1 - Lesson 2", ...],     │
│    session_id: "abc-123-def"                 │
│  }                                           │
└──────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────┐
│  HTML (via marked.js)                        │
│  <p>                                         │
│    <strong>RAG (Retrieval-Augmented          │
│    Generation)</strong> is a technique       │
│    that combines:                            │
│  </p>                                        │
│  <ol>                                        │
│    <li><strong>Retrieval</strong>:           │
│        Finding...</li>                       │
│    <li><strong>Generation</strong>:          │
│        Using...</li>                         │
│  </ol>                                       │
│  <p>Example: When you ask...</p>             │
│                                              │
│  <details>                                   │
│    <summary>Sources (3)</summary>            │
│    <ul>                                      │
│      <li>Course1 - Lesson 2</li>             │
│      <li>Course1 - Lesson 3</li>             │
│      <li>Course2 - Lesson 1</li>             │
│    </ul>                                     │
│  </details>                                  │
└──────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────┐
│  DOM (Rendered in Browser)                   │
│                                              │
│  ┌────────────────────────────────────────┐ │
│  │ [AI Icon]                              │ │
│  │                                        │ │
│  │ RAG (Retrieval-Augmented Generation)  │ │
│  │ is a technique that combines:          │ │
│  │                                        │ │
│  │ 1. Retrieval: Finding...               │ │
│  │ 2. Generation: Using...                │ │
│  │                                        │ │
│  │ Example: When you ask...               │ │
│  │                                        │ │
│  │ ▶ Sources (3)                          │ │
│  └────────────────────────────────────────┘ │
└──────────────────────────────────────────────┘
```

## Key Decision Points

### 1. When Claude Decides to Use Tools

```
Decision Tree in Claude's reasoning:

Is this a GENERAL KNOWLEDGE question?
├─ YES → Answer directly without tools
└─ NO → Is it about COURSE CONTENT?
    ├─ YES → Use search_course_content tool
    └─ NO → Answer based on available context
```

**Examples:**
- "What is Python?" → General knowledge, no tool
- "What does the course say about RAG?" → Course content, use tool
- "How many courses are there?" → Metadata, no tool needed

### 2. When Vector Store Applies Filters

```
Query Parameters:
├─ course_name provided?
│  ├─ YES → Filter by course_title
│  └─ NO → Search across all courses
└─ lesson_number provided?
   ├─ YES → Filter by lesson_number
   └─ NO → Search across all lessons
```

**Examples:**
- `search(query="RAG")` → All courses, all lessons
- `search(query="RAG", course_name="Anthropic")` → One course, all lessons
- `search(query="RAG", lesson_number=2)` → All courses, lesson 2 only

### 3. When Session History is Used

```
Session Tracking:
├─ First query in conversation?
│  ├─ YES → Create new session_id, no history
│  └─ NO → Use existing session_id
└─ Has conversation history?
    ├─ YES → Include last 2 exchanges in context
    └─ NO → Proceed without history
```

**Impact:**
- Follow-up questions benefit from context
- "Tell me more" uses previous answer's context
- Max 2 previous exchanges prevents context bloat

## Performance Characteristics

| Phase | Duration | Percentage |
|-------|----------|------------|
| Frontend processing | 50ms | 2.1% |
| First Claude API call | 1200ms | 50.6% |
| Tool execution & vector search | 170ms | 7.2% |
| Second Claude API call | 750ms | 31.6% |
| Response formatting & frontend | 200ms | 8.4% |
| **TOTAL** | **~2370ms** | **100%** |

**Bottlenecks:**
1. Claude API calls (82% of total time)
2. Vector embedding generation (60-70ms)
3. ChromaDB similarity search (70-90ms)

**Optimization opportunities:**
- Cache embeddings for common queries
- Implement streaming responses
- Parallelize independent operations
- Use lighter embedding model for faster results

## Error Handling Flow

```
┌─────────────────────────────────────────────┐
│ Frontend Error Handling                     │
│                                             │
│ try {                                       │
│   const response = await fetch('/api/query') │
│ } catch (error) {                           │
│   addMessage(                               │
│     "Network error. Check connection.",     │
│     'error'                                 │
│   )                                         │
│ }                                           │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Backend Error Handling                      │
│                                             │
│ • FastAPI validation errors → 422 response │
│ • Anthropic API errors → Logged & re-raised│
│ • ChromaDB errors → Logged & handled       │
│ • Tool execution errors → Returned to Claude│
└─────────────────────────────────────────────┘
```

## Summary

This RAG chatbot system implements a sophisticated multi-stage architecture:

1. **User Input** → Frontend captures and validates
2. **API Request** → FastAPI receives and routes
3. **RAG Orchestration** → Coordinates all components
4. **First AI Call** → Claude decides whether to search
5. **Tool Execution** → Searches vector database if needed
6. **Second AI Call** → Claude synthesizes final answer
7. **Response Return** → API formats and sends back
8. **Frontend Display** → Renders markdown with sources

**Total roundtrip time: ~2.4 seconds**

The system's power comes from:
- **Semantic search** finding relevant content
- **Tool-based architecture** giving Claude access to data
- **Two-stage generation** ensuring accurate, grounded responses
- **Session management** maintaining conversation context
- **Clean separation** of concerns across components

