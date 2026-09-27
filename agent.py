# agent.py

from groq import Groq
import json
from tools import TOOLS, execute_tool
from state import AgentState

class DataAgent:
    def __init__(self):
        self.client = Groq()  # Auto-reads GROQ_API_KEY from .env
        self.state = AgentState()
        self.model = "openai/gpt-oss-20b"  # Free tier model on Groq
    
    def get_system_prompt(self):
        """System prompt tells LLM how to behave"""
        return """You are a data analysis agent. Your job is to answer user questions by:

1. THINKING: Decide what information you need
2. ACTING: Call tools to get that information
3. OBSERVING: Look at the results
4. REASONING: Adjust your approach based on observations

IMPORTANT GUIDELINES:
- Start by calling get_schema() to understand the database
- Use query_database() for SQL queries
- Ask clarifying questions if the query is ambiguous
- If a query fails, read the error and try a different approach
- Show your reasoning to the user

Current agent state:
""" + self.state.get_context_summary()
    
    def run(self, user_query):
        """Main agent loop (ReAct pattern)"""
        # Keep attempts and logs scoped to this question.
        self.state = AgentState()
        
        print(f"\n{'='*60}")
        print(f"USER QUERY: {user_query}")
        print(f"{'='*60}\n")
        
        # Initial message
        self.state.add_message("user", user_query)
        
        # Start with system prompt + user query
        messages = [
            {
                "role": "system",
                "content": self.get_system_prompt()
            },
            {
                "role": "user",
                "content": user_query
            }
        ]
        
        # Loop: Keep going until agent says it's done or max attempts reached
        while self.state.should_continue():
            # Step 1: LLM thinks and decides what to do
            print(f"[Attempt {self.state.attempts + 1}] Calling LLM...")
            
            try:
                # Use Groq's chat.completions API
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=1024,
                    messages=messages,
                    tools=TOOLS
                )
            except Exception as e:
                print(f"ERROR calling Groq API: {e}")
                return None
            
            # Get the response
            choice = response.choices[0]
            
            # Check if LLM is done (no more tool calls)
            if choice.finish_reason == "stop":
                final_response = choice.message.content or "Done"
                print(f"\n[FINAL ANSWER]\n{final_response}")
                self.state.print_log()
                return final_response
            
            # Step 2: Parse what LLM wants to do
            text_response = choice.message.content or ""
            
            if text_response:
                print(f"\n[LLM Thinking]\n{text_response}")
            
            # Get tool calls if they exist
            tool_calls = choice.message.tool_calls or []
            
            # Step 3: If no tool calls, we're done
            if not tool_calls:
                print("\nNo tools called, finishing")
                self.state.print_log()
                return text_response
            
            # Add LLM response to conversation
            messages.append({
                "role": "assistant",
                "content": text_response,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in tool_calls
                ]
            })
            
            # Execute each tool and collect results
            tool_results = []
            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                
                # Parse the arguments (they come as JSON string)
                try:
                    tool_input = json.loads(tool_call.function.arguments)
                except:
                    tool_input = {}
                
                print(f"\n[Tool Call] {tool_name}")
                print(f"Input: {json.dumps(tool_input, indent=2)}")
                
                try:
                    # Execute the tool
                    result = execute_tool(tool_name, tool_input)
                    result_str = str(result)
                    print(f"Result:\n{result_str[:500]}...")  # Print first 500 chars
                    
                    # Tool functions may return errors as text instead of raising.
                    success = not result_str.startswith("ERROR:")
                    self.state.log_attempt(
                        tool_name,
                        success=success,
                        error_msg=None if success else result_str,
                    )
                    
                    tool_results.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": tool_name,
                        "content": result_str
                    })
                
                except Exception as e:
                    # Handle errors
                    error_msg = f"Tool failed: {str(e)}"
                    print(f"ERROR: {error_msg}")
                    
                    self.state.log_attempt(tool_name, success=False, error_msg=error_msg)
                    
                    tool_results.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": tool_name,
                        "content": error_msg
                    })
            
            # Step 4: Feed results back to LLM
            for result in tool_results:
                messages.append({
                    "role": "tool",
                    "tool_call_id": result["tool_call_id"],
                    "name": result["name"],
                    "content": result["content"]
                })
            
            self.state.add_message("assistant", text_response)
        
        print("\nMax attempts reached")
        self.state.print_log()
        return None
