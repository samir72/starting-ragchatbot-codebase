import anthropic
from typing import List, Optional, Dict, Any
import time

class AIGenerator:
    """Handles interactions with Anthropic's Claude API for generating responses"""

    # Maximum sequential tool calling rounds per query
    MAX_TOOL_ROUNDS = 2

    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to comprehensive tools for course information.

Tool Usage:
- **search_course_content**: Use for questions about specific course content or detailed educational materials
- **get_course_outline**: Use for questions about course structure, curriculum, lesson lists, or course overview
- **Multi-round search capability**: You can make UP TO 2 SEARCHES per query
  - Use multiple searches for complex queries requiring information from different sources
  - Example multi-search scenarios:
    * Comparing topics across different courses
    * Multi-part questions (e.g., "What is X and what is Y?")
    * Finding courses that discuss topics mentioned in other courses
  - First search: Explore one aspect or gather initial information
  - Second search (optional): Explore another aspect, refine results, or search different course/lesson
  - Use different search parameters (different course_name, lesson_number, or query terms)
- **Search efficiency**:
  - Do NOT repeat the same search twice
  - Do NOT search if first result already answers the question completely
  - After gathering all needed information, provide final synthesized answer
- Synthesize tool results into accurate, fact-based responses
- If tool yields no results, state this clearly without offering alternatives

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without using tools
- **Course-specific questions**: Use appropriate tool first, then answer
- **Course outline questions**: Use get_course_outline to provide course title, course link, and complete lesson list with lesson numbers and titles
- **No meta-commentary**:
 - Provide direct answers only — no reasoning process, tool usage explanations, or question-type analysis
 - Do not mention "based on the search results" or "based on the tool results"


All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Example-supported** - Include relevant examples when they aid understanding
Provide only the direct answer to what was asked.
"""
    
    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

        # Pre-build base API parameters
        self.base_params = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": 800,
            "timeout": 60.0  # 60 second timeout for API calls
        }

        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 1.0  # Initial retry delay in seconds
    
    def generate_response(self, query: str,
                         conversation_history: Optional[str] = None,
                         tools: Optional[List] = None,
                         tool_manager=None) -> str:
        """
        Generate AI response with optional tool usage and conversation context.
        
        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools
            
        Returns:
            Generated response as string
        """
        
        # Build system content efficiently - avoid string ops when possible
        system_content = (
            f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
            if conversation_history 
            else self.SYSTEM_PROMPT
        )
        
        # Prepare API call parameters efficiently
        api_params = {
            **self.base_params,
            "messages": [{"role": "user", "content": query}],
            "system": system_content
        }
        
        # Add tools if available
        if tools:
            api_params["tools"] = tools
            api_params["tool_choice"] = {"type": "auto"}

        # Get response from Claude with retry logic
        response = self._make_api_call_with_retry(api_params)

        # Handle tool execution if needed
        if response.stop_reason == "tool_use" and tool_manager:
            return self._execute_tool_loop(response, api_params, tool_manager)

        # Return direct response
        return response.content[0].text

    def _make_api_call_with_retry(self, api_params: Dict[str, Any]):
        """
        Make API call with exponential backoff retry logic.

        Args:
            api_params: Parameters for the API call

        Returns:
            API response

        Raises:
            Exception: If all retries fail
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                # Attempt API call
                response = self.client.messages.create(**api_params)
                return response

            except anthropic.RateLimitError as e:
                # Rate limit - retry with exponential backoff
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    print(f"Rate limit hit, retrying in {delay}s (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(delay)
                    continue
                else:
                    print(f"Rate limit exceeded after {self.max_retries} attempts")
                    raise

            except anthropic.APIConnectionError as e:
                # Connection error - retry with backoff
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    print(f"Connection error, retrying in {delay}s (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(delay)
                    continue
                else:
                    print(f"Connection failed after {self.max_retries} attempts")
                    raise

            except anthropic.APITimeoutError as e:
                # Timeout - retry with backoff
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    print(f"Timeout, retrying in {delay}s (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(delay)
                    continue
                else:
                    print(f"Timeout after {self.max_retries} attempts")
                    raise

            except (anthropic.AuthenticationError, anthropic.BadRequestError) as e:
                # Don't retry authentication or bad request errors
                print(f"Non-retryable error: {type(e).__name__}: {str(e)}")
                raise

            except Exception as e:
                # Unknown error - don't retry
                print(f"Unexpected error: {type(e).__name__}: {str(e)}")
                raise

        # If we get here, all retries failed
        if last_exception:
            raise last_exception
    
    def _execute_tool_loop(self, initial_response, base_params: Dict[str, Any], tool_manager):
        """
        Execute up to MAX_TOOL_ROUNDS of sequential tool calling.

        Supports multi-round tool execution where Claude can request additional
        tool calls after seeing previous results. The loop terminates when:
        - Claude responds with text (stop_reason == "end_turn")
        - Maximum rounds reached (MAX_TOOL_ROUNDS)
        - Tool execution error occurs

        Args:
            initial_response: The initial response containing tool use requests
            base_params: Base API parameters with system, messages, etc.
            tool_manager: Manager to execute tools

        Returns:
            Final response text after all tool rounds
        """
        # Start with existing messages
        messages = base_params["messages"].copy()
        current_response = initial_response
        tool_use_round = 0

        # Loop for up to MAX_TOOL_ROUNDS
        while tool_use_round < self.MAX_TOOL_ROUNDS:
            # Check if Claude wants to use tools
            if current_response.stop_reason != "tool_use":
                # Claude responded with text, we're done
                return current_response.content[0].text

            # Add AI's response (including tool use blocks)
            messages.append({"role": "assistant", "content": current_response.content})

            # Execute all tool calls and collect results
            tool_results = []
            for content_block in current_response.content:
                if content_block.type == "tool_use":
                    try:
                        tool_result = tool_manager.execute_tool(
                            content_block.name,
                            **content_block.input
                        )
                    except Exception as e:
                        # Return error as tool result, let Claude handle it gracefully
                        tool_result = f"Error executing tool: {str(e)}"

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": tool_result
                    })

            # Add tool results as user message
            if tool_results:
                messages.append({"role": "user", "content": tool_results})

            tool_use_round += 1

            # Prepare next API call with tools still available
            next_params = {
                **self.base_params,
                "messages": messages,
                "system": base_params["system"],
                "tools": base_params["tools"],
                "tool_choice": {"type": "auto"}
            }

            # Make next API call
            current_response = self._make_api_call_with_retry(next_params)

        # Max rounds reached - check if we need final synthesis
        if current_response.stop_reason == "tool_use":
            # Claude still wants tools but we've hit the limit
            # Force a final response without tools
            messages.append({"role": "assistant", "content": current_response.content})

            # Execute remaining tool calls
            tool_results = []
            for content_block in current_response.content:
                if content_block.type == "tool_use":
                    try:
                        tool_result = tool_manager.execute_tool(
                            content_block.name,
                            **content_block.input
                        )
                    except Exception as e:
                        tool_result = f"Error executing tool: {str(e)}"

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": tool_result
                    })

            if tool_results:
                messages.append({"role": "user", "content": tool_results})

            # Final call WITHOUT tools to force text response
            final_params = {
                **self.base_params,
                "messages": messages,
                "system": base_params["system"]
            }

            current_response = self._make_api_call_with_retry(final_params)

        # Extract and return final text response
        return current_response.content[0].text